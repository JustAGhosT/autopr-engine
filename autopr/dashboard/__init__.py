"""
AutoPR Dashboard Package

Web-based UI for monitoring and configuring AutoPR Engine.
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

__all__ = [
    # Router and state
    "router",
    "dashboard_state",
    # Classes
    "DashboardState",
    "RateLimiter",
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
