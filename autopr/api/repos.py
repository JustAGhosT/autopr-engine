"""Repository API Routes

Repository management endpoints.
"""

from datetime import datetime
from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from .deps import get_current_user, SessionData
from .models import ApiResponse, RepositoryResponse, RepositoryUpdate, PaginationMeta

router = APIRouter()

# Mock repository storage (in production, use database)
_repositories: dict[str, dict] = {}


def _get_user_repos(user_id: str, page: int = 1, per_page: int = 20) -> tuple[List[dict], int]:
    """Get repositories for a user with pagination."""
    user_repos = [r for r in _repositories.values() if r.get("user_id") == user_id]
    total = len(user_repos)
    start = (page - 1) * per_page
    end = start + per_page
    return user_repos[start:end], total


@router.get("", response_model=ApiResponse[List[RepositoryResponse]])
async def list_repositories(
    page: int = 1,
    per_page: int = 20,
    user: SessionData = Depends(get_current_user),
):
    """List repositories for current user."""
    repos, total = _get_user_repos(user.user_id, page, per_page)

    return ApiResponse(
        data=[RepositoryResponse(
            id=r["id"],
            github_id=r["github_id"],
            owner=r["owner"],
            name=r["name"],
            full_name=r["full_name"],
            enabled=r["enabled"],
            settings=r.get("settings", {}),
            created_at=datetime.fromisoformat(r["created_at"]),
            updated_at=datetime.fromisoformat(r["updated_at"]),
        ) for r in repos],
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=(total + per_page - 1) // per_page if total > 0 else 1,
        ),
    )


@router.get("/{owner}/{name}", response_model=ApiResponse[RepositoryResponse])
async def get_repository(
    owner: str,
    name: str,
    user: SessionData = Depends(get_current_user),
):
    """Get a specific repository."""
    full_name = f"{owner}/{name}"
    repo = next(
        (r for r in _repositories.values()
         if r["full_name"] == full_name and r["user_id"] == user.user_id),
        None
    )

    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )

    return ApiResponse(
        data=RepositoryResponse(
            id=repo["id"],
            github_id=repo["github_id"],
            owner=repo["owner"],
            name=repo["name"],
            full_name=repo["full_name"],
            enabled=repo["enabled"],
            settings=repo.get("settings", {}),
            created_at=datetime.fromisoformat(repo["created_at"]),
            updated_at=datetime.fromisoformat(repo["updated_at"]),
        )
    )


@router.patch("/{owner}/{name}", response_model=ApiResponse[RepositoryResponse])
async def update_repository(
    owner: str,
    name: str,
    update: RepositoryUpdate,
    user: SessionData = Depends(get_current_user),
):
    """Update repository settings."""
    full_name = f"{owner}/{name}"
    repo = next(
        (r for r in _repositories.values()
         if r["full_name"] == full_name and r["user_id"] == user.user_id),
        None
    )

    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )

    if update.enabled is not None:
        repo["enabled"] = update.enabled
    if update.settings is not None:
        repo["settings"] = update.settings

    repo["updated_at"] = datetime.utcnow().isoformat()

    return ApiResponse(
        data=RepositoryResponse(
            id=repo["id"],
            github_id=repo["github_id"],
            owner=repo["owner"],
            name=repo["name"],
            full_name=repo["full_name"],
            enabled=repo["enabled"],
            settings=repo.get("settings", {}),
            created_at=datetime.fromisoformat(repo["created_at"]),
            updated_at=datetime.fromisoformat(repo["updated_at"]),
        )
    )


@router.post("/{owner}/{name}/enable")
async def enable_repository(
    owner: str,
    name: str,
    user: SessionData = Depends(get_current_user),
):
    """Enable AutoPR for a repository."""
    full_name = f"{owner}/{name}"
    repo = next(
        (r for r in _repositories.values()
         if r["full_name"] == full_name and r["user_id"] == user.user_id),
        None
    )

    if not repo:
        # Create new repository entry
        repo = {
            "id": str(uuid.uuid4()),
            "user_id": user.user_id,
            "github_id": hash(full_name) % 1000000,  # Mock ID
            "owner": owner,
            "name": name,
            "full_name": full_name,
            "enabled": True,
            "settings": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        _repositories[repo["id"]] = repo
    else:
        repo["enabled"] = True
        repo["updated_at"] = datetime.utcnow().isoformat()

    return {"success": True}


@router.post("/{owner}/{name}/disable")
async def disable_repository(
    owner: str,
    name: str,
    user: SessionData = Depends(get_current_user),
):
    """Disable AutoPR for a repository."""
    full_name = f"{owner}/{name}"
    repo = next(
        (r for r in _repositories.values()
         if r["full_name"] == full_name and r["user_id"] == user.user_id),
        None
    )

    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )

    repo["enabled"] = False
    repo["updated_at"] = datetime.utcnow().isoformat()

    return {"success": True}
