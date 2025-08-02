"""
AI Linting Fixer Models

This module contains all Pydantic models used by the AI linting fixer system.
"""

from collections.abc import Callable
from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class OrchestrationConfig(BaseModel):
    """Configuration for workflow orchestration systems."""

    enabled: bool = False
    orchestrator_type: str = "none"  # none, temporal, celery, prefect, airflow

    # Temporal.io configuration
    temporal: dict[str, Any] = Field(
        default_factory=lambda: {
            "namespace": "default",
            "task_queue": "ai-linting-queue",
            "address": "localhost:7233",
            "tls_enabled": False,
            "api_key_env": "TEMPORAL_API_KEY",
        }
    )

    # Celery configuration
    celery: dict[str, Any] = Field(
        default_factory=lambda: {
            "broker_url": "redis://localhost:6379/0",
            "result_backend": "redis://localhost:6379/0",
            "task_name": "ai_linting_task",
        }
    )

    # Prefect configuration
    prefect: dict[str, Any] = Field(
        default_factory=lambda: {"flow_name": "ai_linting_flow", "task_name": "ai_linting_task"}
    )

    # Fallback configuration
    fallback_to_standalone: bool = True


class WorkflowContext(BaseModel):
    """Context for workflow integration and orchestration."""

    # Workflow identification
    workflow_id: str = Field(default_factory=lambda: str(uuid4()))
    parent_workflow_id: str | None = None
    step_name: str = "ai_linting"

    # Execution context
    execution_mode: str = "standalone"  # standalone, orchestrated, pipeline
    priority: int = 5  # 1-10, higher = more priority
    timeout_seconds: int = 300
    retry_config: dict[str, Any] = Field(
        default_factory=lambda: {"max_retries": 3, "retry_delay": 1.0, "exponential_backoff": True}
    )

    # Resource management
    resource_requirements: dict[str, Any] = Field(
        default_factory=lambda: {
            "cpu_cores": 4,
            "memory_mb": 1024,
            "api_quota": 100,
            "estimated_duration": 60,
        }
    )

    # Integration hooks
    progress_callback: Callable | None = None
    error_callback: Callable | None = None
    completion_callback: Callable | None = None

    # Workflow dependencies
    depends_on: list[str] = Field(default_factory=list)
    triggers: list[str] = Field(default_factory=list)

    # Metadata for orchestration
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


class WorkflowEvent(BaseModel):
    """Event emitted during workflow execution for orchestration."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_id: str
    event_type: str  # started, progress, completed, failed, retry
    timestamp: datetime = Field(default_factory=datetime.now)
    step_name: str

    # Event data
    data: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)

    # Error information
    error_message: str | None = None
    error_type: str | None = None
    retry_count: int = 0


class WorkflowResult(BaseModel):
    """Standardized result format for workflow integration."""

    # Execution metadata
    workflow_id: str
    step_name: str
    execution_time: float
    status: str  # success, failed, partial, skipped

    # Core results
    files_processed: int
    issues_found: int
    issues_fixed: int
    modified_files: list[str]

    # Quality metrics
    success_rate: float
    average_confidence: float
    performance_metrics: dict[str, Any]

    # Artifacts for downstream workflows
    artifacts: dict[str, Any] = Field(default_factory=dict)

    # Next step recommendations
    next_steps: list[str] = Field(default_factory=list)

    # Error details if failed
    error_details: dict[str, Any] | None = None


class PerformanceMetrics(BaseModel):
    """Detailed performance metrics for AI linting operations."""

    # Timing metrics
    total_duration: float
    flake8_duration: float
    ai_processing_duration: float
    file_io_duration: float

    # Throughput metrics
    files_per_second: float
    issues_per_second: float
    tokens_per_second: float

    # Resource metrics
    total_files_processed: int
    total_issues_found: int
    total_issues_fixed: int
    total_tokens_used: int
    average_file_size: float

    # Success metrics
    success_rate: float
    average_confidence: float
    syntax_validation_rate: float

    # Efficiency metrics
    api_calls_made: int
    average_api_response_time: float
    queue_waiting_time: float
    parallel_workers_used: int


class LintingIssue(BaseModel):
    """Represents a single linting issue."""

    file_path: str
    line_number: int
    column_number: int
    error_code: str
    message: str
    line_content: str = ""
    column: int = 0  # Keep for backward compatibility


class LintingFixResult(BaseModel):
    """Result of attempting to fix linting issues."""

    success: bool
    fixed_issues: list[str]
    remaining_issues: list[str]
    modified_files: list[str]
    error_message: str | None = None


class FixAttemptLog(BaseModel):
    """Log entry for a fix attempt."""

    timestamp: str
    file_path: str
    issue_type: str
    issue_details: str
    fix_attempted: bool
    fix_successful: bool
    error_message: str | None = None
    llm_model_used: str  # Changed from model_used to avoid pydantic conflict
    provider_used: str
    syntax_valid_before: bool
    syntax_valid_after: bool | None = None
    confidence_score: float | None = None


class AILintingFixerInputs(BaseModel):
    """Input configuration for AI linting fixer with optional orchestration."""

    target_path: str = Field(default=".", description="Path to check for linting issues")
    fix_types: list[str] = Field(
        default=["E501", "F401", "F841", "E722", "E302", "E305", "D200", "D205", "D400", "D401"],
        description="Types of linting issues to fix",
    )
    max_fixes_per_run: int = Field(
        default=10, description="Maximum number of fixes to apply in one run"
    )
    provider: str | None = Field(default=None, description="LLM provider to use")
    model: str | None = Field(default=None, description="Specific model to use")
    max_workers: int = Field(default=4, description="Maximum number of parallel workers")

    # Additional fields for display compatibility
    max_fixes: int = Field(
        default=10, description="Maximum number of fixes (alias for max_fixes_per_run)"
    )
    use_specialized_agents: bool = Field(
        default=True, description="Whether to use specialized AI agents"
    )
    create_backups: bool = Field(
        default=True, description="Whether to create backups before making changes"
    )
    dry_run: bool = Field(default=False, description="Whether to run in dry-run mode")
    enable_async: bool = Field(default=False, description="Whether to enable async processing")

    # Orchestration configuration
    orchestration: OrchestrationConfig | None = Field(
        default=None, description="Workflow orchestration configuration (optional)"
    )
    force_standalone: bool = Field(
        default=False, description="Force standalone execution even if orchestration is configured"
    )


class AILintingFixerOutputs(BaseModel):
    """Outputs from AI linting fixer action."""

    # Core results
    total_issues_found: int
    issues_fixed: int
    files_modified: list[str]
    success: bool
    summary: str

    # Additional fields for display compatibility
    total_issues_detected: int = 0
    issues_queued: int = 0
    issues_processed: int = 0
    issues_failed: int = 0
    total_duration: float = 0.0
    backup_files_created: int = 0
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    # Performance and statistics
    agent_stats: dict[str, Any] = Field(default_factory=dict)
    queue_stats: dict[str, Any] = Field(default_factory=dict)
    redis_stats: dict[str, Any] | None = None

    # Additional metadata
    session_id: str | None = None
    processing_mode: str = "standalone"
    dry_run: bool = False


def create_empty_outputs(session_id: str | None = None) -> AILintingFixerOutputs:
    """Create empty outputs with default values."""
    return AILintingFixerOutputs(
        total_issues_found=0,
        issues_fixed=0,
        files_modified=[],
        success=True,
        summary="No issues found or processed",
        total_issues_detected=0,
        issues_queued=0,
        issues_processed=0,
        issues_failed=0,
        total_duration=0.0,
        backup_files_created=0,
        errors=[],
        warnings=[],
        agent_stats={},
        queue_stats={},
        redis_stats=None,
        session_id=session_id,
        processing_mode="standalone",
        dry_run=False,
    )
