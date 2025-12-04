"""AutoPR Server with GitHub App Integration.

FastAPI server that can run alongside or replace the Flask dashboard.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "healthy"}

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

