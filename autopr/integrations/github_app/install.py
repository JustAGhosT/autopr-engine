"""GitHub App Installation Handler.

Initiates the OAuth flow for GitHub App installation.
"""

import os
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

install_router = APIRouter(prefix="/api/github-app", tags=["github-app"])


@install_router.get("/install")
async def install_app(
    repository: str | None = Query(None),
) -> RedirectResponse:
    """Initiate GitHub App installation OAuth flow.

    Args:
        repository: Optional repository ID to pre-select

    Returns:
        Redirect to GitHub App installation page

    Raises:
        HTTPException: If GitHub App is not configured
    """
    github_app_client_id = os.getenv("GITHUB_APP_CLIENT_ID")
    if not github_app_client_id:
        raise HTTPException(
            status_code=500,
            detail="GitHub App not configured. GITHUB_APP_CLIENT_ID is missing.",
        )

    # Get redirect URI from env or construct default
    site_url = os.getenv("NEXT_PUBLIC_SITE_URL", "http://localhost:8080")
    redirect_uri = os.getenv(
        "GITHUB_APP_REDIRECT_URI",
        f"{site_url}/api/github-app/callback",
    )

    # Build GitHub OAuth URL
    # Replace 'autopr' with your actual GitHub App slug after creation
    github_app_slug = os.getenv("GITHUB_APP_SLUG", "autopr")
    github_auth_url = f"https://github.com/apps/{github_app_slug}/installations/new"

    # Build query parameters
    params = {
        "redirect_uri": redirect_uri,
    }
    if repository:
        params["repository_id"] = repository

    # Redirect to GitHub
    redirect_url = f"{github_auth_url}?{urlencode(params)}"
    return RedirectResponse(url=redirect_url)

