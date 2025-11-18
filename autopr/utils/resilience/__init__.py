"""
Resilience Utilities Package

Utilities for building resilient systems including circuit breakers,
retry logic, and failure handling.
"""

from autopr.utils.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitBreakerState,
)

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "CircuitBreakerState",
]
