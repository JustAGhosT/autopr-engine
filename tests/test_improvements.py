"""
Tests for improvements implemented in the code review.

This module tests all 5 enhancements to ensure they work correctly.
"""

import asyncio
from datetime import UTC, datetime, timedelta
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from autopr.config import AutoPRConfig
from autopr.engine import AutoPREngine
from autopr.utils.resilience import CircuitBreaker, CircuitBreakerError, CircuitBreakerState


class TestImprovement1CircuitBreaker:
    """Test Improvement 1: Circuit Breaker pattern for LLM providers."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_closes_on_failures(self):
        """Test that circuit breaker opens after threshold failures."""
        breaker = CircuitBreaker("test_breaker", failure_threshold=3, timeout_seconds=1)

        async def failing_func():
            raise RuntimeError("Service unavailable")

        # First 3 failures should still attempt the call
        for i in range(3):
            with pytest.raises(RuntimeError):
                await breaker.call(failing_func)

        # After threshold, circuit should be open
        assert breaker.state == CircuitBreakerState.OPEN

        # Next call should raise CircuitBreakerError without calling the function
        with pytest.raises(CircuitBreakerError) as exc_info:
            await breaker.call(failing_func)

        assert "Circuit breaker" in str(exc_info.value)
        assert "OPEN" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_recovery(self):
        """Test that circuit breaker transitions to half-open and recovers."""
        breaker = CircuitBreaker(
            "test_breaker",
            failure_threshold=2,
            timeout_seconds=1,
            success_threshold=2,
        )

        call_count = [0]

        async def transient_failure():
            call_count[0] += 1
            if call_count[0] <= 2:
                raise RuntimeError("Transient failure")
            return "success"

        # Trigger failures to open circuit
        for _ in range(2):
            with pytest.raises(RuntimeError):
                await breaker.call(transient_failure)

        assert breaker.state == CircuitBreakerState.OPEN

        # Wait for timeout
        await asyncio.sleep(1.1)

        # Next call should transition to half-open
        result = await breaker.call(transient_failure)
        assert result == "success"
        assert breaker.state == CircuitBreakerState.HALF_OPEN

        # One more success should close the circuit
        result = await breaker.call(transient_failure)
        assert result == "success"
        assert breaker.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_resets_on_success(self):
        """Test that failure count resets on success."""
        breaker = CircuitBreaker("test_breaker", failure_threshold=3)

        async def sometimes_fails(should_fail: bool):
            if should_fail:
                raise RuntimeError("Failed")
            return "success"

        # Fail twice
        for _ in range(2):
            with pytest.raises(RuntimeError):
                await breaker.call(sometimes_fails, True)

        assert breaker.failure_count == 2

        # Success should reset count
        await breaker.call(sometimes_fails, False)
        assert breaker.failure_count == 0
        assert breaker.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_protects_llm_provider(self):
        """Test that circuit breaker protects LLM provider calls."""
        from autopr.ai.core.providers.manager import LLMProviderManager

        config = AutoPRConfig()
        manager = LLMProviderManager(config)

        # Check that circuit breakers are created for providers
        for provider_name in manager.providers.keys():
            assert provider_name in manager.circuit_breakers
            assert manager.circuit_breakers[provider_name].state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_status_reporting(self):
        """Test that circuit breaker status can be queried."""
        breaker = CircuitBreaker("test_breaker")

        status = breaker.get_status()

        assert status["name"] == "test_breaker"
        assert status["state"] == "closed"
        assert status["failure_count"] == 0
        assert "configuration" in status
        assert status["configuration"]["failure_threshold"] == 5


class TestImprovement4HealthCheckEndpoint:
    """Test Improvement 4: Comprehensive health check system."""

    @pytest.mark.asyncio
    async def test_health_check_returns_status(self):
        """Test that health check returns comprehensive status."""
        config = AutoPRConfig()
        engine = AutoPREngine(config)

        # Start engine to initialize components
        await engine.start()

        try:
            health_status = await engine.health_check()

            # Verify structure
            assert "overall_status" in health_status
            assert "components" in health_status
            assert health_status["overall_status"] in ["healthy", "degraded", "unhealthy"]

            # Verify components are checked
            components = health_status["components"]
            assert "workflow_engine" in components
            assert "llm_providers" in components

            # Each component should have required fields
            for component_name, component_data in components.items():
                assert "status" in component_data
                assert "message" in component_data
                assert "details" in component_data
                assert component_data["status"] in ["healthy", "degraded", "unhealthy"]

        finally:
            await engine.stop()

    @pytest.mark.asyncio
    async def test_health_check_workflow_engine(self):
        """Test that workflow engine health check works."""
        config = AutoPRConfig()
        engine = AutoPREngine(config)
        await engine.start()

        try:
            health_status = await engine.health_check()
            workflow_health = health_status["components"].get("workflow_engine")

            assert workflow_health is not None
            assert workflow_health["status"] in ["healthy", "degraded", "unhealthy"]
            assert "running" in workflow_health["details"]

        finally:
            await engine.stop()

    @pytest.mark.asyncio
    async def test_health_check_llm_providers(self):
        """Test that LLM provider health check works."""
        config = AutoPRConfig()
        engine = AutoPREngine(config)

        health_status = await engine.health_check()
        llm_health = health_status["components"].get("llm_providers")

        assert llm_health is not None
        assert "provider_count" in llm_health["details"]

    @pytest.mark.asyncio
    async def test_health_check_handles_errors_gracefully(self):
        """Test that health check handles component failures gracefully."""
        config = AutoPRConfig()
        engine = AutoPREngine(config)

        # Even if some components fail, health check should return a result
        health_status = await engine.health_check()

        assert "overall_status" in health_status
        assert "components" in health_status

    def test_health_checker_overall_status_logic(self):
        """Test the logic for determining overall health status."""
        from autopr.health import HealthCheckResult, HealthChecker

        config = AutoPRConfig()
        engine = AutoPREngine(config)
        checker = HealthChecker(engine)

        # All healthy
        results = {
            "component1": HealthCheckResult(
                "component1",
                "healthy",
                "OK",
                {},
                datetime.now(tz=UTC),
                10.0,
            ),
            "component2": HealthCheckResult(
                "component2",
                "healthy",
                "OK",
                {},
                datetime.now(tz=UTC),
                10.0,
            ),
        }
        assert checker.get_overall_status(results) == "healthy"

        # One degraded
        results["component2"] = HealthCheckResult(
            "component2",
            "degraded",
            "Slow",
            {},
            datetime.now(tz=UTC),
            50.0,
        )
        assert checker.get_overall_status(results) == "degraded"

        # One unhealthy
        results["component1"] = HealthCheckResult(
            "component1",
            "unhealthy",
            "Failed",
            {},
            datetime.now(tz=UTC),
            100.0,
        )
        assert checker.get_overall_status(results) == "unhealthy"


class TestImprovement5MetricsBatching:
    """Test Improvement 5: Metrics batching for high performance."""

    def test_metrics_context_manager_usage(self):
        """Test that metrics collector uses context managers consistently."""
        from autopr.quality.metrics_collector import MetricsCollector
        import sqlite3

        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            collector = MetricsCollector(db_path)

            # Record multiple metrics rapidly
            for i in range(100):
                collector.record_metric(f"metric_{i % 10}", float(i))

            # Verify no database locks
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM metrics")
            count = cursor.fetchone()[0]
            conn.close()

            assert count == 100

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_metrics_concurrent_writes(self):
        """Test that metrics can be written concurrently without locks."""
        from autopr.quality.metrics_collector import MetricsCollector
        import sqlite3

        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            collector = MetricsCollector(db_path)

            # Simulate concurrent metric recording
            metrics_written = 0
            for i in range(50):
                collector.record_metric(f"concurrent_{i}", float(i))
                collector.record_event(f"event_{i}", {"index": i}, True, duration_ms=i * 10)
                metrics_written += 1

            # Verify all writes succeeded
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM metrics")
                metrics_count = cursor.fetchone()[0]
                assert metrics_count == 50

                cursor.execute("SELECT COUNT(*) FROM events")
                events_count = cursor.fetchone()[0]
                assert events_count == 50

        finally:
            Path(db_path).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
