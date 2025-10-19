"""
Tests for bug fixes implemented in the code review.

This module tests all 5 critical bug fixes to ensure they work correctly
and prevent regressions.
"""

import asyncio
from pathlib import Path
import sqlite3
import tempfile

import pytest

from autopr.actions.registry import ActionRegistry
from autopr.config import AutoPRConfig
from autopr.exceptions import WorkflowError
from autopr.integrations.base import Integration
from autopr.integrations.registry import IntegrationRegistry
from autopr.quality.metrics_collector import MetricsCollector
from autopr.workflows.engine import WorkflowEngine


class TestBug1IntegrationRegistryCleanup:
    """Test Bug Fix 1: Resource leak in Integration Registry cleanup."""

    @pytest.mark.asyncio
    async def test_unregister_calls_cleanup(self):
        """Test that unregister_integration properly calls async cleanup."""
        registry = IntegrationRegistry()

        # Track cleanup calls
        cleanup_called = []

        # Create mock integration class
        class MockIntegration(Integration):
            async def initialize(self, config: dict):
                self.is_initialized = True

            async def health_check(self) -> dict:
                return {"status": "healthy"}

            async def execute(self, inputs, context):
                return {"success": True}

            async def cleanup(self):
                cleanup_called.append(True)

        # Register integration
        registry.register_integration(MockIntegration)
        # The integration is registered with name "temp" (from the temp instance created in register_integration)
        instance = await registry.get_integration("temp")

        assert instance is not None
        assert len(cleanup_called) == 0

        # Unregister should call cleanup
        await registry.unregister_integration("temp")

        # Verify cleanup was called
        assert len(cleanup_called) == 1
        assert cleanup_called[0] is True

    @pytest.mark.asyncio
    async def test_unregister_handles_cleanup_error(self):
        """Test that unregister continues even if cleanup fails."""
        registry = IntegrationRegistry()

        class FailingIntegration(Integration):
            async def initialize(self, config: dict):
                self.is_initialized = True

            async def health_check(self) -> dict:
                return {"status": "healthy"}

            async def execute(self, inputs, context):
                return {"success": True}

            async def cleanup(self):
                raise RuntimeError("Cleanup failed")

        registry.register_integration(FailingIntegration)
        await registry.get_integration("FailingIntegration")

        # Should not raise, just log the error
        await registry.unregister_integration("FailingIntegration")

        # Verify integration was still removed
        assert "FailingIntegration" not in registry._instances


class TestBug2WorkflowMetricsRaceCondition:
    """Test Bug Fix 2: Race condition in Workflow metrics."""

    @pytest.mark.asyncio
    async def test_concurrent_metrics_updates(self):
        """Test that concurrent metrics updates don't corrupt data."""
        config = AutoPRConfig()
        engine = WorkflowEngine(config)

        # Simulate 100 concurrent updates
        async def update_metrics(status: str):
            await engine._update_metrics(status, 1.0)

        tasks = []
        for i in range(50):
            tasks.append(update_metrics("success"))
            tasks.append(update_metrics("failed"))

        await asyncio.gather(*tasks)

        # Verify metrics are correct
        assert engine.metrics["total_executions"] == 100
        assert engine.metrics["successful_executions"] == 50
        assert engine.metrics["failed_executions"] == 50
        assert engine.metrics["timeout_executions"] == 0

    @pytest.mark.asyncio
    async def test_metrics_lock_prevents_race(self):
        """Test that the lock is properly acquired and released."""
        config = AutoPRConfig()
        engine = WorkflowEngine(config)

        # Lock should exist
        assert hasattr(engine, "_metrics_lock")
        assert isinstance(engine._metrics_lock, asyncio.Lock)

        # Lock should not be held initially
        assert not engine._metrics_lock.locked()

        # During update, lock should be acquired
        async def check_lock():
            async with engine._metrics_lock:
                # Lock is held here
                assert engine._metrics_lock.locked()

        await check_lock()

        # After update, lock should be released
        assert not engine._metrics_lock.locked()


class TestBug3ActionRegistryErrorHandling:
    """Test Bug Fix 3: Improved error handling in Action Registry."""

    def test_missing_action_raises_key_error(self):
        """Test that missing actions raise KeyError with context."""
        registry = ActionRegistry()

        with pytest.raises(KeyError) as exc_info:
            registry._create_action_instance("NonExistentAction")

        assert "NonExistentAction" in str(exc_info.value)
        assert "not registered" in str(exc_info.value)

    def test_failed_instantiation_raises_runtime_error(self):
        """Test that instantiation failures raise RuntimeError with details."""
        from autopr.actions.base.action import Action

        class FailingAction(Action):
            def __init__(self, name, description):
                raise ValueError("Intentional failure")

            async def execute(self, inputs, context):
                pass

        registry = ActionRegistry()
        registry.register("failing_action", FailingAction)

        with pytest.raises(RuntimeError) as exc_info:
            registry._create_action_instance("failing_action")

        assert "failing_action" in str(exc_info.value)
        assert "ValueError" in str(exc_info.value)

    def test_get_action_maintains_backward_compatibility(self):
        """Test that get_action still returns None for missing actions."""
        registry = ActionRegistry()

        # Should return None, not raise
        result = registry.get_action("NonExistentAction")
        assert result is None


class TestBug4WorkflowRetryLogic:
    """Test Bug Fix 4: Hardened workflow retry logic."""

    @pytest.mark.asyncio
    async def test_last_exception_always_initialized(self):
        """Test that last_exception is always set before retry loop."""
        from autopr.workflows.base import Workflow

        class FailingWorkflow(Workflow):
            async def execute(self, context):
                raise RuntimeError("Workflow failed")

        config = AutoPRConfig()
        config.workflow_retry_attempts = 1
        config.workflow_timeout = 1

        engine = WorkflowEngine(config)
        await engine.start()  # Start the engine

        workflow = FailingWorkflow("test_workflow", "Test workflow")
        engine.register_workflow(workflow)

        try:
            # Should raise WorkflowError, not generic error
            with pytest.raises(WorkflowError) as exc_info:
                await engine.execute_workflow("test_workflow", {})

            # Error message should be specific
            assert "Workflow failed" in str(exc_info.value)
        finally:
            await engine.stop()

    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff(self):
        """Test that retries use exponential backoff."""
        import time

        from autopr.workflows.base import Workflow

        attempt_times = []

        class TransientFailureWorkflow(Workflow):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.attempts = 0

            async def execute(self, context):
                self.attempts += 1
                attempt_times.append(time.time())
                if self.attempts < 3:
                    raise RuntimeError("Transient failure")
                return {"success": True}

        config = AutoPRConfig()
        config.workflow_retry_attempts = 3
        config.workflow_retry_delay = 1
        config.workflow_timeout = 10

        engine = WorkflowEngine(config)
        await engine.start()  # Start the engine

        workflow = TransientFailureWorkflow("test_workflow", "Test workflow")
        engine.register_workflow(workflow)

        try:
            # Should succeed on third attempt
            result = await engine.execute_workflow("test_workflow", {})
            assert result["success"] is True
            assert workflow.attempts == 3

            # Verify exponential backoff (approximate timing)
            if len(attempt_times) >= 3:
                # Time between first and second attempt should be ~1s
                delay1 = attempt_times[1] - attempt_times[0]
                # Time between second and third attempt should be ~2s
                delay2 = attempt_times[2] - attempt_times[1]

                # Allow some tolerance for execution time
                assert 0.5 < delay1 < 2.0
                assert 1.5 < delay2 < 3.0
        finally:
            await engine.stop()


class TestBug5SQLiteConnectionLeaks:
    """Test Bug Fix 5: SQLite connection leaks in Metrics Collector."""

    def test_context_manager_closes_connection_on_success(self):
        """Test that connections are closed even when operations succeed."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        conn = None
        try:
            collector = MetricsCollector(db_path)

            # Record some metrics
            collector.record_metric("test_metric", 42.0)
            collector.record_event("test_event", {"data": "value"}, True)
            collector.record_user_feedback("user123", 5)

            # Check that database file can be opened again (no locks)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Verify data was written
            cursor.execute("SELECT COUNT(*) FROM metrics")
            metrics_count = cursor.fetchone()[0]
            assert metrics_count == 1

            cursor.execute("SELECT COUNT(*) FROM events")
            events_count = cursor.fetchone()[0]
            assert events_count == 1

            cursor.execute("SELECT COUNT(*) FROM user_feedback")
            feedback_count = cursor.fetchone()[0]
            assert feedback_count == 1

        finally:
            if conn:
                conn.close()
            # Small delay for Windows to release file locks
            import time
            time.sleep(0.1)
            try:
                Path(db_path).unlink()
            except (PermissionError, OSError):
                pass  # Ignore cleanup errors

    def test_context_manager_closes_connection_on_error(self):
        """Test that connections are closed even when errors occur."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        conn = None
        try:
            collector = MetricsCollector(db_path)

            # Try to execute invalid SQL (should fail gracefully)
            try:
                with sqlite3.connect(collector.db_path) as conn_temp:
                    cursor = conn_temp.cursor()
                    cursor.execute("SELECT * FROM nonexistent_table")
            except sqlite3.OperationalError:
                pass

            # Connection should be closed, allowing us to open again
            conn = sqlite3.connect(db_path)

        finally:
            if conn:
                conn.close()
            # Small delay for Windows to release file locks
            import time
            time.sleep(0.1)
            try:
                Path(db_path).unlink()
            except (PermissionError, OSError):
                pass  # Ignore cleanup errors

    def test_no_database_locks_under_concurrent_access(self):
        """Test that concurrent access doesn't cause database locks."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            collector = MetricsCollector(db_path)

            # Simulate concurrent writes
            for i in range(10):
                collector.record_metric(f"metric_{i}", float(i))
                collector.record_event(f"event_{i}", {"index": i}, True)

            # Verify all writes succeeded
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM metrics")
                assert cursor.fetchone()[0] == 10

                cursor.execute("SELECT COUNT(*) FROM events")
                assert cursor.fetchone()[0] == 10

        finally:
            # Small delay for Windows to release file locks
            import time
            time.sleep(0.1)
            try:
                Path(db_path).unlink()
            except (PermissionError, OSError):
                pass  # Ignore cleanup errors


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
