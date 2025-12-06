"""Dashboard API Routes

Dashboard statistics and activity endpoints.
"""

import uuid
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends

from .deps import SessionData, get_current_user
from .models import ActivityItem, ApiResponse, DashboardStats

router = APIRouter()

# Mock activity data
_activities: list[dict] = []


def _generate_mock_activities() -> List[dict]:
    """Generate mock activity data for demo purposes."""
    if _activities:
        return _activities

    now = datetime.utcnow()
    sample_activities = [
        ("pr_analyzed", "Analyzed PR #42: Fix authentication bug", "example/repo"),
        ("issue_created", "Created issue #123: Code quality improvements", "example/repo"),
        ("bot_filtered", "Filtered comment from coderabbitai[bot]", "example/app"),
        ("workflow_run", "PR Analysis workflow completed", "example/repo"),
        ("pr_analyzed", "Analyzed PR #41: Add new feature", "example/app"),
        ("bot_filtered", "Filtered comment from dependabot[bot]", "example/repo"),
        ("issue_created", "Created issue #122: Security enhancement", "example/api"),
        ("workflow_run", "Comment Handler workflow triggered", "example/app"),
    ]

    for i, (type_, message, repo) in enumerate(sample_activities):
        _activities.append({
            "id": str(uuid.uuid4()),
            "type": type_,
            "message": message,
            "repo": repo,
            "created_at": (now - timedelta(hours=i * 2)).isoformat(),
        })

    return _activities


@router.get("/stats", response_model=ApiResponse[DashboardStats])
async def get_stats(user: SessionData = Depends(get_current_user)):
    """Get dashboard statistics."""
    # In production, these would come from database queries
    return ApiResponse(
        data=DashboardStats(
            total_prs_processed=127,
            issues_created=42,
            bots_filtered=89,
            active_repos=5,
            health_status="healthy",
        )
    )


@router.get("/activity", response_model=ApiResponse[List[ActivityItem]])
async def get_activity(
    limit: int = 20,
    user: SessionData = Depends(get_current_user),
):
    """Get recent activity feed."""
    activities = _generate_mock_activities()[:limit]

    return ApiResponse(
        data=[ActivityItem(
            id=a["id"],
            type=a["type"],
            message=a["message"],
            repo=a["repo"],
            created_at=datetime.fromisoformat(a["created_at"]),
        ) for a in activities]
    )
