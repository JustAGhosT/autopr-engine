"""
Rate Limiting Middleware for AutoPR Engine

Implements request rate limiting to protect against DoS attacks and API abuse.
Supports multiple backends (in-memory, Redis) and tiered rate limits.
"""

import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Callable, Optional
from functools import wraps

# Lazy logger initialization to handle both structlog and standard logging
_logger = None

def _get_logger():
    """Get logger instance with fallback."""
    global _logger
    if _logger is None:
        try:
            import structlog
            _logger = structlog.get_logger(__name__)
            # Test that logger works
            _logger.info  # Access method to ensure it's callable
        except (ImportError, TypeError, AttributeError, Exception):
            # Fallback to standard logging if structlog is not available or not configured
            import logging
            _logger = logging.getLogger(__name__)
    return _logger


class RateLimiter:
    """
    Rate limiter with sliding window algorithm.
    
    Supports:
    - Per-user rate limiting
    - Per-IP rate limiting
    - Tiered limits (anonymous, authenticated, premium)
    - Multiple time windows (per minute, per hour, per day)
    """
    
    def __init__(self, default_limit: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            default_limit: Default requests per window
            window_seconds: Time window in seconds
        """
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        
        # In-memory storage: {key: [(timestamp, count), ...]}
        self._requests: dict[str, list[tuple[float, int]]] = defaultdict(list)
        
        # Tiered limits (requests per minute)
        self.tier_limits = {
            "anonymous": 10,      # Unauthenticated users
            "authenticated": 100,  # Logged in users
            "premium": 1000,       # Premium/paid users
            "admin": 10000,        # Admin users (effectively unlimited)
        }
        
    def _clean_old_requests(self, key: str, now: float) -> None:
        """Remove requests outside the time window."""
        cutoff = now - self.window_seconds
        self._requests[key] = [
            (ts, count) for ts, count in self._requests[key]
            if ts > cutoff
        ]
    
    def _get_request_count(self, key: str, now: float) -> int:
        """Get current request count for key."""
        self._clean_old_requests(key, now)
        return sum(count for _, count in self._requests[key])
    
    def is_allowed(
        self,
        key: str,
        limit: Optional[int] = None,
        tier: Optional[str] = None
    ) -> tuple[bool, dict[str, any]]:
        """
        Check if request is allowed.
        
        Args:
            key: Rate limit key (e.g., user ID, IP address)
            limit: Custom limit (overrides default and tier)
            tier: User tier for tiered limits
            
        Returns:
            Tuple of (allowed, info_dict)
            info_dict contains: remaining, reset_time, limit
        """
        now = time.time()
        
        # Determine limit
        if limit is not None:
            effective_limit = limit
        elif tier and tier in self.tier_limits:
            effective_limit = self.tier_limits[tier]
        else:
            effective_limit = self.default_limit
        
        # Get current count
        current_count = self._get_request_count(key, now)
        
        # Check if allowed
        allowed = current_count < effective_limit
        
        if allowed:
            # Add this request
            self._requests[key].append((now, 1))
        
        # Calculate reset time
        oldest_request = self._requests[key][0][0] if self._requests[key] else now
        reset_time = oldest_request + self.window_seconds
        
        info = {
            "limit": effective_limit,
            "remaining": max(0, effective_limit - current_count - (1 if allowed else 0)),
            "reset": int(reset_time),
            "retry_after": int(reset_time - now) if not allowed else 0,
        }
        
        _get_logger().info(
            "Rate limit check",
            key=key,
            allowed=allowed,
            current_count=current_count,
            limit=effective_limit,
            **info
        )
        
        return allowed, info
    
    def reset(self, key: str) -> None:
        """Reset rate limit for a key (admin function)."""
        if key in self._requests:
            del self._requests[key]
            _get_logger().info("Rate limit reset", key=key)


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def rate_limit(
    limit: int = 100,
    window: int = 60,
    key_func: Optional[Callable] = None,
    tier_func: Optional[Callable] = None
):
    """
    Decorator for rate limiting functions/endpoints.
    
    Args:
        limit: Requests per window
        window: Time window in seconds
        key_func: Function to extract rate limit key from args
        tier_func: Function to extract user tier from args
        
    Example:
        @rate_limit(limit=10, window=60)
        async def api_endpoint(request):
            pass
            
        @rate_limit(limit=100, key_func=lambda r: r.user.id)
        async def user_endpoint(request):
            pass
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            limiter = get_rate_limiter()
            
            # Extract key (default to first arg if available)
            if key_func:
                key = key_func(*args, **kwargs)
            elif args:
                # Try to get IP or user ID from request-like first arg
                request = args[0]
                key = getattr(request, "client", {}).get("host", "default")
            else:
                key = "default"
            
            # Extract tier if provided
            tier = tier_func(*args, **kwargs) if tier_func else None
            
            # Check rate limit
            allowed, info = limiter.is_allowed(key, limit=limit, tier=tier)
            
            if not allowed:
                # Rate limit exceeded
                _get_logger().warning(
                    "Rate limit exceeded",
                    key=key,
                    limit=limit,
                    **info
                )
                # For FastAPI/Flask, you'd raise an exception here
                # For now, we'll just log and continue
                raise Exception(f"Rate limit exceeded. Retry after {info['retry_after']} seconds")
            
            # Add rate limit headers to response if possible
            result = await func(*args, **kwargs)
            
            # Try to add headers if result is response-like
            if hasattr(result, "headers"):
                result.headers["X-RateLimit-Limit"] = str(info["limit"])
                result.headers["X-RateLimit-Remaining"] = str(info["remaining"])
                result.headers["X-RateLimit-Reset"] = str(info["reset"])
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            limiter = get_rate_limiter()
            
            # Extract key
            if key_func:
                key = key_func(*args, **kwargs)
            elif args:
                request = args[0]
                key = getattr(request, "remote_addr", "default")
            else:
                key = "default"
            
            # Extract tier
            tier = tier_func(*args, **kwargs) if tier_func else None
            
            # Check rate limit
            allowed, info = limiter.is_allowed(key, limit=limit, tier=tier)
            
            if not allowed:
                _get_logger().warning(
                    "Rate limit exceeded",
                    key=key,
                    limit=limit,
                    **info
                )
                raise Exception(f"Rate limit exceeded. Retry after {info['retry_after']} seconds")
            
            result = func(*args, **kwargs)
            
            # Try to add headers
            if hasattr(result, "headers"):
                result.headers["X-RateLimit-Limit"] = str(info["limit"])
                result.headers["X-RateLimit-Remaining"] = str(info["remaining"])
                result.headers["X-RateLimit-Reset"] = str(info["reset"])
            
            return result
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class RedisRateLimiter(RateLimiter):
    """
    Redis-backed rate limiter for distributed systems.
    
    TODO: PRODUCTION
    - Implement Redis storage backend
    - Add Redis connection pooling
    - Handle Redis connection failures gracefully
    - Add metrics for rate limit hits/misses
    """
    
    def __init__(self, redis_url: str, **kwargs):
        super().__init__(**kwargs)
        self.redis_url = redis_url
        # TODO: Initialize Redis connection
        _get_logger().warning("RedisRateLimiter not fully implemented, falling back to in-memory")


# Flask middleware for rate limiting
class FlaskRateLimitMiddleware:
    """
    Flask middleware for automatic rate limiting.
    
    Usage:
        app = Flask(__name__)
        FlaskRateLimitMiddleware(app, limit=100, window=60)
    """
    
    def __init__(self, app, limit: int = 100, window: int = 60):
        self.app = app
        self.limiter = RateLimiter(default_limit=limit, window_seconds=window)
        
        @app.before_request
        def check_rate_limit():
            from flask import request, jsonify
            
            # Get client IP
            key = request.remote_addr or "unknown"
            
            # Check rate limit
            allowed, info = self.limiter.is_allowed(key)
            
            if not allowed:
                response = jsonify({
                    "error": "Rate limit exceeded",
                    "limit": info["limit"],
                    "retry_after": info["retry_after"]
                })
                response.status_code = 429
                response.headers["X-RateLimit-Limit"] = str(info["limit"])
                response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
                response.headers["X-RateLimit-Reset"] = str(info["reset"])
                response.headers["Retry-After"] = str(info["retry_after"])
                return response


# FastAPI middleware for rate limiting
class FastAPIRateLimitMiddleware:
    """
    FastAPI middleware for automatic rate limiting.
    
    Usage:
        app = FastAPI()
        app.add_middleware(FastAPIRateLimitMiddleware, limit=100, window=60)
    """
    
    def __init__(self, app, limit: int = 100, window: int = 60):
        self.limiter = RateLimiter(default_limit=limit, window_seconds=window)
        
        @app.middleware("http")
        async def rate_limit_middleware(request, call_next):
            from fastapi import Response
            from fastapi.responses import JSONResponse
            
            # Get client IP
            key = request.client.host if request.client else "unknown"
            
            # Check rate limit
            allowed, info = self.limiter.is_allowed(key)
            
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "limit": info["limit"],
                        "retry_after": info["retry_after"]
                    },
                    headers={
                        "X-RateLimit-Limit": str(info["limit"]),
                        "X-RateLimit-Remaining": str(info["remaining"]),
                        "X-RateLimit-Reset": str(info["reset"]),
                        "Retry-After": str(info["retry_after"])
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(info["reset"])
            
            return response
