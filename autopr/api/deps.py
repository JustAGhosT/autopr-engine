"""API Dependencies

Common dependencies for API endpoints including authentication.
"""

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Any

from fastapi import HTTPException, Request, status

# Configure logger for API module
logger = logging.getLogger("autopr.api")

# Environment check for security settings
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"

# Session storage (in production, use Redis)
_sessions: dict[str, dict[str, Any]] = {}

SESSION_COOKIE_NAME = "autopr_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 days


class SessionData:
    """Session data container."""

    def __init__(self, session_id: str, user_id: str, github_login: str,
                 github_token: str, avatar_url: Optional[str] = None,
                 email: Optional[str] = None):
        self.session_id = session_id
        self.user_id = user_id
        self.github_login = github_login
        self.github_token = github_token
        self.avatar_url = avatar_url
        self.email = email


def create_session(user_id: str, github_login: str, github_token: str,
                   avatar_url: Optional[str] = None, email: Optional[str] = None) -> str:
    """Create a new session and return session ID."""
    session_id = secrets.token_urlsafe(32)
    _sessions[session_id] = {
        "user_id": user_id,
        "github_login": github_login,
        "github_token": github_token,
        "avatar_url": avatar_url,
        "email": email,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(seconds=SESSION_MAX_AGE)).isoformat(),
    }
    return session_id


def get_session(session_id: str) -> Optional[dict[str, Any]]:
    """Get session data by session ID."""
    session = _sessions.get(session_id)
    if not session:
        return None

    # Check if session expired
    expires_at = datetime.fromisoformat(session["expires_at"])
    if datetime.utcnow() > expires_at:
        delete_session(session_id)
        return None

    return session


def delete_session(session_id: str) -> bool:
    """Delete a session."""
    if session_id in _sessions:
        del _sessions[session_id]
        return True
    return False


async def get_session_from_cookie(request: Request) -> Optional[str]:
    """Extract session ID from cookie."""
    return request.cookies.get(SESSION_COOKIE_NAME)


def _hash_api_key(key: str) -> str:
    """Hash an API key for lookup."""
    return hashlib.sha256(key.encode()).hexdigest()


# API key storage reference (shared with settings.py)
# In production, this would use a database
_api_keys_ref: Optional[dict] = None


def set_api_keys_storage(storage: dict) -> None:
    """Set reference to API keys storage from settings module."""
    global _api_keys_ref
    _api_keys_ref = storage


def get_api_keys_storage() -> dict:
    """Get API keys storage, importing from settings if needed."""
    global _api_keys_ref
    if _api_keys_ref is None:
        # Lazy import to avoid circular dependency
        from . import settings
        _api_keys_ref = settings._api_keys
    return _api_keys_ref


async def authenticate_api_key(request: Request) -> Optional[SessionData]:
    """Authenticate via API key in Authorization header.

    Returns SessionData if valid API key, None otherwise.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer apr_"):
        return None

    api_key = auth_header.replace("Bearer ", "")
    key_hash = _hash_api_key(api_key)

    api_keys = get_api_keys_storage()
    for key_data in api_keys.values():
        if key_data.get("key_hash") == key_hash:
            # Update last used timestamp
            key_data["last_used_at"] = datetime.utcnow().isoformat()

            # Create a SessionData-like object for API key auth
            return SessionData(
                session_id=f"api_key:{key_data['id']}",
                user_id=key_data["user_id"],
                github_login=f"api_key:{key_data['name']}",
                github_token="",  # API keys don't have GitHub access
                avatar_url=None,
                email=None,
            )

    return None


async def get_current_user(request: Request) -> SessionData:
    """Get current authenticated user from session or API key.

    Raises HTTPException 401 if not authenticated.
    """
    # Try API key authentication first
    api_key_user = await authenticate_api_key(request)
    if api_key_user:
        return api_key_user

    # Fall back to session cookie authentication
    session_id = await get_session_from_cookie(request)
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    session = get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired"
        )

    return SessionData(
        session_id=session_id,
        user_id=session["user_id"],
        github_login=session["github_login"],
        github_token=session["github_token"],
        avatar_url=session.get("avatar_url"),
        email=session.get("email"),
    )


async def get_optional_user(request: Request) -> Optional[SessionData]:
    """Get current user if authenticated, None otherwise."""
    try:
        return await get_current_user(request)
    except HTTPException:
        return None


# OAuth configuration
def get_github_oauth_config() -> dict[str, str]:
    """Get GitHub OAuth configuration from environment."""
    return {
        "client_id": os.getenv("GITHUB_CLIENT_ID", ""),
        "client_secret": os.getenv("GITHUB_CLIENT_SECRET", ""),
        "redirect_uri": os.getenv("GITHUB_OAUTH_REDIRECT_URI",
                                  "http://localhost:8080/api/auth/github/callback"),
    }
