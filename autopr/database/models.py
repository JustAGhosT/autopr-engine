"""
SQLAlchemy Database Models

This module defines the database schema for AutoPR Engine using SQLAlchemy ORM.
All models inherit from the declarative Base class.

TODO: Production considerations:
- [ ] Add model-level validation using SQLAlchemy validators
- [ ] Implement soft deletes with is_deleted flag pattern
- [ ] Add created_by/updated_by tracking for audit trails
- [ ] Consider adding database-level constraints for data integrity
- [ ] Implement model serialization methods for API responses
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


# TODO: Add audit mixin for created_at, updated_at, created_by, updated_by
class AuditMixin:
    """Mixin for audit fields."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class Workflow(Base, AuditMixin):
    """Workflow definition model."""

    __tablename__ = "workflows"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active"
    )
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    executions: Mapped[list["WorkflowExecution"]] = relationship(
        "WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan"
    )
    actions: Mapped[list["WorkflowAction"]] = relationship(
        "WorkflowAction", back_populates="workflow", cascade="all, delete-orphan"
    )
    triggers: Mapped[list["WorkflowTrigger"]] = relationship(
        "WorkflowTrigger", back_populates="workflow", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'archived', 'draft')",
            name="chk_workflow_status",
        ),
        Index("idx_workflows_status", "status"),
        Index("idx_workflows_created_at", "created_at"),
        Index("idx_workflows_config", "config", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        return f"<Workflow(id={self.id}, name={self.name}, status={self.status})>"


class WorkflowExecution(Base):
    """Workflow execution tracking model."""

    __tablename__ = "workflow_executions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False
    )
    execution_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parent_execution_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_executions.id"), nullable=True
    )
    trigger_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    trigger_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="executions")
    logs: Mapped[list["ExecutionLog"]] = relationship(
        "ExecutionLog", back_populates="execution", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'timeout', 'cancelled')",
            name="chk_execution_status",
        ),
        CheckConstraint(
            "completed_at IS NULL OR completed_at >= started_at",
            name="chk_completed_at_after_started",
        ),
        Index("idx_workflow_executions_workflow_id", "workflow_id"),
        Index("idx_workflow_executions_status", "status"),
        Index("idx_workflow_executions_started_at", "started_at"),
        Index("idx_workflow_executions_execution_id", "execution_id"),
        Index("idx_workflow_executions_trigger_type", "trigger_type"),
        Index(
            "idx_workflow_executions_composite",
            "workflow_id",
            "status",
            "started_at",
        ),
    )

    def __repr__(self) -> str:
        return f"<WorkflowExecution(id={self.id}, execution_id={self.execution_id}, status={self.status})>"


class WorkflowAction(Base, AuditMixin):
    """Workflow action definition model."""

    __tablename__ = "workflow_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False
    )
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    action_name: Mapped[str] = mapped_column(String(255), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    conditions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="actions")

    __table_args__ = (
        UniqueConstraint("workflow_id", "order_index", name="uq_workflow_action_order"),
        CheckConstraint("order_index >= 0", name="chk_order_index_positive"),
        Index("idx_workflow_actions_workflow_id", "workflow_id"),
        Index("idx_workflow_actions_type", "action_type"),
        Index("idx_workflow_actions_order", "workflow_id", "order_index"),
    )

    def __repr__(self) -> str:
        return f"<WorkflowAction(id={self.id}, type={self.action_type}, order={self.order_index})>"


class ExecutionLog(Base):
    """Execution log model."""

    __tablename__ = "execution_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_executions.id", ondelete="CASCADE"),
        nullable=False,
    )
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    log_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    action_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_actions.id"), nullable=True
    )
    step_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    execution: Mapped["WorkflowExecution"] = relationship(
        "WorkflowExecution", back_populates="logs"
    )

    __table_args__ = (
        CheckConstraint(
            "level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')",
            name="chk_log_level",
        ),
        Index("idx_execution_logs_execution_id", "execution_id"),
        Index("idx_execution_logs_level", "level"),
        Index("idx_execution_logs_created_at", "created_at"),
        Index(
            "idx_execution_logs_composite",
            "execution_id",
            "level",
            "created_at",
        ),
    )

    def __repr__(self) -> str:
        return f"<ExecutionLog(id={self.id}, level={self.level}, execution_id={self.execution_id})>"


class Integration(Base, AuditMixin):
    """Integration configuration model."""

    __tablename__ = "integrations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    health_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="unknown"
    )
    last_health_check: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    credentials_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    events: Mapped[list["IntegrationEvent"]] = relationship(
        "IntegrationEvent", back_populates="integration", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "type IN ('github', 'linear', 'slack', 'axolo', 'teams', 'discord', 'jira', 'sentry', 'datadog')",
            name="chk_integration_type",
        ),
        CheckConstraint(
            "health_status IN ('healthy', 'degraded', 'unhealthy', 'unknown')",
            name="chk_health_status",
        ),
        Index("idx_integrations_type", "type"),
        Index("idx_integrations_enabled", "enabled"),
        Index("idx_integrations_health", "health_status"),
    )

    def __repr__(self) -> str:
        return f"<Integration(id={self.id}, name={self.name}, type={self.type})>"


class IntegrationEvent(Base):
    """Integration event model."""

    __tablename__ = "integration_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    integration_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("integrations.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    event_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    integration: Mapped["Integration"] = relationship(
        "Integration", back_populates="events"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed', 'ignored')",
            name="chk_event_status",
        ),
        Index("idx_integration_events_integration_id", "integration_id"),
        Index("idx_integration_events_status", "status"),
        Index("idx_integration_events_type", "event_type"),
        Index("idx_integration_events_created_at", "created_at"),
        Index(
            "idx_integration_events_queue",
            "status",
            "created_at",
            postgresql_where="status IN ('pending', 'processing')",
        ),
    )

    def __repr__(self) -> str:
        return f"<IntegrationEvent(id={self.id}, type={self.event_type}, status={self.status})>"


class WorkflowTrigger(Base, AuditMixin):
    """Workflow trigger configuration model."""

    __tablename__ = "workflow_triggers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False
    )
    trigger_type: Mapped[str] = mapped_column(String(100), nullable=False)
    conditions: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="triggers")

    __table_args__ = (
        CheckConstraint(
            "trigger_type IN ('event', 'schedule', 'webhook', 'manual')",
            name="chk_trigger_type",
        ),
        Index("idx_workflow_triggers_workflow_id", "workflow_id"),
        Index("idx_workflow_triggers_type", "trigger_type"),
        Index("idx_workflow_triggers_enabled", "enabled"),
    )

    def __repr__(self) -> str:
        return f"<WorkflowTrigger(id={self.id}, type={self.trigger_type}, enabled={self.enabled})>"


class AllowedCommenter(Base, AuditMixin):
    """Allowed commenter model for PR comment filtering.
    
    Tracks users who are authorized to have their comments processed by AutoPR.
    Users can be added manually via dashboard or automatically when they first comment.
    """

    __tablename__ = "allowed_commenters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    github_username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    github_user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    added_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_comment_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    comment_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("idx_allowed_commenters_username", "github_username"),
        Index("idx_allowed_commenters_enabled", "enabled"),
        Index("idx_allowed_commenters_user_id", "github_user_id"),
    )

    def __repr__(self) -> str:
        return f"<AllowedCommenter(username={self.github_username}, enabled={self.enabled})>"


class CommentFilterSettings(Base, AuditMixin):
    """Global settings for comment filtering.
    
    Stores configuration for how PR comments should be filtered and processed.
    Only one record should exist in this table (singleton pattern).
    """

    __tablename__ = "comment_filter_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    auto_add_commenters: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    auto_reply_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    auto_reply_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="Thank you for your comment! User @{username} has been added to the allowed commenters list. "
        "Comments from this user will now be processed. You can manage this in your AutoPR dashboard."
    )
    whitelist_mode: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="When True, only allowed commenters are processed. When False, all except blocked are processed."
    )

    __table_args__ = (
        Index("idx_comment_filter_settings_enabled", "enabled"),
    )

    def __repr__(self) -> str:
        return f"<CommentFilterSettings(enabled={self.enabled}, auto_add={self.auto_add_commenters})>"


# TODO: Production enhancements
# - [ ] Add User model for authentication
# - [ ] Add Organization/Team models for multi-tenancy
# - [ ] Add APIKey model for API authentication
# - [ ] Add WebhookLog model for webhook tracking
# - [ ] Add NotificationQueue model for async notifications
# - [ ] Add ScheduledJob model for cron jobs
# - [ ] Add AuditLog model for comprehensive audit trail
# - [ ] Consider adding polymorphic models for extensibility
