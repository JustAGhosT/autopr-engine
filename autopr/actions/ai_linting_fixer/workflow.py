"""
Workflow Integration Patterns

Handles workflow contexts, events, and results for integration with
orchestration systems and enterprise workflow platforms.
"""

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


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


class WorkflowIntegrationMixin:
    """Mixin for workflow orchestration capabilities."""

    def __init__(self):
        self.workflow_events: list[WorkflowEvent] = []
        self.workflow_context: WorkflowContext | None = None

    def emit_event(
        self,
        event_type: str,
        data: dict[str, Any] | None = None,
        metrics: dict[str, Any] | None = None,
        error: Exception | None = None,
    ):
        """Emit workflow event for orchestration systems."""
        if not self.workflow_context:
            return

        event = WorkflowEvent(
            workflow_id=self.workflow_context.workflow_id,
            event_type=event_type,
            step_name=self.workflow_context.step_name,
            data=data or {},
            metrics=metrics or {},
            error_message=str(error) if error else None,
            error_type=type(error).__name__ if error else None,
        )

        self.workflow_events.append(event)

        # Call registered callbacks
        if event_type == "progress" and self.workflow_context.progress_callback:
            try:
                self.workflow_context.progress_callback(event)
            except Exception as e:
                logger.exception(f"Progress callback failed: {e}")

        elif event_type == "failed" and self.workflow_context.error_callback:
            try:
                self.workflow_context.error_callback(event)
            except Exception as e:
                logger.exception(f"Error callback failed: {e}")

        elif event_type == "completed" and self.workflow_context.completion_callback:
            try:
                self.workflow_context.completion_callback(event)
            except Exception as e:
                logger.exception(f"Completion callback failed: {e}")

    def should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if operation should be retried based on workflow config."""
        if not self.workflow_context:
            return False

        retry_config = self.workflow_context.retry_config
        max_retries = retry_config.get("max_retries", 3)

        if attempt >= max_retries:
            return False

        # Define retryable errors
        retryable_errors = (
            ConnectionError,
            TimeoutError,
            # Add more specific errors as needed
        )

        return isinstance(error, retryable_errors)

    def calculate_retry_delay(self, attempt: int) -> float:
        """Calculate delay before retry."""
        if not self.workflow_context:
            return 1.0

        retry_config = self.workflow_context.retry_config
        base_delay = retry_config.get("retry_delay", 1.0)

        if retry_config.get("exponential_backoff", True):
            return base_delay * (2**attempt)
        return base_delay

    def create_workflow_result(self, success: bool, **kwargs) -> WorkflowResult:
        """Create standardized workflow result."""
        if not self.workflow_context:
            workflow_id = str(uuid4())
            step_name = "ai_linting"
        else:
            workflow_id = self.workflow_context.workflow_id
            step_name = self.workflow_context.step_name

        return WorkflowResult(
            workflow_id=workflow_id,
            step_name=step_name,
            execution_time=kwargs.get("execution_time", 0.0),
            status="success" if success else "failed",
            files_processed=kwargs.get("files_processed", 0),
            issues_found=kwargs.get("issues_found", 0),
            issues_fixed=kwargs.get("issues_fixed", 0),
            modified_files=kwargs.get("modified_files", []),
            success_rate=kwargs.get("success_rate", 0.0),
            average_confidence=kwargs.get("average_confidence", 0.0),
            performance_metrics=kwargs.get("performance_metrics", {}),
            artifacts=kwargs.get("artifacts", {}),
            next_steps=kwargs.get("next_steps", []),
            error_details=kwargs.get("error_details"),
        )


class WorkflowEventBus:
    """Event bus for publishing and subscribing to workflow events."""

    def __init__(self):
        self.subscribers: dict[str, list[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to workflow events of a specific type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def publish(self, event: WorkflowEvent) -> None:
        """Publish a workflow event to all subscribers."""
        # Publish to specific event type subscribers
        if event.event_type in self.subscribers:
            for callback in self.subscribers[event.event_type]:
                try:
                    callback(event)
                except Exception as e:
                    logger.exception(f"Event subscriber callback failed: {e}")

        # Publish to wildcard subscribers
        if "*" in self.subscribers:
            for callback in self.subscribers["*"]:
                try:
                    callback(event)
                except Exception as e:
                    logger.exception(f"Wildcard event subscriber callback failed: {e}")


# Global event bus instance
workflow_event_bus = WorkflowEventBus()


class WorkflowRegistry:
    """Registry for tracking active workflows and their statuses."""

    def __init__(self):
        self.active_workflows: dict[str, dict[str, Any]] = {}

    def register_workflow(self, workflow_context: WorkflowContext) -> None:
        """Register a new workflow."""
        self.active_workflows[workflow_context.workflow_id] = {
            "context": workflow_context,
            "start_time": datetime.now(),
            "status": "started",
            "events": [],
            "last_update": datetime.now(),
        }

    def update_workflow_status(
        self, workflow_id: str, status: str, event: WorkflowEvent | None = None
    ) -> None:
        """Update workflow status."""
        if workflow_id in self.active_workflows:
            self.active_workflows[workflow_id]["status"] = status
            self.active_workflows[workflow_id]["last_update"] = datetime.now()

            if event:
                self.active_workflows[workflow_id]["events"].append(event)

    def complete_workflow(self, workflow_id: str, result: WorkflowResult) -> None:
        """Mark workflow as completed."""
        if workflow_id in self.active_workflows:
            self.active_workflows[workflow_id]["status"] = "completed"
            self.active_workflows[workflow_id]["result"] = result
            self.active_workflows[workflow_id]["end_time"] = datetime.now()

    def get_workflow_status(self, workflow_id: str) -> dict[str, Any] | None:
        """Get current status of a workflow."""
        return self.active_workflows.get(workflow_id)

    def list_active_workflows(self) -> list[dict[str, Any]]:
        """List all active workflows."""
        return [
            {
                "workflow_id": wf_id,
                "step_name": info["context"].step_name,
                "status": info["status"],
                "start_time": info["start_time"],
                "last_update": info["last_update"],
            }
            for wf_id, info in self.active_workflows.items()
            if info["status"] not in {"completed", "failed"}
        ]


# Global workflow registry instance
workflow_registry = WorkflowRegistry()
