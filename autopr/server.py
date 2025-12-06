"""AutoPR Server with GitHub App Integration and Dashboard.

FastAPI server that provides the AutoPR Engine API and dashboard UI.
"""

import logging
import os
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

from autopr.health.health_checker import HealthChecker

# Set up logging
logger = logging.getLogger(__name__)

# Import dashboard router and version
try:
    from autopr.dashboard.router import router as dashboard_router
    from autopr.dashboard.router import __version__ as DASHBOARD_VERSION
    DASHBOARD_AVAILABLE = True
    logger.info("Dashboard module loaded successfully")
except ImportError as e:
    DASHBOARD_AVAILABLE = False
    DASHBOARD_VERSION = "1.0.1"
    logger.warning(f"Dashboard module not available: {e}")

# Import GitHub App routers
try:
    from autopr.integrations.github_app import (
        install_router,
        callback_router,
        webhook_router,
        setup_router,
    )
    GITHUB_APP_AVAILABLE = True
    logger.info("GitHub App integration loaded successfully")
except ImportError as e:
    GITHUB_APP_AVAILABLE = False
    logger.warning(f"GitHub App integration not available: {e}")

# Use dashboard version as server version for consistency
__version__ = DASHBOARD_VERSION

# Shared health checker instance
_health_checker: HealthChecker | None = None


def get_health_checker() -> HealthChecker:
    """Get or create the shared HealthChecker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


def create_app() -> FastAPI:
    """Create FastAPI application with GitHub App integration.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="AutoPR Engine",
        description="AI-Powered GitHub PR Automation and Issue Management",
        version=__version__,
    )

    # CORS middleware - restrict origins in production
    cors_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
    if cors_origins_env:
        # Parse comma-separated list of allowed origins
        cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
        allow_credentials = True  # Safe with specific origins
    else:
        # Development fallback: allow all origins only when env var not set
        # Note: credentials cannot be used with wildcard origin per CORS spec
        cors_origins = ["*"]
        allow_credentials = False

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include dashboard routes if available (must be first to handle "/" route)
    if DASHBOARD_AVAILABLE:
        app.include_router(dashboard_router)
    else:
        # Fallback root route when dashboard is not available
        @app.get("/")
        async def root_fallback():
            """Root endpoint when dashboard is not available."""
            return {
                "message": "AutoPR Engine API",
                "version": __version__,
                "dashboard": "not available (import failed)",
                "api_docs": "/docs",
                "health": "/health",
                "github_app": "available" if GITHUB_APP_AVAILABLE else "not configured",
            }

    # Include GitHub App routes if available
    if GITHUB_APP_AVAILABLE:
        app.include_router(install_router)
        app.include_router(callback_router)
        app.include_router(webhook_router)
        app.include_router(setup_router)

    # API info endpoint (when dashboard is not available or for API consumers)
    @app.get("/api")
    async def api_root():
        """API root endpoint."""
        return {
            "message": "AutoPR Engine API",
            "version": __version__,
            "dashboard": "available" if DASHBOARD_AVAILABLE else "not configured",
            "github_app": "available" if GITHUB_APP_AVAILABLE else "not configured",
        }

    @app.get("/favicon.ico")
    async def favicon():
        """Serve favicon - returns empty response to prevent slow 404 lookups."""
        # Check for favicon in common locations
        favicon_paths = [
            Path(__file__).parent.parent / "website" / "app" / "favicon.ico",
            Path(__file__).parent / "static" / "favicon.ico",
        ]
        for favicon_path in favicon_paths:
            if favicon_path.exists():
                return FileResponse(
                    favicon_path,
                    media_type="image/x-icon",
                    headers={"Cache-Control": "public, max-age=86400"},
                )
        # Return empty response with no-content status
        return Response(status_code=204)

    # Get shared health checker
    health_checker = get_health_checker()

    @app.get("/health")
    async def health(detailed: bool = Query(False, description="Return detailed health info")):
        """
        Health check endpoint.

        Args:
            detailed: If True, perform comprehensive health check with all components.
                     If False (default), perform quick check for low latency.

        Returns:
            Health status response with status and optional component details.
        """
        if detailed:
            result = await health_checker.check_all(use_cache=True)
        else:
            result = await health_checker.check_quick()

        # Add version info for consistency
        result["version"] = __version__
        return result

    return app


def main():
    """Run the server."""
    import uvicorn

    app = create_app()
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
