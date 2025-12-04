"""GitHub App OAuth Callback Handler.

Handles the callback from GitHub after app installation.
"""

import os
from urllib.parse import parse_qs, urlencode

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from github import GithubIntegration

callback_router = APIRouter(prefix="/api/github-app", tags=["github-app"])


@callback_router.get("/callback")
async def callback(
    code: str | None = Query(None),
    state: str | None = Query(None),
    installation_id: str | None = Query(None),
) -> RedirectResponse:
    """Handle GitHub App OAuth callback.

    Args:
        code: OAuth authorization code
        state: OAuth state parameter
        installation_id: GitHub App installation ID

    Returns:
        Redirect to setup page with installation info

    Raises:
        HTTPException: If required parameters or configuration is missing
    """
    if not code or not installation_id:
        raise HTTPException(
            status_code=400,
            detail="Missing required parameters: code and installation_id are required",
        )

    github_app_id = os.getenv("GITHUB_APP_ID")
    github_app_private_key = os.getenv("GITHUB_APP_PRIVATE_KEY")

    if not github_app_id or not github_app_private_key:
        raise HTTPException(
            status_code=500,
            detail="GitHub App not configured",
        )

    try:
        # Create GitHub integration
        integration = GithubIntegration(
            github_app_id,
            github_app_private_key.replace("\\n", "\n"),
        )

        # Get installation (already has account info)
        installation = integration.get_installation(int(installation_id))

        # Get account login from installation object
        account = installation.account
        account_login = account.login if account else ""

        # Redirect to setup page
        site_url = os.getenv("NEXT_PUBLIC_SITE_URL", "http://localhost:8080")
        setup_url = f"{site_url}/setup?{urlencode({'installation_id': installation_id, 'account': account_login})}"

        return RedirectResponse(url=setup_url)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process installation: {str(e)}",
        )

