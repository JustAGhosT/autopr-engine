"""AutoPR Dashboard API

RESTful API for the AutoPR Dashboard frontend.
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .repos import router as repos_router
from .bots import router as bots_router
from .workflows import router as workflows_router
from .dashboard import router as dashboard_router
from .settings import router as settings_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(repos_router, prefix="/repos", tags=["repos"])
api_router.include_router(bots_router, prefix="/bots", tags=["bots"])
api_router.include_router(workflows_router, prefix="/workflows", tags=["workflows"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])

__all__ = ["api_router"]
