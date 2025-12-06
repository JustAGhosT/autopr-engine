"""API Response Models

Pydantic models for API request/response handling.
"""

from datetime import datetime
from typing import Generic, TypeVar, Optional, List, Any

from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    page: int
    per_page: int
    total: int
    total_pages: int


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    data: T
    meta: Optional[PaginationMeta] = None


class ErrorDetail(BaseModel):
    """Error detail for validation errors."""
    field: Optional[str] = None
    message: str


class ApiError(BaseModel):
    """API error structure."""
    code: str
    message: str
    details: Optional[List[ErrorDetail]] = None


class SuccessResponse(BaseModel):
    """Simple success response."""
    success: bool = True


class SyncResponse(BaseModel):
    """Repository sync response."""
    success: bool
    synced: int
    total: int


class TriggerResponse(BaseModel):
    """Workflow trigger response."""
    success: bool
    execution_id: str


class ExecutionResponse(BaseModel):
    """Workflow execution record."""
    id: str
    workflow_id: str
    triggered_by: str
    status: str
    started_at: str
    completed_at: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response wrapper."""
    error: ApiError


# User models
class UserResponse(BaseModel):
    """User response model."""
    id: str
    github_login: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None


# Repository models
class RepositoryResponse(BaseModel):
    """Repository response model."""
    id: str
    github_id: int
    owner: str
    name: str
    full_name: str
    enabled: bool
    settings: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class RepositoryUpdate(BaseModel):
    """Repository update request model."""
    enabled: Optional[bool] = None
    settings: Optional[dict[str, Any]] = None


# Bot exclusion models
class BotExclusionCreate(BaseModel):
    """Bot exclusion create request."""
    username: str
    reason: Optional[str] = None


class BotExclusionResponse(BaseModel):
    """Bot exclusion response model."""
    id: str
    username: str
    reason: Optional[str] = None
    source: str  # 'config', 'user', 'builtin'
    created_at: datetime


class BotCommentResponse(BaseModel):
    """Bot comment response model."""
    id: str
    repo_id: int
    pr_number: int
    comment_id: int
    bot_username: str
    body: str
    was_excluded: bool
    exclusion_reason: Optional[str] = None
    created_at: datetime


# Workflow models
class WorkflowResponse(BaseModel):
    """Workflow response model."""
    id: str
    name: str
    description: str
    enabled: bool
    triggers: List[str]
    last_run_at: Optional[datetime] = None
    run_count: int


class WorkflowUpdate(BaseModel):
    """Workflow update request model."""
    enabled: Optional[bool] = None
    triggers: Optional[List[str]] = None


# Dashboard models
class DashboardStats(BaseModel):
    """Dashboard statistics."""
    total_prs_processed: int
    issues_created: int
    bots_filtered: int
    active_repos: int
    health_status: str  # 'healthy', 'degraded', 'unhealthy'


class ActivityItem(BaseModel):
    """Activity feed item."""
    id: str
    type: str  # 'pr_analyzed', 'issue_created', 'bot_filtered', 'workflow_run'
    message: str
    repo: str
    created_at: datetime


# Settings models
class UserSettingsUpdate(BaseModel):
    """User settings update request."""
    notifications_email: Optional[bool] = None
    notifications_pr_activity: Optional[bool] = None
    notifications_workflow_failures: Optional[bool] = None
    default_quality_mode: Optional[str] = None
    auto_create_issues: Optional[bool] = None


class UserSettingsResponse(BaseModel):
    """User settings response model."""
    notifications_email: bool
    notifications_pr_activity: bool
    notifications_workflow_failures: bool
    default_quality_mode: str
    auto_create_issues: bool


class RepositorySettingsUpdate(BaseModel):
    """Repository settings update request."""
    auto_analyze_prs: Optional[bool] = None
    auto_create_issues: Optional[bool] = None
    quality_mode: Optional[str] = None
    exclude_paths: Optional[List[str]] = None


class ApiKeyCreate(BaseModel):
    """API key create request."""
    name: str
    scopes: List[str]


class ApiKeyResponse(BaseModel):
    """API key response model."""
    id: str
    name: str
    prefix: str
    scopes: List[str]
    created_at: datetime
    last_used_at: Optional[datetime] = None


class ApiKeyCreated(ApiKeyResponse):
    """API key response after creation (includes full key)."""
    key: str
