"""Authentication API Routes

GitHub OAuth authentication and session management.
"""

import secrets
import time
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse

from .deps import (
    IS_PRODUCTION,
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE,
    SessionData,
    create_session,
    delete_session,
    get_current_user,
    get_github_oauth_config,
)
from .models import ApiResponse, UserResponse

# OAuth state expiry in seconds (5 minutes)
OAUTH_STATE_TTL = 300

router = APIRouter()

# State storage for OAuth with timestamp (in production, use Redis with expiry)
_oauth_states: dict[str, float] = {}


def _cleanup_expired_states() -> None:
    """Remove expired OAuth states to prevent memory leaks."""
    now = time.time()
    expired = [state for state, created_at in _oauth_states.items()
               if now - created_at > OAUTH_STATE_TTL]
    for state in expired:
        del _oauth_states[state]


def _is_valid_state(state: str) -> bool:
    """Check if OAuth state is valid and not expired."""
    if state not in _oauth_states:
        return False
    created_at = _oauth_states[state]
    if time.time() - created_at > OAUTH_STATE_TTL:
        del _oauth_states[state]
        return False
    return True


@router.get("/github/login")
async def github_login(request: Request):
    """Initiate GitHub OAuth flow."""
    config = get_github_oauth_config()

    if not config["client_id"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub OAuth not configured"
        )

    # Cleanup expired states periodically
    _cleanup_expired_states()

    # Generate state for CSRF protection with timestamp
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = time.time()

    # Build GitHub authorization URL
    params = {
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "scope": "user:email read:org repo",
        "state": state,
    }

    auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/github/callback")
async def github_callback(code: str, state: str, request: Request):
    """Handle GitHub OAuth callback."""
    # Verify state is valid and not expired
    if not _is_valid_state(state):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state"
        )
    del _oauth_states[state]

    config = get_github_oauth_config()

    # Exchange code for access token
    async with httpx.AsyncClient(timeout=30.0) as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": config["client_id"],
                "client_secret": config["client_secret"],
                "code": code,
                "redirect_uri": config["redirect_uri"],
            },
            headers={"Accept": "application/json"},
        )

        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for token"
            )

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token received"
            )

        # Get user info from GitHub
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )

        if user_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info"
            )

        user_data = user_response.json()

    # Create session
    session_id = create_session(
        user_id=str(user_data["id"]),
        github_login=user_data["login"],
        github_token=access_token,
        avatar_url=user_data.get("avatar_url"),
        email=user_data.get("email"),
    )

    # Redirect to dashboard with session cookie
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
    )

    return response


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_me(user: SessionData = Depends(get_current_user)):
    """Get current authenticated user."""
    return ApiResponse(
        data=UserResponse(
            id=user.user_id,
            github_login=user.github_login,
            email=user.email,
            avatar_url=user.avatar_url,
        )
    )


@router.post("/logout")
async def logout(user: SessionData = Depends(get_current_user)):
    """End current session."""
    delete_session(user.session_id)

    response = JSONResponse(content={"success": True})
    response.delete_cookie(SESSION_COOKIE_NAME)

    return response


@router.post("/refresh")
async def refresh_session(user: SessionData = Depends(get_current_user)):
    """Refresh current session."""
    # Delete old session and create new one
    delete_session(user.session_id)

    new_session_id = create_session(
        user_id=user.user_id,
        github_login=user.github_login,
        github_token=user.github_token,
        avatar_url=user.avatar_url,
        email=user.email,
    )

    response = JSONResponse(content={"success": True})
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=new_session_id,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
    )

    return response
