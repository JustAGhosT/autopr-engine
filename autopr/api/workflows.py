"""Workflow API Routes

Workflow management endpoints.
"""

import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from .deps import SessionData, get_current_user
from .models import (
    ApiResponse,
    ExecutionResponse,
    TriggerResponse,
    WorkflowResponse,
    WorkflowUpdate,
)

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

# Mock workflow storage - keyed by user_id -> workflow_id -> workflow
_user_workflows: dict[str, dict[str, dict]] = {}
_workflow_executions: dict[str, list] = {}


def _get_user_workflows(user_id: str) -> dict[str, dict]:
    """Get or initialize workflows for a user."""
    if user_id not in _user_workflows:
        # Initialize with default workflows for this user
        _user_workflows[user_id] = {w["id"]: w.copy() for w in DEFAULT_WORKFLOWS}
    return _user_workflows[user_id]


@router.get("", response_model=ApiResponse[List[WorkflowResponse]])
async def list_workflows(user: SessionData = Depends(get_current_user)):
    """List all workflows for the current user."""
    workflows = _get_user_workflows(user.user_id)
    return ApiResponse(
        data=[WorkflowResponse(
            id=w["id"],
            name=w["name"],
            description=w["description"],
            enabled=w["enabled"],
            triggers=w["triggers"],
            last_run_at=datetime.fromisoformat(w["last_run_at"]) if w.get("last_run_at") else None,
            run_count=w["run_count"],
        ) for w in workflows.values()]
    )


@router.get("/{workflow_id}", response_model=ApiResponse[WorkflowResponse])
async def get_workflow(
    workflow_id: str,
    user: SessionData = Depends(get_current_user),
):
    """Get a specific workflow for the current user."""
    workflows = _get_user_workflows(user.user_id)
    workflow = workflows.get(workflow_id)

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
    """Update workflow settings for the current user."""
    workflows = _get_user_workflows(user.user_id)
    workflow = workflows.get(workflow_id)

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


@router.post("/{workflow_id}/trigger", response_model=TriggerResponse)
async def trigger_workflow(
    workflow_id: str,
    user: SessionData = Depends(get_current_user),
):
    """Manually trigger a workflow for the current user."""
    workflows = _get_user_workflows(user.user_id)
    workflow = workflows.get(workflow_id)

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

    # Record execution - keyed by user_id:workflow_id for user isolation
    execution_key = f"{user.user_id}:{workflow_id}"
    execution_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    if execution_key not in _workflow_executions:
        _workflow_executions[execution_key] = []

    _workflow_executions[execution_key].append({
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

    return TriggerResponse(success=True, execution_id=execution_id)


@router.get("/{workflow_id}/executions", response_model=ApiResponse[List[ExecutionResponse]])
async def get_executions(
    workflow_id: str,
    user: SessionData = Depends(get_current_user),
):
    """Get workflow execution history for the current user."""
    workflows = _get_user_workflows(user.user_id)
    if workflow_id not in workflows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    execution_key = f"{user.user_id}:{workflow_id}"
    executions = _workflow_executions.get(execution_key, [])
    return ApiResponse(
        data=[ExecutionResponse(**e) for e in executions[-20:]]
    )
