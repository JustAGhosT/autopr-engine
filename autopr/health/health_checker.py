"""
Comprehensive health check system for AutoPR Engine.

Monitors database connectivity, LLM providers, integrations, and system resources.
"""

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
import logging
import psutil
import sqlite3
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a health check operation."""

    component: str
    status: str  # 'healthy', 'degraded', 'unhealthy'
    message: str
    details: dict[str, Any]
    timestamp: datetime
    response_time_ms: float


class HealthChecker:
    """
    Comprehensive health checker for AutoPR Engine components.

    Checks:
    - Database connectivity
    - LLM provider availability
    - Integration health
    - System resources (CPU, memory, disk)
    """

    def __init__(self, engine: Any) -> None:
        """
        Initialize health checker.

        Args:
            engine: AutoPREngine instance
        """
        self.engine = engine

    async def check_all(self) -> dict[str, HealthCheckResult]:
        """
        Run all health checks in parallel.

        Returns:
            Dictionary mapping component names to health check results
        """
        checks = [
            self.check_database(),
            self.check_llm_providers(),
            self.check_integrations(),
            self.check_system_resources(),
            self.check_workflow_engine(),
        ]

        results = await asyncio.gather(*checks, return_exceptions=True)

        health_status = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Health check failed with exception: {result}")
                health_status["error"] = HealthCheckResult(
                    component="error",
                    status="unhealthy",
                    message=str(result),
                    details={},
                    timestamp=datetime.now(tz=UTC),
                    response_time_ms=0.0,
                )
            elif isinstance(result, HealthCheckResult):
                health_status[result.component] = result

        return health_status

    async def check_database(self) -> HealthCheckResult:
        """Check database connectivity."""
        start_time = asyncio.get_event_loop().time()

        try:
            # Try to connect and execute a simple query
            if hasattr(self.engine.config, "database_url") and self.engine.config.database_url:
                # For SQLite or other databases
                db_path = self.engine.config.database_url
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                conn.close()

                response_time = (asyncio.get_event_loop().time() - start_time) * 1000

                return HealthCheckResult(
                    component="database",
                    status="healthy",
                    message="Database connection successful",
                    details={"database_type": "sqlite", "response_time_ms": response_time},
                    timestamp=datetime.now(tz=UTC),
                    response_time_ms=response_time,
                )
            else:
                return HealthCheckResult(
                    component="database",
                    status="degraded",
                    message="No database configured",
                    details={},
                    timestamp=datetime.now(tz=UTC),
                    response_time_ms=0.0,
                )

        except Exception as e:
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.exception("Database health check failed")

            return HealthCheckResult(
                component="database",
                status="unhealthy",
                message=f"Database connection failed: {e}",
                details={"error": str(e)},
                timestamp=datetime.now(tz=UTC),
                response_time_ms=response_time,
            )

    async def check_llm_providers(self) -> HealthCheckResult:
        """Check LLM provider availability."""
        start_time = asyncio.get_event_loop().time()

        try:
            available_providers = self.engine.llm_manager.list_providers()
            default_provider = self.engine.llm_manager.get_default_provider()

            if not available_providers:
                response_time = (asyncio.get_event_loop().time() - start_time) * 1000
                return HealthCheckResult(
                    component="llm_providers",
                    status="unhealthy",
                    message="No LLM providers available",
                    details={"provider_count": 0},
                    timestamp=datetime.now(tz=UTC),
                    response_time_ms=response_time,
                )

            response_time = (asyncio.get_event_loop().time() - start_time) * 1000

            return HealthCheckResult(
                component="llm_providers",
                status="healthy",
                message=f"{len(available_providers)} provider(s) available",
                details={
                    "providers": available_providers,
                    "default_provider": default_provider,
                    "provider_count": len(available_providers),
                },
                timestamp=datetime.now(tz=UTC),
                response_time_ms=response_time,
            )

        except Exception as e:
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.exception("LLM provider health check failed")

            return HealthCheckResult(
                component="llm_providers",
                status="unhealthy",
                message=f"LLM provider check failed: {e}",
                details={"error": str(e)},
                timestamp=datetime.now(tz=UTC),
                response_time_ms=response_time,
            )

    async def check_integrations(self) -> HealthCheckResult:
        """Check integration status."""
        start_time = asyncio.get_event_loop().time()

        try:
            all_integrations = self.engine.integration_registry.get_all_integrations()
            initialized = self.engine.integration_registry.get_initialized_integrations()

            response_time = (asyncio.get_event_loop().time() - start_time) * 1000

            if not all_integrations:
                return HealthCheckResult(
                    component="integrations",
                    status="degraded",
                    message="No integrations registered",
                    details={"total": 0, "initialized": 0},
                    timestamp=datetime.now(tz=UTC),
                    response_time_ms=response_time,
                )

            status = "healthy" if len(initialized) == len(all_integrations) else "degraded"

            return HealthCheckResult(
                component="integrations",
                status=status,
                message=f"{len(initialized)}/{len(all_integrations)} integrations healthy",
                details={
                    "total_integrations": len(all_integrations),
                    "initialized_integrations": len(initialized),
                    "integration_names": all_integrations,
                },
                timestamp=datetime.now(tz=UTC),
                response_time_ms=response_time,
            )

        except Exception as e:
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.exception("Integration health check failed")

            return HealthCheckResult(
                component="integrations",
                status="unhealthy",
                message=f"Integration check failed: {e}",
                details={"error": str(e)},
                timestamp=datetime.now(tz=UTC),
                response_time_ms=response_time,
            )

    async def check_system_resources(self) -> HealthCheckResult:
        """Check system resource utilization."""
        start_time = asyncio.get_event_loop().time()

        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            response_time = (asyncio.get_event_loop().time() - start_time) * 1000

            # Determine status based on thresholds
            status = "healthy"
            warnings = []

            if cpu_percent > 80:
                status = "degraded"
                warnings.append(f"High CPU usage: {cpu_percent}%")

            if memory.percent > 85:
                status = "degraded"
                warnings.append(f"High memory usage: {memory.percent}%")

            if disk.percent > 90:
                status = "degraded"
                warnings.append(f"High disk usage: {disk.percent}%")

            message = "System resources healthy"
            if warnings:
                message = f"System resources degraded: {', '.join(warnings)}"

            return HealthCheckResult(
                component="system_resources",
                status=status,
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free / (1024**3),
                },
                timestamp=datetime.now(tz=UTC),
                response_time_ms=response_time,
            )

        except Exception as e:
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.exception("System resources health check failed")

            return HealthCheckResult(
                component="system_resources",
                status="unhealthy",
                message=f"System resources check failed: {e}",
                details={"error": str(e)},
                timestamp=datetime.now(tz=UTC),
                response_time_ms=response_time,
            )

    async def check_workflow_engine(self) -> HealthCheckResult:
        """Check workflow engine status."""
        start_time = asyncio.get_event_loop().time()

        try:
            status_info = self.engine.workflow_engine.get_status()
            metrics = self.engine.workflow_engine.get_metrics()

            response_time = (asyncio.get_event_loop().time() - start_time) * 1000

            # Determine health based on error rate and running status
            is_running = status_info.get("running", False)
            error_rate = metrics.get("error_rate_percent", 0)

            if not is_running:
                status = "unhealthy"
                message = "Workflow engine is not running"
            elif error_rate > 50:
                status = "degraded"
                message = f"High error rate: {error_rate:.1f}%"
            else:
                status = "healthy"
                message = "Workflow engine running normally"

            return HealthCheckResult(
                component="workflow_engine",
                status=status,
                message=message,
                details={
                    "running": is_running,
                    "registered_workflows": status_info.get("registered_workflows", 0),
                    "running_workflows": status_info.get("running_workflows", 0),
                    "success_rate": metrics.get("success_rate_percent", 0),
                    "avg_execution_time": metrics.get("average_execution_time", 0),
                },
                timestamp=datetime.now(tz=UTC),
                response_time_ms=response_time,
            )

        except Exception as e:
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.exception("Workflow engine health check failed")

            return HealthCheckResult(
                component="workflow_engine",
                status="unhealthy",
                message=f"Workflow engine check failed: {e}",
                details={"error": str(e)},
                timestamp=datetime.now(tz=UTC),
                response_time_ms=response_time,
            )

    def get_overall_status(self, health_results: dict[str, HealthCheckResult]) -> str:
        """
        Determine overall system health from individual component checks.

        Args:
            health_results: Dictionary of health check results

        Returns:
            Overall status: 'healthy', 'degraded', or 'unhealthy'
        """
        if not health_results:
            return "unhealthy"

        statuses = [result.status for result in health_results.values()]

        if "unhealthy" in statuses:
            return "unhealthy"
        if "degraded" in statuses:
            return "degraded"
        return "healthy"
