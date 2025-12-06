"""
AutoPR Dashboard Package

Web-based UI for monitoring and configuring AutoPR Engine.
"""

from autopr.dashboard.router import (
    DashboardState,
    RateLimiter,
    StatusResponse,
    MetricsResponse,
    QualityCheckRequest,
    QualityCheckResponse,
    ConfigRequest,
    ConfigResponse,
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
    "QualityCheckResponse",
    "ConfigResponse",
    # Request models
    "QualityCheckRequest",
    "ConfigRequest",
    # Version
    "__version__",
]

__author__ = "AutoPR Team"
__description__ = "Web-based dashboard for AutoPR Engine"
