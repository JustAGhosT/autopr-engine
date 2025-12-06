"""AutoPR Server with GitHub App Integration.

FastAPI server that can run alongside or replace the Flask dashboard.
"""

import os
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

from autopr.health.health_checker import HealthChecker

# Import GitHub App routers
try:
    from autopr.integrations.github_app import (
        install_router,
        callback_router,
        webhook_router,
        setup_router,
    )
    GITHUB_APP_AVAILABLE = True
except ImportError:
    GITHUB_APP_AVAILABLE = False


def create_app() -> FastAPI:
    """Create FastAPI application with GitHub App integration.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="AutoPR Engine",
        description="AI-Powered GitHub PR Automation and Issue Management",
        version="1.0.1",
    )

    # CORS middleware - restrict origins in production
    cors_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
    if cors_origins_env:
        # Parse comma-separated list of allowed origins
        cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
    else:
        # Development fallback: allow all origins only when env var not set
        cors_origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include GitHub App routes if available
    if GITHUB_APP_AVAILABLE:
        app.include_router(install_router)
        app.include_router(callback_router)
        app.include_router(webhook_router)
        app.include_router(setup_router)

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "AutoPR Engine API",
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

    # Initialize health checker (without engine for standalone mode)
    health_checker = HealthChecker()

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
            return await health_checker.check_all(use_cache=True)
        return await health_checker.check_quick()

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

