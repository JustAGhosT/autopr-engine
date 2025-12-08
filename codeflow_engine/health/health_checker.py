"""
Health Checker

Comprehensive health checking system for AutoPR components.
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any


logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Overall health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status of a single component."""
    name: str
    status: HealthStatus
    message: str
    response_time_ms: float
    details: dict[str, Any] | None = None


class HealthChecker:
    """
    Comprehensive health checker for AutoPR components.

    Checks health of:
    - Database connectivity
    - LLM provider availability
    - Integration status
    - System resources (CPU, memory, disk)
    - Workflow engine health
    """

    # Cache TTL in seconds
    CACHE_TTL_SECONDS = 10

    def __init__(self, engine: Any = None):
        """
        Initialize health checker.

        Args:
            engine: AutoPREngine instance (optional)
        """
        self.engine = engine
        self.last_check_time: float | None = None
        self.last_check_results: dict[str, ComponentHealth] | None = None
        self._last_cpu_percent: float = 0.0
        self._last_cpu_check_time: float = 0.0
    
    async def check_all(self, use_cache: bool = False) -> dict[str, Any]:
        """
        Perform comprehensive health check on all components.

        Args:
            use_cache: If True, return cached results if available and fresh

        Returns:
            Dictionary with overall health status and component details
        """
        # Return cached results if fresh and caching is enabled
        if use_cache and self._is_cache_valid():
            cached = self.get_cached_results()
            if cached:
                cached["cached"] = True
                return cached

        start_time = time.time()

        # Run all health checks in parallel
        checks = [
            self._check_database(),
            self._check_llm_providers(),
            self._check_integrations(),
            self._check_system_resources(),
            self._check_workflow_engine(),
        ]

        results = await asyncio.gather(*checks, return_exceptions=True)
        
        # Process results
        component_health: dict[str, ComponentHealth] = {}
        for result in results:
            if isinstance(result, Exception):
                logger.exception("Health check failed with exception", exc_info=result)
                component_health["error"] = ComponentHealth(
                    name="error",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {result}",
                    response_time_ms=0.0,
                )
            elif result:
                component_health[result.name] = result
        
        # Determine overall health
        overall_status = self._determine_overall_health(component_health)
        
        # Calculate total response time
        total_time_ms = (time.time() - start_time) * 1000
        
        # Store results for caching
        self.last_check_time = time.time()
        self.last_check_results = component_health
        
        return {
            "status": overall_status.value,
            "timestamp": time.time(),
            "response_time_ms": total_time_ms,
            "components": {
                name: {
                    "status": health.status.value,
                    "message": health.message,
                    "response_time_ms": health.response_time_ms,
                    "details": health.details,
                }
                for name, health in component_health.items()
            },
        }
    
    async def _check_database(self) -> ComponentHealth:
        """Check database connectivity."""
        start_time = time.time()
        
        try:
            # Check if we can access metrics collector database
            if self.engine and hasattr(self.engine, 'metrics_collector'):
                from codeflow_engine.quality.metrics_collector import MetricsCollector
                collector = MetricsCollector()
                
                # Try a simple query
                import sqlite3
                with sqlite3.connect(collector.db_path, timeout=5) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                    table_count = cursor.fetchone()[0]
                
                response_time = (time.time() - start_time) * 1000
                
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    message="Database connection successful",
                    response_time_ms=response_time,
                    details={"table_count": table_count},
                )
            else:
                response_time = (time.time() - start_time) * 1000
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.DEGRADED,
                    message="Metrics collector not configured",
                    response_time_ms=response_time,
                )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.exception("Database health check failed")
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database check failed: {e}",
                response_time_ms=response_time,
            )
    
    async def _check_llm_providers(self) -> ComponentHealth:
        """Check LLM provider availability."""
        start_time = time.time()
        
        try:
            if not self.engine or not hasattr(self.engine, 'llm_manager'):
                response_time = (time.time() - start_time) * 1000
                return ComponentHealth(
                    name="llm_providers",
                    status=HealthStatus.DEGRADED,
                    message="LLM manager not configured",
                    response_time_ms=response_time,
                )
            
            providers = self.engine.llm_manager.list_providers()
            
            if not providers:
                response_time = (time.time() - start_time) * 1000
                return ComponentHealth(
                    name="llm_providers",
                    status=HealthStatus.UNHEALTHY,
                    message="No LLM providers available",
                    response_time_ms=response_time,
                )
            
            # Check circuit breaker status
            cb_status = self.engine.llm_manager.get_circuit_breaker_status()
            available_providers = [
                name for name, stats in cb_status.items()
                if stats["state"] != "open"
            ]
            
            response_time = (time.time() - start_time) * 1000
            
            if not available_providers:
                return ComponentHealth(
                    name="llm_providers",
                    status=HealthStatus.UNHEALTHY,
                    message="All LLM providers are unavailable (circuit breakers open)",
                    response_time_ms=response_time,
                    details={
                        "total_providers": len(providers),
                        "available_providers": 0,
                        "circuit_breaker_status": cb_status,
                    },
                )
            elif len(available_providers) < len(providers):
                return ComponentHealth(
                    name="llm_providers",
                    status=HealthStatus.DEGRADED,
                    message=f"{len(available_providers)}/{len(providers)} LLM providers available",
                    response_time_ms=response_time,
                    details={
                        "total_providers": len(providers),
                        "available_providers": len(available_providers),
                        "circuit_breaker_status": cb_status,
                    },
                )
            else:
                return ComponentHealth(
                    name="llm_providers",
                    status=HealthStatus.HEALTHY,
                    message=f"All {len(providers)} LLM providers available",
                    response_time_ms=response_time,
                    details={
                        "total_providers": len(providers),
                        "available_providers": len(available_providers),
                        "providers": providers,
                    },
                )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.exception("LLM provider health check failed")
            return ComponentHealth(
                name="llm_providers",
                status=HealthStatus.UNHEALTHY,
                message=f"LLM provider check failed: {e}",
                response_time_ms=response_time,
            )
    
    async def _check_integrations(self) -> ComponentHealth:
        """Check integration status."""
        start_time = time.time()
        
        try:
            if not self.engine or not hasattr(self.engine, 'integration_registry'):
                response_time = (time.time() - start_time) * 1000
                return ComponentHealth(
                    name="integrations",
                    status=HealthStatus.DEGRADED,
                    message="Integration registry not configured",
                    response_time_ms=response_time,
                )
            
            registry = self.engine.integration_registry
            all_integrations = registry.get_all_integrations()
            initialized = registry.get_initialized_integrations()
            
            # Perform health check on initialized integrations
            health_results = await registry.health_check_all()
            unhealthy_count = sum(
                1 for status in health_results.values()
                if status.get("status") == "error"
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if unhealthy_count > 0:
                return ComponentHealth(
                    name="integrations",
                    status=HealthStatus.DEGRADED,
                    message=f"{unhealthy_count}/{len(initialized)} integrations unhealthy",
                    response_time_ms=response_time,
                    details={
                        "total": len(all_integrations),
                        "initialized": len(initialized),
                        "unhealthy": unhealthy_count,
                        "health_results": health_results,
                    },
                )
            else:
                return ComponentHealth(
                    name="integrations",
                    status=HealthStatus.HEALTHY,
                    message=f"{len(initialized)} integrations healthy",
                    response_time_ms=response_time,
                    details={
                        "total": len(all_integrations),
                        "initialized": len(initialized),
                        "integrations": all_integrations,
                    },
                )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.exception("Integration health check failed")
            return ComponentHealth(
                name="integrations",
                status=HealthStatus.UNHEALTHY,
                message=f"Integration check failed: {e}",
                response_time_ms=response_time,
            )
    
    async def _check_system_resources(self) -> ComponentHealth:
        """Check system resource utilization."""
        start_time = time.time()

        try:
            import psutil

            # CPU usage - use non-blocking call (interval=None) with cached fallback
            # This avoids the 100ms+ blocking delay from interval=0.1
            cpu_percent = psutil.cpu_percent(interval=None)
            if cpu_percent == 0.0 and self._last_cpu_percent > 0:
                # Use cached value if current reading is 0 (first call returns 0)
                cpu_percent = self._last_cpu_percent
            else:
                self._last_cpu_percent = cpu_percent
                self._last_cpu_check_time = time.time()
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine status based on resource utilization
            if cpu_percent > 90 or memory_percent > 90 or disk_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = "Critical resource utilization"
            elif cpu_percent > 75 or memory_percent > 75 or disk_percent > 80:
                status = HealthStatus.DEGRADED
                message = "High resource utilization"
            else:
                status = HealthStatus.HEALTHY
                message = "Resource utilization normal"
            
            return ComponentHealth(
                name="system_resources",
                status=status,
                message=message,
                response_time_ms=response_time,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "memory_available_mb": memory.available / (1024 * 1024),
                    "disk_percent": disk_percent,
                    "disk_free_gb": disk.free / (1024 * 1024 * 1024),
                },
            )
        
        except ImportError:
            # psutil not available
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="system_resources",
                status=HealthStatus.DEGRADED,
                message="Resource monitoring not available (psutil not installed)",
                response_time_ms=response_time,
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.exception("System resource health check failed")
            return ComponentHealth(
                name="system_resources",
                status=HealthStatus.UNHEALTHY,
                message=f"Resource check failed: {e}",
                response_time_ms=response_time,
            )
    
    async def _check_workflow_engine(self) -> ComponentHealth:
        """Check workflow engine health."""
        start_time = time.time()
        
        try:
            if not self.engine or not hasattr(self.engine, 'workflow_engine'):
                response_time = (time.time() - start_time) * 1000
                return ComponentHealth(
                    name="workflow_engine",
                    status=HealthStatus.DEGRADED,
                    message="Workflow engine not configured",
                    response_time_ms=response_time,
                )
            
            engine_status = self.engine.workflow_engine.get_status()
            metrics = self.engine.workflow_engine.get_metrics()
            
            response_time = (time.time() - start_time) * 1000
            
            # Check if engine is running and has reasonable metrics
            if not engine_status.get("running"):
                return ComponentHealth(
                    name="workflow_engine",
                    status=HealthStatus.UNHEALTHY,
                    message="Workflow engine not running",
                    response_time_ms=response_time,
                    details=engine_status,
                )
            
            # Check error rate
            error_rate = metrics.get("failed_executions", 0) / max(metrics.get("total_executions", 1), 1)
            
            if error_rate > 0.5:
                status = HealthStatus.UNHEALTHY
                message = f"High error rate: {error_rate*100:.1f}%"
            elif error_rate > 0.2:
                status = HealthStatus.DEGRADED
                message = f"Elevated error rate: {error_rate*100:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = "Workflow engine healthy"
            
            return ComponentHealth(
                name="workflow_engine",
                status=status,
                message=message,
                response_time_ms=response_time,
                details={
                    "running": engine_status.get("running"),
                    "registered_workflows": engine_status.get("registered_workflows"),
                    "running_workflows": engine_status.get("running_workflows"),
                    "metrics": metrics,
                },
            )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.exception("Workflow engine health check failed")
            return ComponentHealth(
                name="workflow_engine",
                status=HealthStatus.UNHEALTHY,
                message=f"Workflow engine check failed: {e}",
                response_time_ms=response_time,
            )
    
    def _determine_overall_health(
        self, component_health: dict[str, ComponentHealth]
    ) -> HealthStatus:
        """
        Determine overall health based on component health.
        
        Args:
            component_health: Dictionary of component health statuses
            
        Returns:
            Overall health status
        """
        if not component_health:
            return HealthStatus.UNHEALTHY
        
        unhealthy_count = sum(
            1 for health in component_health.values()
            if health.status == HealthStatus.UNHEALTHY
        )
        degraded_count = sum(
            1 for health in component_health.values()
            if health.status == HealthStatus.DEGRADED
        )
        
        # If any component is unhealthy, overall is unhealthy
        if unhealthy_count > 0:
            return HealthStatus.UNHEALTHY
        
        # If any component is degraded, overall is degraded
        if degraded_count > 0:
            return HealthStatus.DEGRADED
        
        # All components are healthy
        return HealthStatus.HEALTHY
    
    def get_cached_results(self) -> dict[str, Any] | None:
        """
        Get cached health check results.

        Returns:
            Last health check results, or None if no cached results
        """
        if not self.last_check_results:
            return None

        return {
            "status": self._determine_overall_health(self.last_check_results).value,
            "timestamp": self.last_check_time,
            "components": {
                name: {
                    "status": health.status.value,
                    "message": health.message,
                    "response_time_ms": health.response_time_ms,
                    "details": health.details,
                }
                for name, health in self.last_check_results.items()
            },
        }

    def _is_cache_valid(self) -> bool:
        """Check if cached results are still valid."""
        if self.last_check_time is None:
            return False
        return (time.time() - self.last_check_time) < self.CACHE_TTL_SECONDS

    async def check_quick(self) -> dict[str, Any]:
        """
        Perform a quick health check suitable for high-frequency polling.

        Returns cached results if available, otherwise performs minimal checks.
        This is optimized for low latency (<10ms) responses.

        Returns:
            Dictionary with health status
        """
        start_time = time.time()

        # Return cached results if fresh
        if self._is_cache_valid():
            cached = self.get_cached_results()
            if cached:
                cached["cached"] = True
                return cached

        # Perform minimal health check (no external calls)
        try:
            import psutil

            # Non-blocking CPU check
            cpu_percent = psutil.cpu_percent(interval=None)
            if cpu_percent == 0.0 and self._last_cpu_percent > 0:
                cpu_percent = self._last_cpu_percent
            else:
                self._last_cpu_percent = cpu_percent

            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            response_time = (time.time() - start_time) * 1000

            if cpu_percent > 90 or memory_percent > 90:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY

            return {
                "status": status.value,
                "timestamp": time.time(),
                "response_time_ms": response_time,
                "cached": False,
                "quick_check": True,
                "resources": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                },
            }

        except ImportError:
            # psutil not available, return basic healthy status
            return {
                "status": HealthStatus.HEALTHY.value,
                "timestamp": time.time(),
                "response_time_ms": (time.time() - start_time) * 1000,
                "cached": False,
                "quick_check": True,
            }
