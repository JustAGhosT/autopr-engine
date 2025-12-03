"""GitHub App Webhook Handler.

Receives webhook events from GitHub when the app is installed/uninstalled.
"""

import hashlib
import hmac
import json
import logging
import os

from fastapi import APIRouter, Header, HTTPException, Request
from github import GithubIntegration

from autopr.integrations.github_app.secrets import configure_repository_secrets

webhook_router = APIRouter(prefix="/api/github-app", tags=["github-app"])
logger = logging.getLogger(__name__)


@webhook_router.post("/webhook")
async def webhook(
    request: Request,
    x_github_event: str = Header(..., alias="x-github-event"),
    x_hub_signature_256: str | None = Header(None, alias="x-hub-signature-256"),
) -> dict:
    """Handle GitHub App webhook events.

    Args:
        request: FastAPI request object
        x_github_event: GitHub event type
        x_hub_signature_256: Webhook signature for verification

    Returns:
        Confirmation response

    Raises:
        HTTPException: If webhook secret is not configured or signature is invalid
    """
    webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    if not webhook_secret:
        raise HTTPException(
            status_code=500,
            detail="Webhook secret not configured",
        )

    # Get request body
    body = await request.body()

    # Verify webhook signature
    if x_hub_signature_256:
        expected_signature = hmac.new(
            webhook_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        expected_header = f"sha256={expected_signature}"

        if not hmac.compare_digest(x_hub_signature_256, expected_header):
            raise HTTPException(
                status_code=401,
                detail="Invalid webhook signature",
            )

    try:
        payload = json.loads(body.decode())

        if x_github_event == "installation" and payload.get("action") == "created":
            await handle_installation(payload.get("installation", {}))
        elif (
            x_github_event == "installation_repositories"
            and payload.get("action") == "added"
        ):
            installation = payload.get("installation", {})
            installation_id = installation.get("id")
            owner = installation.get("account", {}).get("login", "")

            for repo in payload.get("repositories_added", []):
                await configure_repository_secrets(
                    installation_id,
                    owner,
                    repo.get("name", ""),
                )

        return {"received": True}

    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Webhook processing failed: {str(e)}",
        )


async def handle_installation(installation: dict) -> None:
    """Handle installation created event.

    Args:
        installation: Installation data from webhook payload
    """
    installation_id = installation.get("id")
    logger.info(f"Handling installation: {installation_id}")
    # Installation is handled, repositories will be configured via installation_repositories event

