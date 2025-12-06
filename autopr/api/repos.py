"""Repository API Routes

Repository management endpoints.
"""

import asyncio
import uuid
from datetime import datetime
from typing import List

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

from .deps import SessionData, get_current_user
from .models import (
    ApiResponse,
    PaginationMeta,
    RepositoryResponse,
    RepositoryUpdate,
    SuccessResponse,
    SyncResponse,
)

router = APIRouter()

# Mock repository storage (in production, use database)
_repositories: dict[str, dict] = {}

# Retry configuration for external API calls
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds


async def _fetch_with_retry(
    client: httpx.AsyncClient,
    url: str,
    headers: dict,
    max_retries: int = MAX_RETRIES,
) -> httpx.Response:
    """Fetch URL with exponential backoff retry."""
    last_exception = None
    for attempt in range(max_retries):
        try:
            response = await client.get(url, headers=headers)
            return response
        except httpx.RequestError as e:
            last_exception = e
            if attempt < max_retries - 1:
                delay = RETRY_DELAY * (2 ** attempt)
                await asyncio.sleep(delay)
    raise last_exception


async def _fetch_github_repos(github_token: str) -> List[dict]:
    """Fetch repositories from GitHub API with retry logic."""
    repos = []
    page = 1
    per_page = 100  # Max allowed by GitHub API

    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json",
        }

        while True:
            try:
                response = await _fetch_with_retry(
                    client,
                    f"https://api.github.com/user/repos?page={page}&per_page={per_page}&sort=updated",
                    headers,
                )
            except httpx.RequestError:
                break

            if response.status_code != 200:
                break

            page_repos = response.json()
            if not page_repos:
                break

            repos.extend(page_repos)
            page += 1

            # Limit to first 500 repos
            if len(repos) >= 500:
                break

    return repos


def _get_user_repos(user_id: str, page: int = 1, per_page: int = 20) -> tuple[List[dict], int]:
    """Get repositories for a user with pagination."""
    user_repos = [r for r in _repositories.values() if r.get("user_id") == user_id]
    total = len(user_repos)
    start = (page - 1) * per_page
    end = start + per_page
    return user_repos[start:end], total


@router.post("/sync", response_model=SyncResponse)
async def sync_repositories(user: SessionData = Depends(get_current_user)):
    """Sync repositories from GitHub."""
    github_repos = await _fetch_github_repos(user.github_token)

    synced = 0
    now = datetime.utcnow().isoformat()

    for gh_repo in github_repos:
        full_name = gh_repo["full_name"]
        owner, name = full_name.split("/", 1)

        # Check if repo already exists
        existing = next(
            (r for r in _repositories.values()
             if r["github_id"] == gh_repo["id"] and r["user_id"] == user.user_id),
            None
        )

        if existing:
            # Update existing repo
            existing["full_name"] = full_name
            existing["owner"] = owner
            existing["name"] = name
            existing["updated_at"] = now
        else:
            # Create new repo entry
            repo = {
                "id": str(uuid.uuid4()),
                "user_id": user.user_id,
                "github_id": gh_repo["id"],
                "owner": owner,
                "name": name,
                "full_name": full_name,
                "enabled": False,
                "settings": {},
                "created_at": now,
                "updated_at": now,
            }
            _repositories[repo["id"]] = repo

        synced += 1

    return SyncResponse(success=True, synced=synced, total=len(github_repos))


@router.get("", response_model=ApiResponse[List[RepositoryResponse]])
async def list_repositories(
    page: int = Query(1, ge=1, le=1000, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    sync: bool = Query(False, description="Sync from GitHub first"),
    user: SessionData = Depends(get_current_user),
):
    """List repositories for current user."""
    # Auto-sync if no repos exist or sync requested
    user_repos_count = len([r for r in _repositories.values() if r.get("user_id") == user.user_id])
    if sync or user_repos_count == 0:
        await sync_repositories(user)

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


@router.post("/{owner}/{name}/enable", response_model=SuccessResponse)
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

    return SuccessResponse()


@router.post("/{owner}/{name}/disable", response_model=SuccessResponse)
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

    return SuccessResponse()
