# Database Schema Documentation

## Overview

AutoPR Engine uses **PostgreSQL** as the primary database with **SQLAlchemy ORM** for data management. This document provides comprehensive documentation of the database schema, relationships, indexes, and design patterns.

**Database:** PostgreSQL 14+  
**ORM:** SQLAlchemy 2.0+  
**Migrations:** Alembic  
**Last Updated:** 2025-11-22

## Table of Contents

1. [Schema Overview](#schema-overview)
2. [Core Tables](#core-tables)
3. [Entity Relationship Diagram](#entity-relationship-diagram)
4. [Table Definitions](#table-definitions)
5. [Indexes & Performance](#indexes--performance)
6. [Constraints & Validation](#constraints--validation)
7. [Relationships](#relationships)
8. [JSON Fields](#json-fields)
9. [Audit Fields](#audit-fields)
10. [Migration Guide](#migration-guide)
11. [Best Practices](#best-practices)

---

## Schema Overview

### Database Name
- **Development:** `autopr_dev`
- **Staging:** `autopr_staging`
- **Production:** `autopr_prod`

### Tables Summary

| Table | Purpose | Row Est. | Primary Key | Foreign Keys |
|-------|---------|----------|-------------|--------------|
| `workflows` | Workflow definitions | 1K-10K | UUID | - |
| `workflow_executions` | Execution tracking | 100K-1M | UUID | workflows.id |
| `workflow_actions` | Action definitions | 5K-50K | UUID | workflows.id |
| `workflow_triggers` | Trigger configuration | 1K-10K | UUID | workflows.id |
| `execution_logs` | Execution logs | 1M-10M+ | UUID | workflow_executions.id, workflow_actions.id |
| `integrations` | Integration config | 10-100 | UUID | - |
| `integration_events` | Integration events | 100K-1M | UUID | integrations.id |

**Total Tables:** 7  
**Total Indexes:** 35+ (including constraints)  
**Estimated Storage:** 10GB-100GB (production)

---

## Core Tables

### 1. workflows

**Purpose:** Stores workflow definitions and configurations

**Columns:**
- `id` (UUID, PK) - Unique workflow identifier
- `name` (VARCHAR(255), UNIQUE) - Workflow name
- `description` (TEXT, NULL) - Optional description
- `status` (VARCHAR(50)) - Workflow status: 'active', 'inactive', 'archived', 'draft'
- `config` (JSONB) - Workflow configuration
- `created_by` (VARCHAR(255), NULL) - Creator identifier
- `created_at` (TIMESTAMP WITH TIME ZONE) - Creation timestamp
- `updated_at` (TIMESTAMP WITH TIME ZONE) - Last update timestamp

**Indexes:**
- PRIMARY KEY: `id`
- UNIQUE: `name`
- INDEX: `idx_workflows_status` on `status`
- INDEX: `idx_workflows_created_at` on `created_at`
- GIN INDEX: `idx_workflows_config` on `config` (for JSON queries)

**Constraints:**
- CHECK: `status IN ('active', 'inactive', 'archived', 'draft')`

**Example:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Deploy to Production",
  "description": "Automated production deployment workflow",
  "status": "active",
  "config": {
    "max_retries": 3,
    "timeout_seconds": 3600,
    "notification_channels": ["slack", "email"]
  },
  "created_by": "user-123",
  "created_at": "2025-11-22T10:00:00Z",
  "updated_at": "2025-11-22T15:30:00Z"
}
```

---

### 2. workflow_executions

**Purpose:** Tracks individual workflow executions with status and results

**Columns:**
- `id` (UUID, PK) - Unique execution record ID
- `workflow_id` (UUID, FK -> workflows.id) - Parent workflow
- `execution_id` (VARCHAR(255), UNIQUE) - Human-readable execution ID
- `status` (VARCHAR(50)) - Execution status: 'pending', 'running', 'completed', 'failed', 'timeout', 'cancelled'
- `started_at` (TIMESTAMP WITH TIME ZONE) - Execution start time
- `completed_at` (TIMESTAMP WITH TIME ZONE, NULL) - Execution completion time
- `result` (JSONB, NULL) - Execution result data
- `error_message` (TEXT, NULL) - Error details if failed
- `retry_count` (INTEGER) - Number of retry attempts
- `parent_execution_id` (UUID, NULL, FK -> workflow_executions.id) - Parent execution for retries
- `trigger_type` (VARCHAR(100), NULL) - How workflow was triggered
- `trigger_data` (JSONB, NULL) - Trigger context data

**Indexes:**
- PRIMARY KEY: `id`
- UNIQUE: `execution_id`
- INDEX: `idx_workflow_executions_workflow_id` on `workflow_id`
- INDEX: `idx_workflow_executions_status` on `status`
- INDEX: `idx_workflow_executions_started_at` on `started_at`
- INDEX: `idx_workflow_executions_trigger_type` on `trigger_type`
- COMPOSITE INDEX: `idx_workflow_executions_composite` on `(workflow_id, status, started_at)`

**Constraints:**
- CHECK: `status IN ('pending', 'running', 'completed', 'failed', 'timeout', 'cancelled')`
- CHECK: `completed_at IS NULL OR completed_at >= started_at`
- FOREIGN KEY: `workflow_id` REFERENCES `workflows(id)` ON DELETE CASCADE
- FOREIGN KEY: `parent_execution_id` REFERENCES `workflow_executions(id)`

**Example:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "execution_id": "exec-20251122-150000-abc123",
  "status": "completed",
  "started_at": "2025-11-22T15:00:00Z",
  "completed_at": "2025-11-22T15:05:30Z",
  "result": {
    "deployed_version": "v1.2.3",
    "deployment_url": "https://prod.example.com"
  },
  "error_message": null,
  "retry_count": 0,
  "parent_execution_id": null,
  "trigger_type": "manual",
  "trigger_data": {"triggered_by": "user-123"}
}
```

---

### 3. workflow_actions

**Purpose:** Defines actions/steps within workflows

**Columns:**
- `id` (UUID, PK) - Unique action ID
- `workflow_id` (UUID, FK -> workflows.id) - Parent workflow
- `action_type` (VARCHAR(100)) - Type of action (e.g., 'deploy', 'notify', 'test')
- `action_name` (VARCHAR(255)) - Human-readable action name
- `config` (JSONB) - Action-specific configuration
- `order_index` (INTEGER) - Execution order within workflow
- `conditions` (JSONB, NULL) - Conditional execution logic
- `created_at` (TIMESTAMP WITH TIME ZONE) - Creation timestamp
- `updated_at` (TIMESTAMP WITH TIME ZONE) - Last update timestamp

**Indexes:**
- PRIMARY KEY: `id`
- INDEX: `idx_workflow_actions_workflow_id` on `workflow_id`
- INDEX: `idx_workflow_actions_type` on `action_type`
- COMPOSITE INDEX: `idx_workflow_actions_order` on `(workflow_id, order_index)`

**Constraints:**
- UNIQUE: `(workflow_id, order_index)` - No duplicate order within workflow
- CHECK: `order_index >= 0`
- FOREIGN KEY: `workflow_id` REFERENCES `workflows(id)` ON DELETE CASCADE

**Example:**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "action_type": "deploy",
  "action_name": "Deploy to Kubernetes",
  "config": {
    "cluster": "prod-us-east",
    "namespace": "production",
    "image": "autopr:v1.2.3"
  },
  "order_index": 0,
  "conditions": {
    "branch": "main",
    "environment": "production"
  },
  "created_at": "2025-11-22T10:00:00Z",
  "updated_at": "2025-11-22T10:00:00Z"
}
```

---

### 4. execution_logs

**Purpose:** Stores detailed logs for workflow executions

**Columns:**
- `id` (UUID, PK) - Unique log entry ID
- `execution_id` (UUID, FK -> workflow_executions.id) - Parent execution
- `level` (VARCHAR(20)) - Log level: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
- `message` (TEXT) - Log message
- `log_metadata` (JSONB, NULL) - Additional structured log data
- `action_id` (UUID, NULL, FK -> workflow_actions.id) - Related action
- `step_name` (VARCHAR(255), NULL) - Step name for organization
- `created_at` (TIMESTAMP WITH TIME ZONE) - Log entry timestamp

**Indexes:**
- PRIMARY KEY: `id`
- INDEX: `idx_execution_logs_execution_id` on `execution_id`
- INDEX: `idx_execution_logs_level` on `level`
- INDEX: `idx_execution_logs_created_at` on `created_at`
- COMPOSITE INDEX: `idx_execution_logs_composite` on `(execution_id, level, created_at)`

**Constraints:**
- CHECK: `level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')`
- FOREIGN KEY: `execution_id` REFERENCES `workflow_executions(id)` ON DELETE CASCADE
- FOREIGN KEY: `action_id` REFERENCES `workflow_actions(id)`

**Example:**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "execution_id": "660e8400-e29b-41d4-a716-446655440000",
  "level": "INFO",
  "message": "Deployment started successfully",
  "log_metadata": {
    "cluster": "prod-us-east",
    "pods_deployed": 5
  },
  "action_id": "770e8400-e29b-41d4-a716-446655440000",
  "step_name": "deploy_kubernetes",
  "created_at": "2025-11-22T15:01:00Z"
}
```

---

### 5. integrations

**Purpose:** Configuration for external service integrations

**Columns:**
- `id` (UUID, PK) - Unique integration ID
- `name` (VARCHAR(255), UNIQUE) - Integration name
- `type` (VARCHAR(100)) - Integration type: 'github', 'linear', 'slack', 'axolo', 'teams', 'discord', 'jira', 'sentry', 'datadog'
- `config` (JSONB) - Integration-specific configuration
- `enabled` (BOOLEAN) - Whether integration is active
- `health_status` (VARCHAR(50)) - Health status: 'healthy', 'degraded', 'unhealthy', 'unknown'
- `last_health_check` (TIMESTAMP WITH TIME ZONE, NULL) - Last health check time
- `credentials_encrypted` (TEXT, NULL) - Encrypted credentials
- `created_at` (TIMESTAMP WITH TIME ZONE) - Creation timestamp
- `updated_at` (TIMESTAMP WITH TIME ZONE) - Last update timestamp

**Indexes:**
- PRIMARY KEY: `id`
- UNIQUE: `name`
- INDEX: `idx_integrations_type` on `type`
- INDEX: `idx_integrations_enabled` on `enabled`
- INDEX: `idx_integrations_health` on `health_status`

**Constraints:**
- CHECK: `type IN ('github', 'linear', 'slack', 'axolo', 'teams', 'discord', 'jira', 'sentry', 'datadog')`
- CHECK: `health_status IN ('healthy', 'degraded', 'unhealthy', 'unknown')`

**Example:**
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440000",
  "name": "Production Slack",
  "type": "slack",
  "config": {
    "webhook_url": "https://hooks.slack.com/...",
    "channel": "#deployments",
    "mention_on_failure": true
  },
  "enabled": true,
  "health_status": "healthy",
  "last_health_check": "2025-11-22T15:00:00Z",
  "credentials_encrypted": "encrypted_data_here",
  "created_at": "2025-11-01T10:00:00Z",
  "updated_at": "2025-11-22T15:00:00Z"
}
```

---

### 6. integration_events

**Purpose:** Queue and track events from external integrations

**Columns:**
- `id` (UUID, PK) - Unique event ID
- `integration_id` (UUID, FK -> integrations.id) - Source integration
- `event_type` (VARCHAR(100)) - Type of event
- `event_id` (VARCHAR(255), NULL) - External event identifier
- `payload` (JSONB) - Event payload data
- `status` (VARCHAR(50)) - Processing status: 'pending', 'processing', 'completed', 'failed', 'ignored'
- `processed_at` (TIMESTAMP WITH TIME ZONE, NULL) - Processing completion time
- `error_message` (TEXT, NULL) - Error details if failed
- `retry_count` (INTEGER) - Number of retry attempts
- `created_at` (TIMESTAMP WITH TIME ZONE) - Event received timestamp

**Indexes:**
- PRIMARY KEY: `id`
- INDEX: `idx_integration_events_integration_id` on `integration_id`
- INDEX: `idx_integration_events_status` on `status`
- INDEX: `idx_integration_events_type` on `event_type`
- INDEX: `idx_integration_events_created_at` on `created_at`
- PARTIAL INDEX: `idx_integration_events_queue` on `(status, created_at)` WHERE `status IN ('pending', 'processing')`

**Constraints:**
- CHECK: `status IN ('pending', 'processing', 'completed', 'failed', 'ignored')`
- FOREIGN KEY: `integration_id` REFERENCES `integrations(id)` ON DELETE CASCADE

**Example:**
```json
{
  "id": "aa0e8400-e29b-41d4-a716-446655440000",
  "integration_id": "990e8400-e29b-41d4-a716-446655440000",
  "event_type": "deployment.completed",
  "event_id": "gh-123456",
  "payload": {
    "repository": "codeflow-engine",
    "branch": "main",
    "commit_sha": "abc123def456"
  },
  "status": "completed",
  "processed_at": "2025-11-22T15:05:30Z",
  "error_message": null,
  "retry_count": 0,
  "created_at": "2025-11-22T15:05:00Z"
}
```

---

### 7. workflow_triggers

**Purpose:** Configuration for workflow triggers

**Columns:**
- `id` (UUID, PK) - Unique trigger ID
- `workflow_id` (UUID, FK -> workflows.id) - Parent workflow
- `trigger_type` (VARCHAR(100)) - Trigger type: 'event', 'schedule', 'webhook', 'manual'
- `conditions` (JSONB) - Trigger conditions
- `enabled` (BOOLEAN) - Whether trigger is active
- `created_at` (TIMESTAMP WITH TIME ZONE) - Creation timestamp
- `updated_at` (TIMESTAMP WITH TIME ZONE) - Last update timestamp

**Indexes:**
- PRIMARY KEY: `id`
- INDEX: `idx_workflow_triggers_workflow_id` on `workflow_id`
- INDEX: `idx_workflow_triggers_type` on `trigger_type`
- INDEX: `idx_workflow_triggers_enabled` on `enabled`

**Constraints:**
- CHECK: `trigger_type IN ('event', 'schedule', 'webhook', 'manual')`
- FOREIGN KEY: `workflow_id` REFERENCES `workflows(id)` ON DELETE CASCADE

**Example:**
```json
{
  "id": "bb0e8400-e29b-41d4-a716-446655440000",
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "trigger_type": "event",
  "conditions": {
    "event_type": "pull_request.merged",
    "branches": ["main"],
    "paths": ["src/**"]
  },
  "enabled": true,
  "created_at": "2025-11-01T10:00:00Z",
  "updated_at": "2025-11-01T10:00:00Z"
}
```

---

## Entity Relationship Diagram

```
┌─────────────────────┐
│     workflows       │
│ ─────────────────── │
│ PK id (UUID)        │
│    name (VARCHAR)   │
│    status (VARCHAR) │
│    config (JSONB)   │
└──────────┬──────────┘
           │
           │ 1:N
           ├──────────────────────────┐
           │                          │
           ▼                          ▼
┌──────────────────────┐   ┌─────────────────────┐
│  workflow_executions │   │   workflow_actions  │
│ ──────────────────── │   │ ─────────────────── │
│ PK id (UUID)         │   │ PK id (UUID)        │
│ FK workflow_id       │   │ FK workflow_id      │
│    execution_id      │   │    action_type      │
│    status (VARCHAR)  │   │    order_index      │
│    result (JSONB)    │   │    config (JSONB)   │
└──────────┬───────────┘   └──────────┬──────────┘
           │                          │
           │ 1:N                      │
           ▼                          │ (FK)
┌──────────────────────┐              │
│   execution_logs     │◄─────────────┘
│ ──────────────────── │
│ PK id (UUID)         │
│ FK execution_id      │
│ FK action_id         │
│    level (VARCHAR)   │
│    message (TEXT)    │
└──────────────────────┘

           │ 1:N
           ▼
┌──────────────────────┐
│   workflow_triggers  │
│ ──────────────────── │
│ PK id (UUID)         │
│ FK workflow_id       │
│    trigger_type      │
│    conditions (JSONB)│
└──────────────────────┘

┌─────────────────────┐
│   integrations      │
│ ─────────────────── │
│ PK id (UUID)        │
│    name (VARCHAR)   │
│    type (VARCHAR)   │
│    enabled (BOOL)   │
└──────────┬──────────┘
           │
           │ 1:N
           ▼
┌──────────────────────┐
│ integration_events   │
│ ──────────────────── │
│ PK id (UUID)         │
│ FK integration_id    │
│    event_type        │
│    payload (JSONB)   │
│    status (VARCHAR)  │
└──────────────────────┘
```

---

## Indexes & Performance

### Index Strategy

All tables have been optimized with indexes for common query patterns:

1. **Primary Key Indexes** - Automatic on all UUID primary keys
2. **Foreign Key Indexes** - On all foreign key columns for JOIN performance
3. **Status Indexes** - For filtering by workflow/execution/event status
4. **Timestamp Indexes** - For time-range queries and sorting
5. **Composite Indexes** - For multi-column queries (workflow_id + status + created_at)
6. **Partial Indexes** - For queuing systems (only index pending/processing events)
7. **GIN Indexes** - For JSONB column searches (config, payload)

### Query Performance

Expected query performance with proper indexes:

| Query Type | Row Count | Expected Time | Index Used |
|------------|-----------|---------------|------------|
| Get workflow by ID | 1 | <1ms | PK |
| List workflows by status | 100-1K | <10ms | idx_workflows_status |
| Get execution by execution_id | 1 | <1ms | UNIQUE idx |
| List executions for workflow | 100-1K | <20ms | idx_workflow_executions_workflow_id |
| Get logs for execution | 1K-10K | <100ms | idx_execution_logs_execution_id |
| Get pending events | 100-1K | <20ms | idx_integration_events_queue (partial) |
| JSON config search | varies | <100ms | idx_workflows_config (GIN) |

---

## Constraints & Validation

### Check Constraints

All ENUM-like fields use CHECK constraints for data integrity:

```sql
-- Workflow status validation
ALTER TABLE workflows ADD CONSTRAINT chk_workflow_status 
  CHECK (status IN ('active', 'inactive', 'archived', 'draft'));

-- Execution status validation
ALTER TABLE workflow_executions ADD CONSTRAINT chk_execution_status 
  CHECK (status IN ('pending', 'running', 'completed', 'failed', 'timeout', 'cancelled'));

-- Logical constraint: completion time must be after start time
ALTER TABLE workflow_executions ADD CONSTRAINT chk_completed_at_after_started 
  CHECK (completed_at IS NULL OR completed_at >= started_at);

-- Order index must be non-negative
ALTER TABLE workflow_actions ADD CONSTRAINT chk_order_index_positive 
  CHECK (order_index >= 0);
```

### Unique Constraints

```sql
-- Workflow name must be unique
ALTER TABLE workflows ADD CONSTRAINT uq_workflow_name UNIQUE (name);

-- Execution ID must be unique (human-readable identifier)
ALTER TABLE workflow_executions ADD CONSTRAINT uq_execution_id UNIQUE (execution_id);

-- Action order must be unique within workflow
ALTER TABLE workflow_actions ADD CONSTRAINT uq_workflow_action_order 
  UNIQUE (workflow_id, order_index);

-- Integration name must be unique
ALTER TABLE integrations ADD CONSTRAINT uq_integration_name UNIQUE (name);
```

### Foreign Key Cascade

All foreign keys use appropriate CASCADE rules:

- **ON DELETE CASCADE**: Child records deleted when parent is deleted
  - `workflow_executions.workflow_id`
  - `workflow_actions.workflow_id`
  - `workflow_triggers.workflow_id`
  - `execution_logs.execution_id`
  - `integration_events.integration_id`

---

## Relationships

### One-to-Many Relationships

1. **Workflow → Workflow Executions**
   - One workflow can have many executions
   - Cascade delete: Delete workflow → Delete all executions

2. **Workflow → Workflow Actions**
   - One workflow can have many actions/steps
   - Cascade delete: Delete workflow → Delete all actions

3. **Workflow → Workflow Triggers**
   - One workflow can have many triggers
   - Cascade delete: Delete workflow → Delete all triggers

4. **Workflow Execution → Execution Logs**
   - One execution can have many log entries
   - Cascade delete: Delete execution → Delete all logs

5. **Integration → Integration Events**
   - One integration can have many events
   - Cascade delete: Delete integration → Delete all events

### Self-Referencing Relationships

1. **Workflow Execution → Parent Execution**
   - For tracking retry attempts
   - `parent_execution_id` references `workflow_executions.id`
   - NULL for original executions

---

## JSON Fields

### JSONB Column Usage

Several tables use JSONB columns for flexible configuration and data storage:

1. **workflows.config** - Workflow-level settings
   ```json
   {
     "max_retries": 3,
     "timeout_seconds": 3600,
     "notification_channels": ["slack", "email"],
     "auto_rollback": true
   }
   ```

2. **workflow_executions.result** - Execution output
   ```json
   {
     "deployed_version": "v1.2.3",
     "deployment_url": "https://prod.example.com",
     "artifacts": ["build.tar.gz", "logs.txt"]
   }
   ```

3. **workflow_actions.config** - Action-specific configuration
   ```json
   {
     "cluster": "prod-us-east",
     "namespace": "production",
     "replicas": 3
   }
   ```

4. **integration_events.payload** - Event data from external systems
   ```json
   {
     "repository": "codeflow-engine",
     "pull_request_number": 123,
     "author": "user@example.com"
   }
   ```

### GIN Index for JSON Queries

GIN indexes enable efficient JSON queries:

```sql
-- Query workflows by JSON config field
SELECT * FROM workflows 
WHERE config @> '{"notification_channels": ["slack"]}';

-- Query by nested JSON path
SELECT * FROM workflows 
WHERE config -> 'settings' ->> 'auto_deploy' = 'true';
```

---

## Audit Fields

### AuditMixin Pattern

Common audit fields across multiple tables:

```python
class AuditMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
```

**Tables with AuditMixin:**
- `workflows`
- `workflow_actions`
- `workflow_triggers`
- `integrations`

**Benefits:**
- Automatic timestamp management
- Track creation and modification times
- No manual timestamp updates required

---

## Migration Guide

### Alembic Configuration

AutoPR Engine uses Alembic for database migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# Check current version
alembic current
```

### Example Migration

```python
# migrations/versions/001_initial_schema.py

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Create workflows table
    op.create_table(
        'workflows',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), unique=True, nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('config', postgresql.JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    # Create index
    op.create_index('idx_workflows_status', 'workflows', ['status'])

def downgrade():
    op.drop_index('idx_workflows_status')
    op.drop_table('workflows')
```

---

## Best Practices

### 1. UUID Usage

✅ **DO:** Use UUIDs for primary keys
```python
id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
)
```

❌ **DON'T:** Use auto-incrementing integers (security risk, distributed system issues)

### 2. Timestamp Handling

✅ **DO:** Always use timezone-aware timestamps
```python
created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), 
    default=lambda: datetime.now(timezone.utc)
)
```

❌ **DON'T:** Use naive datetime objects

### 3. JSON Field Validation

✅ **DO:** Validate JSON schemas at application level
```python
from pydantic import BaseModel

class WorkflowConfig(BaseModel):
    max_retries: int = 3
    timeout_seconds: int = 3600

# Before saving
config = WorkflowConfig(**config_dict).dict()
```

❌ **DON'T:** Store unvalidated JSON in database

### 4. Foreign Key Cascades

✅ **DO:** Use appropriate CASCADE rules
```python
workflow_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), 
    ForeignKey("workflows.id", ondelete="CASCADE")
)
```

❌ **DON'T:** Leave orphaned records in database

### 5. Index Strategy

✅ **DO:** Create indexes for frequent queries
```sql
CREATE INDEX idx_workflow_executions_composite 
ON workflow_executions(workflow_id, status, started_at);
```

❌ **DON'T:** Over-index (every index has write cost)

### 6. Soft Deletes (Future Enhancement)

**TODO:** Implement soft delete pattern for audit trail:
```python
is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
deleted_at: Mapped[Optional[datetime]] = mapped_column(
    DateTime(timezone=True), nullable=True
)
```

---

## Future Enhancements

### Planned Tables

From `models.py` TODO comments:

1. **User** - User authentication and profiles
2. **Organization/Team** - Multi-tenancy support
3. **APIKey** - API key management
4. **WebhookLog** - Webhook event tracking
5. **NotificationQueue** - Async notification delivery
6. **ScheduledJob** - Cron job management
7. **AuditLog** - Comprehensive audit trail

### Performance Optimization

1. **Partitioning** - Table partitioning for `execution_logs` (by month)
2. **Archival** - Move old execution data to archive tables
3. **Read Replicas** - Separate read queries from write queries
4. **Caching** - Redis cache for frequently accessed workflows

---

## Troubleshooting

### Connection Pool Exhausted

**Problem:** "QueuePool limit of size X overflow Y reached"

**Solution:** See [Database Optimization Guide](./DATABASE_OPTIMIZATION_GUIDE.md)

### Slow Queries

**Problem:** Queries taking >1 second

**Solution:**
```sql
-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM workflow_executions 
WHERE workflow_id = '...' AND status = 'running';

-- Check missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE tablename = 'workflow_executions';
```

### Migration Conflicts

**Problem:** Alembic migration conflicts

**Solution:**
```bash
# Check current state
alembic current

# Stamp database with specific revision
alembic stamp head

# Re-run migrations
alembic upgrade head
```

---

## References

- [Database Optimization Guide](./DATABASE_OPTIMIZATION_GUIDE.md)
- [Deployment Playbook](./DEPLOYMENT_PLAYBOOK.md)
- [API Reference](./API_REFERENCE.md)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

**Document Status:** ✅ Complete  
**DOC-2 Status:** ✅ **RESOLVED** - Comprehensive database schema documented  
**Last Updated:** 2025-11-22  
**Version:** 1.0.0  
**Maintained by:** AutoPR DevOps Team
