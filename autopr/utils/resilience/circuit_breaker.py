"""
Circuit Breaker pattern implementation for AutoPR Engine.

Prevents repeated calls to failing services and provides graceful degradation.
"""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from enum import Enum
import logging
from typing import Any


logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, calls are blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""

    pass


class CircuitBreaker:
    """
    Circuit breaker implementation to prevent cascading failures.

    The circuit breaker monitors failures and:
    - Remains CLOSED during normal operation
    - Opens after failure_threshold consecutive failures
    - After timeout_seconds, transitions to HALF_OPEN to test recovery
    - Closes again if test call succeeds, or reopens if it fails
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        success_threshold: int = 2,
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Circuit breaker identifier
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: Seconds to wait before attempting recovery
            success_threshold: Successful calls needed to close circuit from half-open
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.success_threshold = success_threshold

        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: datetime | None = None
        self.last_state_change = datetime.now(tz=UTC)

        self._lock = asyncio.Lock()

        logger.info(
            f"Circuit breaker '{name}' initialized: "
            f"failure_threshold={failure_threshold}, timeout={timeout_seconds}s"
        )

    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from func

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Original exception from func
        """
        async with self._lock:
            # Check if we should attempt the call
            if self.state == CircuitBreakerState.OPEN:
                # Check if timeout has elapsed
                if self.last_failure_time and datetime.now(tz=UTC) - self.last_failure_time > self.timeout:
                    self._transition_to(CircuitBreakerState.HALF_OPEN)
                    logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state")
                else:
                    raise CircuitBreakerError(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Service is temporarily unavailable."
                    )

        # Attempt the call
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            await self._on_success()
            return result

        except Exception as e:
            await self._on_failure(e)
            raise

    async def _on_success(self) -> None:
        """Handle successful call."""
        async with self._lock:
            self.failure_count = 0

            if self.state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    self._transition_to(CircuitBreakerState.CLOSED)
                    logger.info(
                        f"Circuit breaker '{self.name}' closed after "
                        f"{self.success_count} successful calls"
                    )
                    self.success_count = 0

    async def _on_failure(self, exception: Exception) -> None:
        """Handle failed call."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now(tz=UTC)
            self.success_count = 0

            logger.warning(
                f"Circuit breaker '{self.name}' recorded failure {self.failure_count}/"
                f"{self.failure_threshold}: {exception}"
            )

            if self.state == CircuitBreakerState.HALF_OPEN:
                # Immediately reopen on failure in half-open state
                self._transition_to(CircuitBreakerState.OPEN)
                logger.warning(f"Circuit breaker '{self.name}' reopened after test failure")

            elif self.failure_count >= self.failure_threshold:
                # Open circuit after threshold reached
                self._transition_to(CircuitBreakerState.OPEN)
                logger.error(
                    f"Circuit breaker '{self.name}' OPENED after "
                    f"{self.failure_count} consecutive failures"
                )

    def _transition_to(self, new_state: CircuitBreakerState) -> None:
        """
        Transition to new state.

        Args:
            new_state: New circuit breaker state
        """
        old_state = self.state
        self.state = new_state
        self.last_state_change = datetime.now(tz=UTC)

        if old_state != new_state:
            logger.info(
                f"Circuit breaker '{self.name}' transitioned from "
                f"{old_state.value} to {new_state.value}"
            )

    def get_status(self) -> dict[str, Any]:
        """
        Get current circuit breaker status.

        Returns:
            Dictionary with current state and metrics
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat()
            if self.last_failure_time
            else None,
            "last_state_change": self.last_state_change.isoformat(),
            "configuration": {
                "failure_threshold": self.failure_threshold,
                "timeout_seconds": self.timeout.total_seconds(),
                "success_threshold": self.success_threshold,
            },
        }

    async def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        async with self._lock:
            self._transition_to(CircuitBreakerState.CLOSED)
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None
            logger.info(f"Circuit breaker '{self.name}' manually reset")
