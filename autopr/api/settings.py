"""Settings API Routes

User settings and API key management.
"""

import hashlib
import secrets
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from .deps import SessionData, get_current_user
from .models import (
    ApiKeyCreate,
    ApiKeyCreated,
    ApiKeyResponse,
    ApiResponse,
    UserSettingsResponse,
    UserSettingsUpdate,
)

router = APIRouter()

# Mock storage
_user_settings: dict[str, dict] = {}
_api_keys: dict[str, dict] = {}


def _hash_key(key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


DEFAULT_SETTINGS = {
    "notifications_email": True,
    "notifications_pr_activity": True,
    "notifications_workflow_failures": True,
    "default_quality_mode": "fast",
    "auto_create_issues": True,
}


@router.get("", response_model=ApiResponse[UserSettingsResponse])
async def get_settings(user: SessionData = Depends(get_current_user)):
    """Get user settings."""
    settings = {**DEFAULT_SETTINGS, **_user_settings.get(user.user_id, {})}
    return ApiResponse(data=UserSettingsResponse(**settings))


@router.patch("", response_model=ApiResponse[UserSettingsResponse])
async def update_settings(
    data: UserSettingsUpdate,
    user: SessionData = Depends(get_current_user),
):
    """Update user settings."""
    if user.user_id not in _user_settings:
        _user_settings[user.user_id] = {}

    # Only update fields that were provided (not None)
    update_data = data.model_dump(exclude_unset=True)
    _user_settings[user.user_id].update(update_data)

    # Return merged settings
    settings = {**DEFAULT_SETTINGS, **_user_settings[user.user_id]}
    return ApiResponse(data=UserSettingsResponse(**settings))


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
