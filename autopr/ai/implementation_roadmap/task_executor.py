"""
Task Executor for Implementation Roadmap
Handles the execution of individual implementation tasks
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from implementation_roadmap.task_definitions import Task, TaskRegistry


@dataclass
class TaskExecution:
    """Result of task execution"""

    task_name: str
    status: str  # "success", "error", "skipped"
    start_time: datetime
    end_time: datetime | None = None
    error_message: str | None = None
    files_created: list[str] = None
    logs: list[str] = None

    def __post_init__(self) -> None:
        if self.files_created is None:
            self.files_created = []
        if self.logs is None:
            self.logs = []

    @property
    def duration(self) -> float | None:
        """Get execution duration in seconds"""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class TaskExecutor:
    """Executes individual implementation tasks"""

    def __init__(self, task_registry: TaskRegistry) -> None:
        self.task_registry = task_registry
        self.project_root = Path.cwd()
        self.executions: dict[str, TaskExecution] = {}

    async def execute_task(
        self, task_name: str, dry_run: bool = False
    ) -> TaskExecution:
        """Execute a specific task"""
        task = self.task_registry.get_task(task_name)
        execution = TaskExecution(
            task_name=task_name, status="running", start_time=datetime.now()
        )

        self.executions[task_name] = execution

        try:
            if dry_run:
                execution.status = "skipped"
                execution.logs.append(f"DRY RUN: Would execute {task_name}")
                return execution

            # Execute the specific task implementation
            result = await self._execute_task_implementation(task, execution)

            if isinstance(result, Exception):
                execution.status = "error"
                execution.error_message = str(result)
            else:
                execution.status = "success"
                execution.files_created = task.files_created.copy()

        except Exception as e:
            execution.status = "error"
            execution.error_message = str(e)

        finally:
            execution.end_time = datetime.now()

        return execution

    async def _execute_task_implementation(
        self, task: Task, execution: TaskExecution
    ) -> TaskExecution | BaseException:
        """Execute the actual task implementation"""
        # For immediate priority tasks, we have real implementations
        if task.name == "setup_sentry_monitoring":
            return await self._setup_sentry_monitoring(execution)
        if task.name == "implement_structured_logging":
            return await self._implement_structured_logging(execution)
        if task.name == "setup_redis_caching":
            return await self._setup_redis_caching(execution)
        if task.name == "create_health_checks":
            return await self._create_health_checks(execution)
        if task.name == "implement_basic_circuit_breakers":
            return await self._implement_basic_circuit_breakers(execution)
        # For other tasks, create placeholder implementations
        return await self._create_placeholder_implementation(task, execution)

    async def _setup_sentry_monitoring(self, execution: TaskExecution) -> TaskExecution:
        """Setup Sentry for error tracking and performance monitoring"""
        execution.logs.append("Setting up Sentry monitoring...")

        # Create monitoring directory and basic Sentry config
        monitoring_dir = self.project_root / "autopr" / "monitoring"
        monitoring_dir.mkdir(parents=True, exist_ok=True)

        sentry_config = '''"""Sentry Configuration for AutoPR"""
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
import os

def initialize_sentry():
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[FastApiIntegration()],
            traces_sample_rate=0.1,
            environment=os.getenv("ENVIRONMENT", "development")
        )
'''

        await self._write_file(str(monitoring_dir / "sentry_config.py"), sentry_config)
        await self._write_file(
            str(monitoring_dir / "__init__.py"),
            "from .sentry_config import initialize_sentry",
        )
        await self._add_requirement("sentry-sdk[fastapi]>=1.32.0")

        execution.logs.append("✅ Sentry monitoring setup complete")
        return execution

    async def _implement_structured_logging(
        self, execution: TaskExecution
    ) -> TaskExecution:
        """Implement structured JSON logging"""
        execution.logs.append("Implementing structured logging...")

        logging_dir = self.project_root / "autopr" / "logging"
        logging_dir.mkdir(parents=True, exist_ok=True)

        logger_config = '''"""Structured Logging for AutoPR"""
import structlog
import logging
from contextvars import ContextVar

correlation_id: ContextVar = ContextVar('correlation_id', default=None)

def configure_logging():
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )

def get_logger(name: str = __name__):
    return structlog.get_logger(name)
'''

        await self._write_file(str(logging_dir / "structured_logger.py"), logger_config)
        await self._write_file(
            str(logging_dir / "__init__.py"),
            "from .structured_logger import configure_logging, get_logger",
        )
        await self._add_requirement("structlog>=23.1.0")

        execution.logs.append("✅ Structured logging implementation complete")
        return execution

    async def _setup_redis_caching(self, execution: TaskExecution) -> TaskExecution:
        """Setup Redis caching"""
        execution.logs.append("Setting up Redis caching...")

        caching_dir = self.project_root / "autopr" / "caching"
        caching_dir.mkdir(parents=True, exist_ok=True)

        redis_cache = '''"""Redis Cache for AutoPR"""
import redis.asyncio as redis
import pickle
import os
from typing import Any, Optional

class RedisCache:
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self._redis: Optional[redis.Redis] = None

    async def connect(self):
        if not self._redis:
            self._redis = redis.from_url(self.redis_url, decode_responses=False)

    async def get(self, key: str) -> Optional[Any]:
        await self.connect()
        try:
            value = await self._redis.get(key)
            return pickle.loads(value) if value else None
        except Exception:
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        await self.connect()
        try:
            await self._redis.set(key, pickle.dumps(value), ex=ttl)
        except Exception:
            pass

cache = RedisCache()
'''

        await self._write_file(str(caching_dir / "redis_cache.py"), redis_cache)
        await self._write_file(
            str(caching_dir / "__init__.py"), "from .redis_cache import cache"
        )
        await self._add_requirement("redis>=4.6.0")

        execution.logs.append("✅ Redis caching setup complete")
        return execution

    async def _create_health_checks(self, execution: TaskExecution) -> TaskExecution:
        """Create health check endpoints"""
        execution.logs.append("Creating health checks...")

        health_dir = self.project_root / "autopr" / "health"
        health_dir.mkdir(parents=True, exist_ok=True)

        health_checks = '''"""Health Checks for AutoPR"""
try:
    import psutil  # type: ignore[import-not-found]
except Exception:
    psutil = None  # type: ignore[assignment]
import time
from typing import Dict, Any

class HealthChecker:
    def __init__(self):
        self.start_time = time.time()

    async def get_health_status(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "uptime_seconds": time.time() - self.start_time,
            "cpu_usage": psutil.cpu_percent() if psutil else 0.0,
            "memory_usage": psutil.virtual_memory().percent if psutil else 0.0
        }

    async def is_healthy(self) -> bool:
        try:
            status = await self.get_health_status()
            return status["cpu_usage"] < 90 and status["memory_usage"] < 90
        except Exception:
            return False

health_checker = HealthChecker()
'''

        await self._write_file(str(health_dir / "health_checks.py"), health_checks)
        await self._write_file(
            str(health_dir / "__init__.py"), "from .health_checks import health_checker"
        )
        await self._add_requirement("psutil>=5.9.0")

        execution.logs.append("✅ Health checks created")
        return execution

    async def _implement_basic_circuit_breakers(
        self, execution: TaskExecution
    ) -> TaskExecution:
        """Implement circuit breaker pattern"""
        execution.logs.append("Implementing circuit breakers...")

        resilience_dir = self.project_root / "autopr" / "resilience"
        resilience_dir.mkdir(parents=True, exist_ok=True)

        circuit_breaker = '''"""Circuit Breaker for AutoPR"""
import asyncio
import time
from enum import Enum
from typing import Any, Callable

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception(f"Circuit breaker {self.name} is OPEN")

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise e

    async def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    async def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
'''

        await self._write_file(
            str(resilience_dir / "circuit_breaker.py"), circuit_breaker
        )
        await self._write_file(
            str(resilience_dir / "__init__.py"),
            "from .circuit_breaker import CircuitBreaker",
        )
        await self._add_requirement("tenacity>=8.2.0")

        execution.logs.append("✅ Circuit breakers implemented")
        return execution

    async def _create_placeholder_implementation(
        self, task: Task, execution: TaskExecution
    ) -> TaskExecution:
        """Create placeholder implementation for tasks not yet fully implemented"""
        execution.logs.append(f"Creating placeholder for {task.name}...")

        # Create basic directory structure
        if task.files_created:
            for file_path in task.files_created:
                if file_path.endswith("/"):
                    # It's a directory
                    dir_path = self.project_root / file_path
                    dir_path.mkdir(parents=True, exist_ok=True)
                else:
                    # It's a file
                    full_path = self.project_root / file_path
                    full_path.parent.mkdir(parents=True, exist_ok=True)

                    if not full_path.exists():
                        placeholder_content = (
                            f'"""\n{task.description}\n'
                            f'TODO: Implement {task.name}\n"""\n\n'
                            "# Placeholder implementation\npass\n"
                        )
                        await self._write_file(str(full_path), placeholder_content)

        # Add requirements
        for requirement in task.packages_required:
            await self._add_requirement(requirement)

        execution.logs.append(f"✅ Placeholder for {task.name} created")
        return execution

    # Helper methods

    async def _write_file(self, file_path: str, content: str) -> None:
        """Write content to file, creating directories as needed"""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    async def _add_requirement(self, requirement: str) -> None:
        """Add requirement to requirements.txt"""
        requirements_file = self.project_root / "requirements.txt"

        # Read existing requirements
        existing_requirements = set()
        if requirements_file.exists():
            with open(requirements_file, encoding="utf-8") as f:
                existing_requirements = {
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith("#")
                }

        # Add new requirement if not already present
        req_name = requirement.split(">=")[0].split("==")[0].split("[")[0]
        if not any(req_name in existing for existing in existing_requirements):
            with open(requirements_file, "a", encoding="utf-8") as f:
                f.write(f"{requirement}\n")

    def get_execution_summary(self) -> dict[str, Any]:
        """Get summary of all task executions"""
        total_tasks = len(self.executions)
        successful_tasks = sum(
            1 for exec in self.executions.values() if exec.status == "success"
        )
        failed_tasks = sum(
            1 for exec in self.executions.values() if exec.status == "error"
        )

        return {
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0,
            "executions": {
                name: {
                    "status": exec.status,
                    "duration": exec.duration,
                    "error": exec.error_message,
                }
                for name, exec in self.executions.items()
            },
        }
