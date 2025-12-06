"""Bot Exclusion API Routes

Bot exclusion management endpoints.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from .deps import SessionData, get_current_user
from .models import (
    ApiResponse,
    BotCommentResponse,
    BotExclusionCreate,
    BotExclusionResponse,
    PaginationMeta,
)

router = APIRouter()

# Built-in bot exclusions (always excluded)
BUILTIN_EXCLUSIONS = [
    "github-actions[bot]",
    "dependabot[bot]",
    "dependabot-preview[bot]",
    "renovate[bot]",
    "coderabbitai[bot]",
    "chatgpt-codex-connector[bot]",
    "copilot[bot]",
    "codecov[bot]",
    "sonarcloud[bot]",
    "netlify[bot]",
    "vercel[bot]",
]

# Mock storage (in production, use database)
_user_exclusions: dict[str, dict] = {}
_bot_comments: list[dict] = []


# Builtin exclusions are considered to have always existed
BUILTIN_CREATED_AT = "1970-01-01T00:00:00Z"


def _get_all_exclusions(user_id: str) -> List[dict]:
    """Get all exclusions for a user (builtin + user-defined)."""
    exclusions = []

    # Add builtin exclusions
    for bot in BUILTIN_EXCLUSIONS:
        exclusions.append({
            "id": f"builtin-{bot}",
            "username": bot,
            "reason": "Built-in bot exclusion",
            "source": "builtin",
            "created_at": BUILTIN_CREATED_AT,
        })

    # Add user exclusions
    for exc in _user_exclusions.values():
        if exc.get("user_id") == user_id:
            exclusions.append(exc)

    return exclusions


@router.get("/exclusions", response_model=ApiResponse[List[BotExclusionResponse]])
async def list_exclusions(user: SessionData = Depends(get_current_user)):
    """List all bot exclusions for current user."""
    exclusions = _get_all_exclusions(user.user_id)

    return ApiResponse(
        data=[BotExclusionResponse(
            id=e["id"],
            username=e["username"],
            reason=e.get("reason"),
            source=e["source"],
            created_at=datetime.fromisoformat(e["created_at"]),
        ) for e in exclusions]
    )


@router.post("/exclusions", response_model=ApiResponse[BotExclusionResponse], status_code=201)
async def add_exclusion(
    body: BotExclusionCreate,
    user: SessionData = Depends(get_current_user),
):
    """Add a bot to the exclusion list."""
    # Check if already exists
    existing = next(
        (e for e in _user_exclusions.values()
         if e.get("user_id") == user.user_id and e["username"] == body.username),
        None
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bot already excluded"
        )

    # Check if it's a builtin
    if body.username in BUILTIN_EXCLUSIONS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bot is already excluded by default"
        )

    # Create new exclusion
    exclusion = {
        "id": str(uuid.uuid4()),
        "user_id": user.user_id,
        "username": body.username,
        "reason": body.reason,
        "source": "user",
        "created_at": datetime.utcnow().isoformat(),
    }

    _user_exclusions[exclusion["id"]] = exclusion

    return ApiResponse(
        data=BotExclusionResponse(
            id=exclusion["id"],
            username=exclusion["username"],
            reason=exclusion.get("reason"),
            source=exclusion["source"],
            created_at=datetime.fromisoformat(exclusion["created_at"]),
        )
    )


@router.delete("/exclusions/{username}", status_code=204)
async def remove_exclusion(
    username: str,
    user: SessionData = Depends(get_current_user),
):
    """Remove a bot from the exclusion list."""
    # Find the exclusion
    exclusion = next(
        (e for e in _user_exclusions.values()
         if e.get("user_id") == user.user_id and e["username"] == username),
        None
    )

    if not exclusion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exclusion not found"
        )

    del _user_exclusions[exclusion["id"]]
    return None


@router.get("/comments", response_model=ApiResponse[List[BotCommentResponse]])
async def list_comments(
    page: int = Query(1, ge=1, le=1000, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    excluded: Optional[bool] = Query(None, description="Filter by exclusion status"),
    user: SessionData = Depends(get_current_user),
):
    """List recent bot comments for the current user."""
    # Filter comments by user first, then by exclusion status
    user_comments = [c for c in _bot_comments if c.get("user_id") == user.user_id]

    if excluded is not None:
        user_comments = [c for c in user_comments if c["was_excluded"] == excluded]

    total = len(user_comments)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = user_comments[start:end]

    return ApiResponse(
        data=[BotCommentResponse(
            id=c["id"],
            repo_id=c["repo_id"],
            pr_number=c["pr_number"],
            comment_id=c["comment_id"],
            bot_username=c["bot_username"],
            body=c["body"],
            was_excluded=c["was_excluded"],
            exclusion_reason=c.get("exclusion_reason"),
            created_at=datetime.fromisoformat(c["created_at"]),
        ) for c in paginated],
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=(total + per_page - 1) // per_page if total > 0 else 1,
        ),
    )


@router.get("/analytics", response_model=ApiResponse[dict])
async def get_analytics(user: SessionData = Depends(get_current_user)):
    """Get bot filtering analytics for the current user."""
    # Calculate analytics from user's comments only
    bot_counts: dict[str, int] = {}
    for comment in _bot_comments:
        if comment.get("user_id") == user.user_id and comment["was_excluded"]:
            bot = comment["bot_username"]
            bot_counts[bot] = bot_counts.get(bot, 0) + 1

    return ApiResponse(data=bot_counts)
