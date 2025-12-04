"""Initial schema

Revision ID: 8f7f9c9512ec
Revises: 
Create Date: 2025-11-20 21:33:51.797622

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8f7f9c9512ec'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - create all tables with UUID PKs matching ORM models."""
    
    # Create workflows table
    op.create_table(
        'workflows',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('config', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("status IN ('active', 'inactive', 'archived', 'draft')", name='chk_workflow_status'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_workflows_status', 'workflows', ['status'])
    op.create_index('idx_workflows_created_at', 'workflows', ['created_at'])
    op.create_index('idx_workflows_config', 'workflows', ['config'], postgresql_using='gin')
    
    # Create workflow_executions table
    op.create_table(
        'workflow_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('execution_id', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('parent_execution_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('trigger_type', sa.String(length=100), nullable=True),
        sa.Column('trigger_data', sa.JSON(), nullable=True),
        sa.CheckConstraint("status IN ('pending', 'running', 'completed', 'failed', 'timeout', 'cancelled')", name='chk_execution_status'),
        sa.CheckConstraint('completed_at IS NULL OR completed_at >= started_at', name='chk_completed_at_after_started'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_execution_id'], ['workflow_executions.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('execution_id')
    )
    op.create_index('idx_workflow_executions_workflow_id', 'workflow_executions', ['workflow_id'])
    op.create_index('idx_workflow_executions_status', 'workflow_executions', ['status'])
    op.create_index('idx_workflow_executions_started_at', 'workflow_executions', ['started_at'])
    op.create_index('idx_workflow_executions_execution_id', 'workflow_executions', ['execution_id'])
    op.create_index('idx_workflow_executions_trigger_type', 'workflow_executions', ['trigger_type'])
    op.create_index('idx_workflow_executions_composite', 'workflow_executions', ['workflow_id', 'status', 'started_at'])
    
    # Create workflow_actions table
    op.create_table(
        'workflow_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('action_name', sa.String(length=255), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('conditions', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint('order_index >= 0', name='chk_order_index_positive'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workflow_id', 'order_index', name='uq_workflow_action_order')
    )
    op.create_index('idx_workflow_actions_workflow_id', 'workflow_actions', ['workflow_id'])
    op.create_index('idx_workflow_actions_type', 'workflow_actions', ['action_type'])
    op.create_index('idx_workflow_actions_order', 'workflow_actions', ['workflow_id', 'order_index'])
    
    # Create execution_logs table
    op.create_table(
        'execution_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('execution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('level', sa.String(length=20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('log_metadata', sa.JSON(), nullable=True),
        sa.Column('action_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('step_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')", name='chk_log_level'),
        sa.ForeignKeyConstraint(['execution_id'], ['workflow_executions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['action_id'], ['workflow_actions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_execution_logs_execution_id', 'execution_logs', ['execution_id'])
    op.create_index('idx_execution_logs_level', 'execution_logs', ['level'])
    op.create_index('idx_execution_logs_created_at', 'execution_logs', ['created_at'])
    op.create_index('idx_execution_logs_composite', 'execution_logs', ['execution_id', 'level', 'created_at'])
    
    # Create integrations table
    op.create_table(
        'integrations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('health_status', sa.String(length=50), nullable=False, server_default='unknown'),
        sa.Column('last_health_check', sa.DateTime(timezone=True), nullable=True),
        sa.Column('credentials_encrypted', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("type IN ('github', 'linear', 'slack', 'axolo', 'teams', 'discord', 'jira', 'sentry', 'datadog')", name='chk_integration_type'),
        sa.CheckConstraint("health_status IN ('healthy', 'degraded', 'unhealthy', 'unknown')", name='chk_health_status'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_integrations_type', 'integrations', ['type'])
    op.create_index('idx_integrations_enabled', 'integrations', ['enabled'])
    op.create_index('idx_integrations_health', 'integrations', ['health_status'])
    
    # Create integration_events table
    op.create_table(
        'integration_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('integration_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('event_id', sa.String(length=255), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed', 'ignored')", name='chk_event_status'),
        sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_integration_events_integration_id', 'integration_events', ['integration_id'])
    op.create_index('idx_integration_events_status', 'integration_events', ['status'])
    op.create_index('idx_integration_events_type', 'integration_events', ['event_type'])
    op.create_index('idx_integration_events_created_at', 'integration_events', ['created_at'])
    op.create_index('idx_integration_events_queue', 'integration_events', ['status', 'created_at'], 
                    postgresql_where=sa.text("status IN ('pending', 'processing')"))
    
    # Create workflow_triggers table
    op.create_table(
        'workflow_triggers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trigger_type', sa.String(length=100), nullable=False),
        sa.Column('conditions', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("trigger_type IN ('event', 'schedule', 'webhook', 'manual')", name='chk_trigger_type'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_workflow_triggers_workflow_id', 'workflow_triggers', ['workflow_id'])
    op.create_index('idx_workflow_triggers_type', 'workflow_triggers', ['trigger_type'])
    op.create_index('idx_workflow_triggers_enabled', 'workflow_triggers', ['enabled'])


def downgrade() -> None:
    """Downgrade schema - drop all tables in reverse order."""
    op.drop_table('workflow_triggers')
    op.drop_table('integration_events')
    op.drop_table('integrations')
    op.drop_table('execution_logs')
    op.drop_table('workflow_actions')
    op.drop_table('workflow_executions')
    op.drop_table('workflows')
