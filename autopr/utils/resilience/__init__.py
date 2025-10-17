"""
Resilience utilities for AutoPR Engine.

Provides circuit breaker pattern and other resilience mechanisms.
"""

from autopr.utils.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitBreakerState,
)

__all__ = ["CircuitBreaker", "CircuitBreakerError", "CircuitBreakerState"]
