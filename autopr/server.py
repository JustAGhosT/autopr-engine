"""AutoPR Server with GitHub App Integration.

FastAPI server that can run alongside or replace the Flask dashboard.
"""

import logging
import os
import sys
from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from autopr.health.health_checker import HealthChecker

logger = logging.getLogger(__name__)

# Required environment variables for dashboard functionality
REQUIRED_ENV_VARS = {
    "GITHUB_CLIENT_ID": "GitHub OAuth client ID for dashboard login",
    "GITHUB_CLIENT_SECRET": "GitHub OAuth client secret",
}

# Optional but recommended environment variables
RECOMMENDED_ENV_VARS = {
    "ENVIRONMENT": "Deployment environment (development/production)",
    "CORS_ALLOWED_ORIGINS": "Comma-separated list of allowed CORS origins",
}


def validate_environment() -> dict[str, list[str]]:
    """Validate required and recommended environment variables.

    Returns:
        Dict with 'missing' and 'warnings' lists.
    """
    result = {"missing": [], "warnings": []}

    for var, description in REQUIRED_ENV_VARS.items():
        if not os.getenv(var):
            result["missing"].append(f"{var}: {description}")

    for var, description in RECOMMENDED_ENV_VARS.items():
        if not os.getenv(var):
            result["warnings"].append(f"{var}: {description}")

    return result

# Import Dashboard API router
try:
    from autopr.api import api_router
    DASHBOARD_API_AVAILABLE = True
except ImportError:
    DASHBOARD_API_AVAILABLE = False

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

# Dashboard static files directory
DASHBOARD_DIR = Path(__file__).parent.parent / "dashboard" / "dist"


def create_app(skip_env_validation: bool = False) -> FastAPI:
    """Create FastAPI application with GitHub App integration.

    Args:
        skip_env_validation: If True, skip environment variable validation.

    Returns:
        Configured FastAPI application
    """
    # Validate environment on startup
    if not skip_env_validation:
        env_status = validate_environment()

        if env_status["warnings"]:
            for warning in env_status["warnings"]:
                logger.warning(f"Missing recommended env var: {warning}")

        if env_status["missing"]:
            logger.warning(
                "Missing required environment variables for full dashboard functionality:\n"
                + "\n".join(f"  - {m}" for m in env_status["missing"])
            )

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

    # Add CSRF protection middleware for API routes
    if DASHBOARD_API_AVAILABLE:
        from autopr.api.deps import verify_csrf

        class CSRFMiddleware(BaseHTTPMiddleware):
            """Middleware to verify CSRF protection on mutation requests."""

            async def dispatch(self, request: Request, call_next):
                # Only check CSRF for API routes
                if request.url.path.startswith("/api/"):
                    await verify_csrf(request)
                return await call_next(request)

        app.add_middleware(CSRFMiddleware)

    # Add caching headers middleware
    class CacheHeadersMiddleware(BaseHTTPMiddleware):
        """Middleware to add appropriate Cache-Control headers."""

        async def dispatch(self, request: Request, call_next):
            response = await call_next(request)

            # Skip if response already has Cache-Control
            if "cache-control" in response.headers:
                return response

            # Add caching headers based on route and method
            if request.method == "GET":
                if request.url.path.startswith("/api/"):
                    # API responses: private, must revalidate for fresh data
                    response.headers["Cache-Control"] = "private, no-cache, must-revalidate"
                elif request.url.path.startswith("/assets/"):
                    # Static assets: long cache with immutable
                    response.headers["Cache-Control"] = "public, max-age=31536000, immutable"

            return response

    app.add_middleware(CacheHeadersMiddleware)

    # Include Dashboard API routes if available
    if DASHBOARD_API_AVAILABLE:
        app.include_router(api_router)

    # Include GitHub App routes if available
    if GITHUB_APP_AVAILABLE:
        app.include_router(install_router)
        app.include_router(callback_router)
        app.include_router(webhook_router)
        app.include_router(setup_router)

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

    # Serve dashboard static files if available
    if DASHBOARD_DIR.exists():
        # Mount static assets
        assets_dir = DASHBOARD_DIR / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(request: Request, full_path: str):
            """Serve the React SPA for all non-API routes."""
            # Don't serve SPA for API routes
            if full_path.startswith("api/"):
                return Response(status_code=404)

            # Try to serve static file first
            file_path = DASHBOARD_DIR / full_path
            if file_path.is_file():
                return FileResponse(file_path)

            # Otherwise serve index.html for SPA routing
            index_path = DASHBOARD_DIR / "index.html"
            if index_path.exists():
                return FileResponse(index_path)

            return Response(status_code=404)
    else:
        # Fallback API response when dashboard not built
        @app.get("/")
        async def root():
            """Root endpoint."""
            return {
                "message": "AutoPR Engine API",
                "dashboard": "not built (run: cd dashboard && npm run build)",
                "api_available": DASHBOARD_API_AVAILABLE,
                "github_app": "available" if GITHUB_APP_AVAILABLE else "not configured",
            }

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

