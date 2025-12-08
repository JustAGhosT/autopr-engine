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

from codeflow_engine.integrations.github_app.secrets import configure_repository_secrets

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

    # Verify webhook signature - reject if missing when secret is configured
    if not x_hub_signature_256:
        raise HTTPException(
            status_code=401,
            detail="Missing webhook signature header",
        )

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
        elif x_github_event == "issue_comment" and payload.get("action") == "created":
            # Handle PR comments (issue_comment event includes PR comments)
            if "pull_request" in payload.get("issue", {}):
                await handle_pr_comment(payload)
    except Exception as e:
        from codeflow_engine.exceptions import sanitize_error_message
        
        logger.error(f"Webhook error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Webhook processing failed: {sanitize_error_message(str(e))}",
        ) from e
    else:
        return {"received": True}


async def handle_installation(installation: dict) -> None:
    """Handle installation created event.

    Args:
        installation: Installation data from webhook payload
    """
    installation_id = installation.get("id")
    logger.info(f"Handling installation: {installation_id}")
    # Installation is handled, repositories will be configured via installation_repositories event


async def handle_pr_comment(payload: dict) -> None:
    """Handle PR comment event with filtering.

    Args:
        payload: Webhook payload containing comment data
    """
    from codeflow_engine.database.config import get_db
    from codeflow_engine.services.comment_filter import CommentFilterService
    
    comment = payload.get("comment", {})
    commenter_username = comment.get("user", {}).get("login", "")
    commenter_id = comment.get("user", {}).get("id")
    
    if not commenter_username:
        logger.warning("Comment received without username, skipping")
        return
    
    logger.info(f"Processing comment from {commenter_username}")
    
    # Check if commenter is allowed
    try:
        # Get database session (synchronous)
        db = next(get_db())
        try:
            service = CommentFilterService(db)
            
            # Note: Using synchronous version since get_db() returns sync session
            # The service detects this automatically via isinstance check
            is_allowed = await service.is_commenter_allowed(commenter_username)
            
            if not is_allowed:
                logger.info(f"Comment from {commenter_username} filtered (not in allowed list)")
                
                # Check if auto-add is enabled
                settings = await service.get_settings()
                if settings and settings.auto_add_commenters:
                    # Add the commenter automatically
                    await service.add_commenter(
                        github_username=commenter_username,
                        github_user_id=commenter_id,
                        added_by="auto",
                        notes="Automatically added via auto_add_commenters setting",
                    )
                    logger.info(f"Auto-added commenter: {commenter_username}")
                    
                    # Send auto-reply if enabled
                    if settings.auto_reply_enabled:
                        await send_comment_reply(payload, commenter_username, settings)
                
                # Don't process the comment
                return
            
            # Update commenter activity
            await service.update_commenter_activity(commenter_username)
            
            # Process the comment (existing logic would go here)
            logger.info(f"Processing comment from allowed user: {commenter_username}")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error processing comment filter: {e}", exc_info=True)
        # On error, allow comment to be processed (fail open)


async def send_comment_reply(payload: dict, username: str, settings) -> None:
    """Send auto-reply comment when adding a new commenter.

    Args:
        payload: Webhook payload
        username: GitHub username of the new commenter
        settings: Comment filter settings
    """
    try:
        repo_full_name = payload.get("repository", {}).get("full_name", "")
        comment_url = payload.get("comment", {}).get("url", "")
        
        if not repo_full_name or not comment_url:
            logger.warning("Missing repo or comment URL for auto-reply")
            return
        
        # Get the auto-reply message
        message = settings.auto_reply_message.format(username=username)
        
        # Post reply comment using GitHub API
        # This requires GitHub App credentials
        # For now, just log it
        logger.info(f"Would send auto-reply to {username}: {message}")
        
        # TODO: Implement actual GitHub API call to post comment
        # This would require:
        # 1. Get installation token
        # 2. Use PyGithub or httpx to post comment
        # 3. Handle rate limiting and errors
        
    except Exception as e:
        logger.error(f"Error sending auto-reply: {e}", exc_info=True)

