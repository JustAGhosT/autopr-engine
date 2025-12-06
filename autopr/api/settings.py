"""Settings API Routes

User settings and API key management.
"""

from datetime import datetime
from typing import List
import secrets
import hashlib
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from .deps import get_current_user, SessionData
from .models import ApiResponse, ApiKeyCreate, ApiKeyResponse, ApiKeyCreated

router = APIRouter()

# Mock storage
_user_settings: dict[str, dict] = {}
_api_keys: dict[str, dict] = {}


def _hash_key(key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


@router.get("")
async def get_settings(user: SessionData = Depends(get_current_user)):
    """Get user settings."""
    settings = _user_settings.get(user.user_id, {
        "notifications_email": True,
        "notifications_pr_activity": True,
        "notifications_workflow_failures": True,
        "default_quality_mode": "fast",
        "auto_create_issues": True,
    })

    return ApiResponse(data=settings)


@router.patch("")
async def update_settings(
    data: dict,
    user: SessionData = Depends(get_current_user),
):
    """Update user settings."""
    if user.user_id not in _user_settings:
        _user_settings[user.user_id] = {}

    _user_settings[user.user_id].update(data)

    return ApiResponse(data=_user_settings[user.user_id])


@router.get("/api-keys", response_model=ApiResponse[List[ApiKeyResponse]])
async def list_api_keys(user: SessionData = Depends(get_current_user)):
    """List user's API keys."""
    keys = [k for k in _api_keys.values() if k.get("user_id") == user.user_id]

    return ApiResponse(
        data=[ApiKeyResponse(
            id=k["id"],
            name=k["name"],
            prefix=k["prefix"],
            scopes=k["scopes"],
            created_at=datetime.fromisoformat(k["created_at"]),
            last_used_at=datetime.fromisoformat(k["last_used_at"]) if k.get("last_used_at") else None,
        ) for k in keys]
    )


@router.post("/api-keys", response_model=ApiResponse[ApiKeyCreated], status_code=201)
async def create_api_key(
    body: ApiKeyCreate,
    user: SessionData = Depends(get_current_user),
):
    """Create a new API key."""
    # Generate key
    key = f"apr_{secrets.token_urlsafe(32)}"
    prefix = key[:12]
    key_hash = _hash_key(key)

    api_key = {
        "id": str(uuid.uuid4()),
        "user_id": user.user_id,
        "name": body.name,
        "prefix": prefix,
        "key_hash": key_hash,
        "scopes": body.scopes,
        "created_at": datetime.utcnow().isoformat(),
        "last_used_at": None,
    }

    _api_keys[api_key["id"]] = api_key

    return ApiResponse(
        data=ApiKeyCreated(
            id=api_key["id"],
            name=api_key["name"],
            prefix=api_key["prefix"],
            scopes=api_key["scopes"],
            created_at=datetime.fromisoformat(api_key["created_at"]),
            last_used_at=None,
            key=key,  # Only returned on creation
        )
    )


@router.delete("/api-keys/{key_id}", status_code=204)
async def revoke_api_key(
    key_id: str,
    user: SessionData = Depends(get_current_user),
):
    """Revoke an API key."""
    api_key = _api_keys.get(key_id)

    if not api_key or api_key.get("user_id") != user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    del _api_keys[key_id]
    return None
