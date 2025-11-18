"""
Circuit Breaker Pattern Implementation

Implements the circuit breaker pattern to prevent repeated calls to failing services.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation, requests allowed
    OPEN = "open"      # Failures detected, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and prevents operation."""
    pass


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Number of failures before opening
    success_threshold: int = 2  # Number of successes to close from half-open
    timeout: float = 60.0  # Seconds to wait before moving to half-open
    half_open_timeout: float = 30.0  # Seconds to wait in half-open before re-opening


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker."""
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float | None = None
    last_success_time: float | None = None
    total_calls: int = 0
    total_failures: int = 0
    total_successes: int = 0
    state_transitions: dict[str, int] = field(default_factory=lambda: {
        "closed_to_open": 0,
        "open_to_half_open": 0,
        "half_open_to_closed": 0,
        "half_open_to_open": 0,
    })


class CircuitBreaker:
    """
    Circuit breaker implementation for protecting services from repeated failures.
    
    The circuit breaker has three states:
    - CLOSED: Normal operation, requests are allowed through
    - OPEN: Too many failures, requests are blocked
    - HALF_OPEN: Testing if the service has recovered
    
    Example:
        >>> cb = CircuitBreaker(name="my_service", failure_threshold=3, timeout=60)
        >>> async with cb:
        >>>     result = await my_service_call()
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 60.0,
        half_open_timeout: float = 30.0,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Name of the circuit breaker (for logging)
            failure_threshold: Number of consecutive failures before opening
            success_threshold: Number of consecutive successes to close from half-open
            timeout: Seconds to wait before moving from open to half-open
            half_open_timeout: Seconds to wait in half-open before re-opening
        """
        self.name = name
        self.config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            timeout=timeout,
            half_open_timeout=half_open_timeout,
        )
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()
        
        logger.info(
            "Circuit breaker '%s' initialized with failure_threshold=%d, timeout=%.1fs",
            name, failure_threshold, timeout
        )
    
    async def __aenter__(self):
        """Context manager entry - check if request should be allowed."""
        await self._check_and_update_state()
        
        if self.stats.state == CircuitBreakerState.OPEN:
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is OPEN, blocking request"
            )
        
        self.stats.total_calls += 1
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - record success or failure."""
        if exc_type is None:
            # Success
            await self._record_success()
        else:
            # Failure
            await self._record_failure()
        
        return False  # Don't suppress exceptions
    
    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute a function with circuit breaker protection.
        
        Args:
            func: Async function to call
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function call
            
        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
            Exception: Any exception raised by the function
        """
        async with self:
            return await func(*args, **kwargs)
    
    async def _check_and_update_state(self) -> None:
        """Check if state should be updated based on time elapsed."""
        async with self._lock:
            current_time = time.time()
            
            if self.stats.state == CircuitBreakerState.OPEN:
                # Check if timeout has elapsed
                if self.stats.last_failure_time is not None:
                    elapsed = current_time - self.stats.last_failure_time
                    if elapsed >= self.config.timeout:
                        self._transition_to_half_open()
            
            elif self.stats.state == CircuitBreakerState.HALF_OPEN:
                # Check if half-open timeout has elapsed without success
                if self.stats.last_failure_time is not None:
                    elapsed = current_time - self.stats.last_failure_time
                    if elapsed >= self.config.half_open_timeout:
                        self._transition_to_open()
    
    async def _record_success(self) -> None:
        """Record a successful operation."""
        async with self._lock:
            self.stats.success_count += 1
            self.stats.total_successes += 1
            self.stats.last_success_time = time.time()
            
            if self.stats.state == CircuitBreakerState.HALF_OPEN:
                if self.stats.success_count >= self.config.success_threshold:
                    self._transition_to_closed()
            elif self.stats.state == CircuitBreakerState.CLOSED:
                # Reset failure count on success
                self.stats.failure_count = 0
    
    async def _record_failure(self) -> None:
        """Record a failed operation."""
        async with self._lock:
            self.stats.failure_count += 1
            self.stats.total_failures += 1
            self.stats.last_failure_time = time.time()
            
            if self.stats.state == CircuitBreakerState.CLOSED:
                if self.stats.failure_count >= self.config.failure_threshold:
                    self._transition_to_open()
            elif self.stats.state == CircuitBreakerState.HALF_OPEN:
                # Single failure in half-open should re-open the circuit
                self._transition_to_open()
    
    def _transition_to_open(self) -> None:
        """Transition to OPEN state."""
        old_state = self.stats.state
        self.stats.state = CircuitBreakerState.OPEN
        self.stats.success_count = 0
        
        if old_state == CircuitBreakerState.CLOSED:
            self.stats.state_transitions["closed_to_open"] += 1
        elif old_state == CircuitBreakerState.HALF_OPEN:
            self.stats.state_transitions["half_open_to_open"] += 1
        
        logger.warning(
            "Circuit breaker '%s' transitioned from %s to OPEN after %d failures",
            self.name, old_state.value, self.stats.failure_count
        )
    
    def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state."""
        self.stats.state = CircuitBreakerState.HALF_OPEN
        self.stats.failure_count = 0
        self.stats.success_count = 0
        self.stats.state_transitions["open_to_half_open"] += 1
        
        logger.info(
            "Circuit breaker '%s' transitioned to HALF_OPEN, testing service recovery",
            self.name
        )
    
    def _transition_to_closed(self) -> None:
        """Transition to CLOSED state."""
        self.stats.state = CircuitBreakerState.CLOSED
        self.stats.failure_count = 0
        self.stats.success_count = 0
        self.stats.state_transitions["half_open_to_closed"] += 1
        
        logger.info(
            "Circuit breaker '%s' transitioned to CLOSED, service recovered",
            self.name
        )
    
    def get_state(self) -> CircuitBreakerState:
        """Get current state of the circuit breaker."""
        return self.stats.state
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics for the circuit breaker.
        
        Returns:
            Dictionary containing circuit breaker statistics
        """
        return {
            "name": self.name,
            "state": self.stats.state.value,
            "failure_count": self.stats.failure_count,
            "success_count": self.stats.success_count,
            "total_calls": self.stats.total_calls,
            "total_failures": self.stats.total_failures,
            "total_successes": self.stats.total_successes,
            "failure_rate": (
                self.stats.total_failures / self.stats.total_calls
                if self.stats.total_calls > 0 else 0.0
            ),
            "last_failure_time": self.stats.last_failure_time,
            "last_success_time": self.stats.last_success_time,
            "state_transitions": self.stats.state_transitions.copy(),
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout,
                "half_open_timeout": self.config.half_open_timeout,
            },
        }
    
    async def reset(self) -> None:
        """Reset the circuit breaker to CLOSED state with cleared stats."""
        async with self._lock:
            self.stats = CircuitBreakerStats()
            logger.info("Circuit breaker '%s' reset to CLOSED state", self.name)
    
    def is_available(self) -> bool:
        """Check if the circuit breaker allows requests."""
        return self.stats.state != CircuitBreakerState.OPEN
