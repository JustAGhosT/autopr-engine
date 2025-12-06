"""Workflow API Routes

Workflow management endpoints.
"""

from datetime import datetime
from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from .deps import get_current_user, SessionData
from .models import ApiResponse, WorkflowResponse, WorkflowUpdate, PaginationMeta

router = APIRouter()

# Default workflows
DEFAULT_WORKFLOWS = [
    {
        "id": "wf-pr-analysis",
        "name": "PR Analysis",
        "description": "Analyze PRs for code quality and potential issues",
        "enabled": True,
        "triggers": ["pull_request.opened", "pull_request.synchronize"],
        "run_count": 0,
        "last_run_at": None,
    },
    {
        "id": "wf-issue-creation",
        "name": "Issue Creation",
        "description": "Automatically create issues from PR analysis results",
        "enabled": True,
        "triggers": ["pr_analyzed"],
        "run_count": 0,
        "last_run_at": None,
    },
    {
        "id": "wf-comment-handler",
        "name": "Comment Handler",
        "description": "Process and respond to PR comments",
        "enabled": True,
        "triggers": ["issue_comment.created"],
        "run_count": 0,
        "last_run_at": None,
    },
    {
        "id": "wf-bot-filter",
        "name": "Bot Filter",
        "description": "Filter out bot comments based on exclusion rules",
        "enabled": True,
        "triggers": ["issue_comment.created"],
        "run_count": 0,
        "last_run_at": None,
    },
]

# Mock workflow storage
_workflows: dict[str, dict] = {w["id"]: w.copy() for w in DEFAULT_WORKFLOWS}
_workflow_executions: dict[str, list] = {}


@router.get("", response_model=ApiResponse[List[WorkflowResponse]])
async def list_workflows(user: SessionData = Depends(get_current_user)):
    """List all workflows."""
    return ApiResponse(
        data=[WorkflowResponse(
            id=w["id"],
            name=w["name"],
            description=w["description"],
            enabled=w["enabled"],
            triggers=w["triggers"],
            last_run_at=datetime.fromisoformat(w["last_run_at"]) if w.get("last_run_at") else None,
            run_count=w["run_count"],
        ) for w in _workflows.values()]
    )


@router.get("/{workflow_id}", response_model=ApiResponse[WorkflowResponse])
async def get_workflow(
    workflow_id: str,
    user: SessionData = Depends(get_current_user),
):
    """Get a specific workflow."""
    workflow = _workflows.get(workflow_id)

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    return ApiResponse(
        data=WorkflowResponse(
            id=workflow["id"],
            name=workflow["name"],
            description=workflow["description"],
            enabled=workflow["enabled"],
            triggers=workflow["triggers"],
            last_run_at=datetime.fromisoformat(workflow["last_run_at"]) if workflow.get("last_run_at") else None,
            run_count=workflow["run_count"],
        )
    )


@router.patch("/{workflow_id}", response_model=ApiResponse[WorkflowResponse])
async def update_workflow(
    workflow_id: str,
    update: WorkflowUpdate,
    user: SessionData = Depends(get_current_user),
):
    """Update workflow settings."""
    workflow = _workflows.get(workflow_id)

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    if update.enabled is not None:
        workflow["enabled"] = update.enabled
    if update.triggers is not None:
        workflow["triggers"] = update.triggers

    return ApiResponse(
        data=WorkflowResponse(
            id=workflow["id"],
            name=workflow["name"],
            description=workflow["description"],
            enabled=workflow["enabled"],
            triggers=workflow["triggers"],
            last_run_at=datetime.fromisoformat(workflow["last_run_at"]) if workflow.get("last_run_at") else None,
            run_count=workflow["run_count"],
        )
    )


@router.post("/{workflow_id}/trigger")
async def trigger_workflow(
    workflow_id: str,
    user: SessionData = Depends(get_current_user),
):
    """Manually trigger a workflow."""
    workflow = _workflows.get(workflow_id)

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    if not workflow["enabled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow is disabled"
        )

    # Record execution
    execution_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    if workflow_id not in _workflow_executions:
        _workflow_executions[workflow_id] = []

    _workflow_executions[workflow_id].append({
        "id": execution_id,
        "workflow_id": workflow_id,
        "triggered_by": user.github_login,
        "status": "completed",
        "started_at": now,
        "completed_at": now,
    })

    # Update workflow stats
    workflow["run_count"] += 1
    workflow["last_run_at"] = now

    return {"success": True, "execution_id": execution_id}


@router.get("/{workflow_id}/executions")
async def get_executions(
    workflow_id: str,
    user: SessionData = Depends(get_current_user),
):
    """Get workflow execution history."""
    if workflow_id not in _workflows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    executions = _workflow_executions.get(workflow_id, [])
    return ApiResponse(data=executions[-20:])  # Last 20 executions
