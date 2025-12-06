"""
AutoPR Dashboard Package

Web-based UI for monitoring and configuring AutoPR Engine.

Storage Backends:
    Configure via environment variables:
    - AUTOPR_STORAGE_BACKEND: "memory" (default) or "redis"
    - REDIS_URL: Redis connection URL (required if backend is "redis")
"""

from autopr.dashboard.router import (
    DashboardState,
    RateLimiter,
    StatusResponse,
    MetricsResponse,
    ActivityRecord,
    QualityCheckRequest,
    QualityCheckResponse,
    ConfigRequest,
    ConfigResponse,
    SuccessResponse,
    router,
    dashboard_state,
    __version__,
)

from autopr.dashboard.storage import (
    StorageBackend,
    InMemoryStorage,
    RedisStorage,
    get_storage,
    get_storage_backend,
)

__all__ = [
    # Router and state
    "router",
    "dashboard_state",
    # Classes
    "DashboardState",
    "RateLimiter",
    # Storage
    "StorageBackend",
    "InMemoryStorage",
    "RedisStorage",
    "get_storage",
    "get_storage_backend",
    # Response models
    "StatusResponse",
    "MetricsResponse",
    "ActivityRecord",
    "QualityCheckResponse",
    "ConfigResponse",
    "SuccessResponse",
    # Request models
    "QualityCheckRequest",
    "ConfigRequest",
    # Version
    "__version__",
]

__author__ = "AutoPR Team"
__description__ = "Web-based dashboard for AutoPR Engine"
