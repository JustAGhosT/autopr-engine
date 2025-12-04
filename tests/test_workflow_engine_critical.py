"""
Tests for Workflow Engine - Critical Components

Tests for race condition fixes, input validation, and core functionality.
"""

import asyncio
from datetime import datetime
import pytest
import pytest_asyncio

from autopr.config import AutoPRConfig
from autopr.exceptions import WorkflowError
from autopr.workflows.engine import WorkflowEngine
from autopr.workflows.base import Workflow


class MockWorkflow(Workflow):
    """Mock workflow for testing."""
    
    def __init__(self, name: str, delay: float = 0.1):
        self.name = name
        self.delay = delay
        self.execute_count = 0
    
    async def execute(self, context: dict) -> dict:
        """Execute mock workflow."""
        self.execute_count += 1
        await asyncio.sleep(self.delay)
        return {"status": "success", "count": self.execute_count}
    
    async def validate_inputs(self, context: dict) -> None:
        """Validate inputs."""
        pass
    
    async def validate_outputs(self, result: dict) -> None:
        """Validate outputs."""
        pass


@pytest.fixture
def config():
    """Create test configuration."""
    return AutoPRConfig()


@pytest_asyncio.fixture
async def workflow_engine(config):
    """Create and start workflow engine."""
    engine = WorkflowEngine(config)
    await engine.start()
    yield engine
    await engine.stop()


@pytest.mark.asyncio
async def test_metrics_race_condition_fixed(workflow_engine):
    """
    Test that metrics updates are thread-safe.
    
    This tests the fix for BUG-2: Race condition in workflow metrics.
    Previously, get_metrics() and get_status() could read metrics without
    the lock, causing race conditions. Now they properly use async locks.
    """
    # Register a fast workflow
    workflow = MockWorkflow("test-workflow", delay=0.01)
    workflow_engine.register_workflow(workflow)
    
    # Run multiple workflows concurrently
    num_workflows = 10
    tasks = []
    
    for i in range(num_workflows):
        task = asyncio.create_task(
            workflow_engine.execute_workflow(
                "test-workflow",
                {"workflow_name": "test-workflow", "index": i}
            )
        )
        tasks.append(task)
    
    # Concurrently read metrics while workflows are running
    metric_tasks = []
    for _ in range(20):
        metric_tasks.append(asyncio.create_task(workflow_engine.get_metrics()))
        metric_tasks.append(asyncio.create_task(workflow_engine.get_status()))
        await asyncio.sleep(0.001)  # Small delay
    
    # Wait for all to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)
    metric_results = await asyncio.gather(*metric_tasks, return_exceptions=True)
    
    # Verify no exceptions from concurrent access
    for result in metric_results:
        assert not isinstance(result, Exception), f"Metrics access raised exception: {result}"
    
    # Verify metrics are consistent
    final_metrics = await workflow_engine.get_metrics()
    assert final_metrics["total_executions"] == num_workflows
    assert final_metrics["successful_executions"] == num_workflows
    assert final_metrics["failed_executions"] == 0
    
    # Verify success rate calculation
    assert final_metrics["success_rate_percent"] == 100.0


@pytest.mark.asyncio
async def test_input_validation_prevents_injection(workflow_engine):
    """
    Test that input validation prevents injection attacks.
    
    This tests the fix for BUG-3: Missing input validation on workflow execution.
    """
    workflow = MockWorkflow("safe-workflow")
    workflow_engine.register_workflow(workflow)
    
    # Test 1: Invalid workflow name with special characters
    with pytest.raises(WorkflowError) as exc_info:
        await workflow_engine.execute_workflow(
            "safe-workflow",
            {"workflow_name": "test'; DROP TABLE workflows;--"}
        )
    assert "validation failed" in str(exc_info.value).lower()
    
    # Test 2: Excessively long execution ID
    with pytest.raises(WorkflowError) as exc_info:
        await workflow_engine.execute_workflow(
            "safe-workflow",
            {
                "workflow_name": "safe-workflow",
                "execution_id": "x" * 1000  # Too long
            }
        )
    assert "validation failed" in str(exc_info.value).lower()
    
    # Test 3: Suspicious patterns in parameters
    with pytest.raises(WorkflowError) as exc_info:
        await workflow_engine.execute_workflow(
            "safe-workflow",
            {
                "workflow_name": "safe-workflow",
                "data": "<script>alert('xss')</script>"
            }
        )
    assert "suspicious pattern" in str(exc_info.value).lower()
    
    # Test 4: Valid input should work
    result = await workflow_engine.execute_workflow(
        "safe-workflow",
        {"workflow_name": "safe-workflow", "data": "valid data"}
    )
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_workflow_history_limit(workflow_engine):
    """
    Test that workflow history is properly limited.
    
    This verifies the fix for BUG-8: Potential memory leak in workflow history.
    """
    from autopr.workflows.engine import MAX_WORKFLOW_HISTORY
    
    workflow = MockWorkflow("history-test", delay=0.001)
    workflow_engine.register_workflow(workflow)
    
    # Execute more workflows than the history limit
    num_executions = MAX_WORKFLOW_HISTORY + 100
    
    for i in range(num_executions):
        try:
            await workflow_engine.execute_workflow(
                "history-test",
                {"workflow_name": "history-test", "index": i}
            )
        except Exception:
            pass  # Continue even if some fail
    
    # Verify history is limited
    history = workflow_engine.get_workflow_history(limit=num_executions)
    assert len(history) <= MAX_WORKFLOW_HISTORY
    assert len(workflow_engine.workflow_history) <= MAX_WORKFLOW_HISTORY


@pytest.mark.asyncio
async def test_concurrent_workflow_execution(workflow_engine):
    """Test that multiple workflows can run concurrently without issues."""
    # Register multiple workflows
    for i in range(5):
        workflow = MockWorkflow(f"concurrent-{i}", delay=0.05)
        workflow_engine.register_workflow(workflow)
    
    # Execute all concurrently
    tasks = []
    for i in range(5):
        task = asyncio.create_task(
            workflow_engine.execute_workflow(
                f"concurrent-{i}",
                {"workflow_name": f"concurrent-{i}"}
            )
        )
        tasks.append(task)
    
    # Wait for all to complete
    results = await asyncio.gather(*tasks)
    
    # Verify all succeeded
    assert all(r["status"] == "success" for r in results)
    
    # Verify metrics
    metrics = await workflow_engine.get_metrics()
    assert metrics["total_executions"] == 5
    assert metrics["successful_executions"] == 5


@pytest.mark.asyncio
async def test_workflow_not_found_error(workflow_engine):
    """Test that attempting to execute non-existent workflow raises error."""
    with pytest.raises(WorkflowError) as exc_info:
        await workflow_engine.execute_workflow(
            "nonexistent-workflow",
            {"workflow_name": "nonexistent"}
        )
    assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_workflow_engine_start_stop(config):
    """Test that workflow engine can be started and stopped properly."""
    engine = WorkflowEngine(config)
    
    # Initially not running
    status = await engine.get_status()
    assert not status["running"]
    
    # Start engine
    await engine.start()
    status = await engine.get_status()
    assert status["running"]
    
    # Stop engine
    await engine.stop()
    status = await engine.get_status()
    assert not status["running"]


@pytest.mark.asyncio
async def test_workflow_retry_on_failure(workflow_engine):
    """Test that workflows are retried on failure."""
    
    class FailingWorkflow(Workflow):
        def __init__(self):
            self.name = "failing-workflow"
            self.attempt_count = 0
        
        async def execute(self, context: dict) -> dict:
            self.attempt_count += 1
            if self.attempt_count < 3:
                raise RuntimeError("Simulated failure")
            return {"status": "success", "attempts": self.attempt_count}
        
        async def validate_inputs(self, context: dict) -> None:
            pass
        
        async def validate_outputs(self, result: dict) -> None:
            pass
    
    workflow = FailingWorkflow()
    workflow_engine.register_workflow(workflow)
    
    # Should succeed after retries
    result = await workflow_engine.execute_workflow(
        "failing-workflow",
        {"workflow_name": "failing-workflow"}
    )
    
    assert result["status"] == "success"
    assert result["attempts"] == 3


@pytest.mark.asyncio
async def test_metrics_accuracy_under_load(workflow_engine):
    """Test that metrics remain accurate under concurrent load."""
    workflow = MockWorkflow("load-test", delay=0.01)
    workflow_engine.register_workflow(workflow)
    
    num_workflows = 50
    tasks = []
    
    for i in range(num_workflows):
        task = asyncio.create_task(
            workflow_engine.execute_workflow(
                "load-test",
                {"workflow_name": "load-test", "index": i}
            )
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Count successes
    successes = sum(1 for r in results if not isinstance(r, Exception))
    
    # Verify metrics match actual results
    metrics = await workflow_engine.get_metrics()
    assert metrics["total_executions"] == num_workflows
    assert metrics["successful_executions"] == successes
    
    # Verify average execution time is reasonable
    assert metrics["average_execution_time"] > 0
    assert metrics["average_execution_time"] < 1.0  # Should complete quickly


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
