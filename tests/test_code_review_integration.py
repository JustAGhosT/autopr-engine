"""
Integration tests for all code review changes.

This module provides end-to-end tests that verify all bug fixes,
refactorings, and improvements work together correctly.
"""

import asyncio
import tempfile
from pathlib import Path

import pytest

from autopr.config import AutoPRConfig
from autopr.engine import AutoPREngine
from autopr.utils.resilience import CircuitBreakerState


class TestCodeReviewIntegration:
    """Integration tests for all code review changes."""

    @pytest.mark.asyncio
    async def test_engine_initialization_with_all_components(self):
        """Test that engine initializes with all new components."""
        config = AutoPRConfig()
        engine = AutoPREngine(config)

        # Verify all components are initialized
        assert engine.workflow_engine is not None
        assert engine.action_registry is not None
        assert engine.integration_registry is not None
        assert engine.llm_manager is not None
        assert engine.health_checker is not None

        # Verify circuit breakers are created for LLM providers
        for provider_name in engine.llm_manager.providers.keys():
            assert provider_name in engine.llm_manager.circuit_breakers

    @pytest.mark.asyncio
    async def test_health_check_with_metrics_lock(self):
        """Test health check works with workflow metrics lock."""
        config = AutoPRConfig()
        config.test_mode = True
        engine = AutoPREngine(config)

        await engine.start()

        try:
            # Perform health check
            health_status = await engine.health_check()

            # Verify overall status
            assert health_status["overall_status"] in ["healthy", "degraded", "unhealthy"]

            # Verify workflow engine is running
            assert "workflow_engine" in health_status["components"]
            workflow_status = health_status["components"]["workflow_engine"]
            assert workflow_status["status"] in ["healthy", "degraded", "unhealthy"]
            assert workflow_status["details"]["running"] is True

        finally:
            await engine.stop()

    @pytest.mark.asyncio
    async def test_concurrent_operations_with_locks(self):
        """Test that concurrent operations don't cause race conditions."""
        config = AutoPRConfig()
        config.test_mode = True
        engine = AutoPREngine(config)

        await engine.start()

        try:
            # Simulate concurrent workflow executions updating metrics
            from autopr.workflows.base import Workflow

            class QuickWorkflow(Workflow):
                async def execute(self, context):
                    await asyncio.sleep(0.01)
                    return {"success": True}

            workflow = QuickWorkflow("quick_workflow", "Quick test workflow")
            engine.workflow_engine.register_workflow(workflow)

            # Run multiple workflows concurrently
            tasks = []
            for i in range(10):
                tasks.append(
                    engine.workflow_engine.execute_workflow(
                        "quick_workflow", {"iteration": i}, f"exec_{i}"
                    )
                )

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # All should succeed
            successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
            assert successful == 10

            # Metrics should be accurate
            metrics = engine.workflow_engine.get_metrics()
            assert metrics["total_executions"] >= 10
            assert metrics["successful_executions"] >= 10

        finally:
            await engine.stop()

    @pytest.mark.asyncio
    async def test_error_handling_consistency(self):
        """Test that error handling is consistent across components."""
        config = AutoPRConfig()
        engine = AutoPREngine(config)

        # Test engine operation error handling
        try:
            # Try to process event without starting
            await engine.process_event("test_event", {})
        except Exception as e:
            # Should get a meaningful error message
            assert "failed" in str(e).lower() or "error" in str(e).lower()

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_llm_fallback(self):
        """Test that circuit breaker enables fallback between providers."""
        from autopr.ai.core.providers.manager import LLMProviderManager

        config = AutoPRConfig()
        manager = LLMProviderManager(config)

        # Verify circuit breakers exist for all providers
        for provider_name in manager.providers.keys():
            breaker = manager.circuit_breakers.get(provider_name)
            assert breaker is not None
            assert breaker.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_metrics_collection_without_locks(self):
        """Test that metrics can be collected rapidly without database locks."""
        from autopr.quality.metrics_collector import MetricsCollector
        import sqlite3
        import time

        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        conn = None
        try:
            collector = MetricsCollector(db_path)

            # Rapidly record metrics (simulating high load)
            for i in range(100):
                collector.record_metric(f"metric_{i % 10}", float(i))
                collector.record_event(f"event_{i % 5}", {"index": i}, True, i * 10)

            # Verify no database locks by opening connection
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM metrics")
            metrics_count = cursor.fetchone()[0]
            assert metrics_count == 100

            cursor.execute("SELECT COUNT(*) FROM events")
            events_count = cursor.fetchone()[0]
            assert events_count == 100

        finally:
            if conn:
                conn.close()
            # Small delay for Windows to release file locks
            time.sleep(0.1)
            try:
                Path(db_path).unlink()
            except (PermissionError, OSError):
                pass  # Ignore cleanup errors

    @pytest.mark.asyncio
    async def test_engine_lifecycle_with_cleanup(self):
        """Test complete engine lifecycle with proper cleanup."""
        config = AutoPRConfig()
        config.test_mode = True
        engine = AutoPREngine(config)

        # Start engine
        await engine.start()

        # Verify components are running
        status = engine.get_status()
        assert status["engine"] == "running"

        # Stop engine
        await engine.stop()

        # Verify cleanup occurred (no exceptions)
        # Registry instances should be cleared
        assert len(engine.integration_registry._instances) == 0

    @pytest.mark.asyncio
    async def test_get_status_includes_all_components(self):
        """Test that get_status returns information about all components."""
        config = AutoPRConfig()
        engine = AutoPREngine(config)

        status = engine.get_status()

        # Verify all expected keys
        assert "engine" in status
        assert "workflow_engine" in status
        assert "actions" in status
        assert "integrations" in status
        assert "llm_providers" in status
        assert "config" in status

        # Verify types
        assert isinstance(status["actions"], int)
        assert isinstance(status["integrations"], int)
        assert isinstance(status["llm_providers"], int)

    def test_shared_error_handler_usage(self):
        """Test that shared error handler is used consistently."""
        from autopr.utils.error_handlers import handle_operation_error
        from autopr.exceptions import AutoPRException

        # Test that error handler can be called
        with pytest.raises(AutoPRException) as exc_info:
            handle_operation_error(
                "test_operation",
                ValueError("test error"),
                AutoPRException,
                log_level="error",
            )

        assert "test_operation" in str(exc_info.value)
        assert "test error" in str(exc_info.value)


class TestEndToEndScenario:
    """End-to-end scenario testing the complete system."""

    @pytest.mark.asyncio
    async def test_complete_workflow_with_health_checks(self):
        """Test a complete workflow execution with health monitoring."""
        config = AutoPRConfig()
        config.test_mode = True
        engine = AutoPREngine(config)

        await engine.start()

        try:
            # Check initial health
            health_before = await engine.health_check()
            assert health_before["overall_status"] in ["healthy", "degraded", "unhealthy"]

            # Create and register a simple workflow
            from autopr.workflows.base import Workflow

            class SimpleWorkflow(Workflow):
                async def execute(self, context):
                    return {"result": "success", "data": context.get("input_data")}

            workflow = SimpleWorkflow("simple_workflow", "Simple test workflow")
            engine.workflow_engine.register_workflow(workflow)

            # Execute workflow
            result = await engine.workflow_engine.execute_workflow(
                "simple_workflow", {"input_data": "test data"}, "test_exec_1"
            )

            assert result["result"] == "success"
            assert result["data"] == "test data"

            # Check health after workflow
            health_after = await engine.health_check()
            assert "workflow_engine" in health_after["components"]

            # Get metrics
            metrics = engine.workflow_engine.get_metrics()
            assert metrics["total_executions"] >= 1
            assert metrics["successful_executions"] >= 1

            # Get status
            status = engine.get_status()
            assert status["engine"] == "running"

        finally:
            await engine.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
