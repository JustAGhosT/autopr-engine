# Database Optimization Guide

**Version:** 1.0  
**Last Updated:** 2025-11-22  
**Status:** Production Implementation Guide

---

## Overview

This guide documents database optimization strategies, connection pooling configuration, indexing strategy, and performance tuning for AutoPR Engine's PostgreSQL and SQLite backends.

---

## Table of Contents

1. [Connection Pooling](#connection-pooling)
2. [Index Strategy](#index-strategy)
3. [Query Optimization](#query-optimization)
4. [Performance Monitoring](#performance-monitoring)
5. [Backup & Recovery](#backup--recovery)
6. [Troubleshooting](#troubleshooting)

---

## Connection Pooling

### Current Implementation ✅

AutoPR Engine uses SQLAlchemy's QueuePool for production environments with configurable parameters:

```python
# autopr/database/config.py
POOL_CONFIG = {
    "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),          # Base connections
    "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),    # Additional under load
    "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),    # Wait time (seconds)
    "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),  # Recycle every hour
    "pool_pre_ping": True,                                       # Health checks enabled
}
```

### Environment Configuration

**Development:**
```bash
export DB_POOL_SIZE=5
export DB_MAX_OVERFLOW=10
export DB_POOL_TIMEOUT=30
export DB_POOL_RECYCLE=3600
```

**Production:**
```bash
export DB_POOL_SIZE=20
export DB_MAX_OVERFLOW=40
export DB_POOL_TIMEOUT=30
export DB_POOL_RECYCLE=3600
export DB_ECHO=false  # Disable SQL logging in production
```

**Testing:**
```bash
export ENVIRONMENT=test  # Uses NullPool automatically
```

### Pool Sizing Guidelines

**Formula:** `pool_size + max_overflow = total_connections`

**Recommended Sizing:**

| Environment | Workers | Pool Size | Max Overflow | Total |
|-------------|---------|-----------|--------------|-------|
| Development | 1-2     | 5         | 10           | 15    |
| Staging     | 4-8     | 10        | 20           | 30    |
| Production  | 10-20   | 20        | 40           | 60    |
| High Load   | 20+     | 30        | 50           | 80    |

**Calculation:**
- `pool_size` = (workers * 2) + buffer
- `max_overflow` = pool_size * 2
- Monitor and adjust based on actual usage

### Connection Lifecycle

**Pool Pre-Ping (Enabled):**
- Verifies connections before checkout
- Prevents "server has gone away" errors
- Adds minimal overhead (<1ms)

**Pool Recycle (3600s):**
- Recycles connections every hour
- Prevents stale connections
- Recommended for cloud databases

**Connection Timeout (30s):**
- Maximum wait time for connection
- Raises timeout error if pool exhausted
- Tune based on request patterns

### Monitoring Connection Pool

**Check Pool Status:**
```python
from codeflow_engine.database import engine

# Get pool statistics
pool = engine.pool
print(f"Pool size: {pool.size()}")
print(f"Checked out: {pool.checkedin()}")
print(f"Overflow: {pool.overflow()}")
print(f"Queue size: {pool._queue.qsize() if hasattr(pool, '_queue') else 'N/A'}")
```

**PostgreSQL Connection Monitoring:**
```sql
-- Check active connections
SELECT 
    count(*),
    state,
    application_name
FROM pg_stat_activity
WHERE datname = 'autopr_db'
GROUP BY state, application_name;

-- Check connection limits
SELECT 
    setting::int AS max_connections
FROM pg_settings
WHERE name = 'max_connections';

-- Kill idle connections (if needed)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE 
    datname = 'autopr_db'
    AND state = 'idle'
    AND NOW() - query_start > interval '10 minutes';
```

---

## Index Strategy

### Current Indexes ✅

AutoPR Engine implements comprehensive indexing strategy across all tables:

#### Workflows Table
```sql
CREATE INDEX idx_workflows_status ON workflows(status);
CREATE INDEX idx_workflows_created_at ON workflows(created_at);
CREATE INDEX idx_workflows_config ON workflows USING GIN(config);  -- PostgreSQL only
```

#### Workflow Executions Table
```sql
CREATE INDEX idx_workflow_executions_workflow_id ON workflow_executions(workflow_id);
CREATE INDEX idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX idx_workflow_executions_started_at ON workflow_executions(started_at);
CREATE INDEX idx_workflow_executions_execution_id ON workflow_executions(execution_id);
CREATE INDEX idx_workflow_executions_trigger_type ON workflow_executions(trigger_type);
CREATE INDEX idx_workflow_executions_composite ON workflow_executions(workflow_id, status, started_at);
```

#### Execution Logs Table
```sql
CREATE INDEX idx_execution_logs_execution_id ON execution_logs(execution_id);
CREATE INDEX idx_execution_logs_level ON execution_logs(level);
CREATE INDEX idx_execution_logs_timestamp ON execution_logs(timestamp);
```

#### Integrations Table
```sql
CREATE INDEX idx_integrations_type ON integrations(type);
CREATE INDEX idx_integrations_status ON integrations(status);
```

#### Integration Events Table
```sql
CREATE INDEX idx_integration_events_integration_id ON integration_events(integration_id);
CREATE INDEX idx_integration_events_event_type ON integration_events(event_type);
CREATE INDEX idx_integration_events_timestamp ON integration_events(timestamp);
CREATE INDEX idx_integration_events_composite ON integration_events(integration_id, timestamp);
```

### Index Usage Analysis

**PostgreSQL:**
```sql
-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Find unused indexes
SELECT 
    schemaname,
    tablename,
    indexname
FROM pg_stat_user_indexes
WHERE idx_scan = 0
    AND schemaname = 'public'
    AND indexname NOT LIKE 'pk_%';

-- Check index size
SELECT
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Index Best Practices

**When to Add Indexes:**
- ✅ Foreign keys (already indexed)
- ✅ Frequently filtered columns (status, type)
- ✅ Columns in JOIN conditions
- ✅ Columns in ORDER BY/GROUP BY
- ✅ Composite indexes for common query patterns

**When NOT to Add Indexes:**
- ❌ Tables with < 1000 rows
- ❌ Columns with low cardinality (few distinct values)
- ❌ Columns rarely used in WHERE clauses
- ❌ Write-heavy tables (indexes slow down INSERTs)

**Composite Index Order:**
```sql
-- ✅ Good: Most selective column first
CREATE INDEX idx_exec_status_workflow ON workflow_executions(status, workflow_id);

-- ❌ Bad: Less selective column first
CREATE INDEX idx_exec_workflow_status ON workflow_executions(workflow_id, status);
```

---

## Query Optimization

### Common Query Patterns

#### 1. Get Active Workflows
```python
# ✅ Optimized (uses idx_workflows_status)
workflows = session.query(Workflow).filter(
    Workflow.status == 'active'
).order_by(Workflow.created_at.desc()).limit(100).all()

# ❌ Not optimized (loads all, then filters in Python)
workflows = session.query(Workflow).all()
active = [w for w in workflows if w.status == 'active']
```

#### 2. Get Recent Executions for Workflow
```python
# ✅ Optimized (uses composite index)
executions = session.query(WorkflowExecution).filter(
    WorkflowExecution.workflow_id == workflow_id,
    WorkflowExecution.status == 'completed'
).order_by(WorkflowExecution.started_at.desc()).limit(50).all()
```

#### 3. Get Execution with Logs (N+1 Query Problem)
```python
# ❌ N+1 queries (bad)
executions = session.query(WorkflowExecution).all()
for execution in executions:
    logs = execution.logs  # Triggers separate query

# ✅ Eager loading (single query with JOIN)
from sqlalchemy.orm import joinedload

executions = session.query(WorkflowExecution).options(
    joinedload(WorkflowExecution.logs)
).all()
```

#### 4. Aggregate Queries
```python
from sqlalchemy import func

# ✅ Database aggregation (fast)
stats = session.query(
    func.count(WorkflowExecution.id).label('total'),
    func.avg(
        func.extract('epoch', WorkflowExecution.completed_at - WorkflowExecution.started_at)
    ).label('avg_duration')
).filter(
    WorkflowExecution.status == 'completed'
).first()
```

### Query Performance Tips

**Use EXPLAIN ANALYZE:**
```python
from sqlalchemy import text

# Get query execution plan
query = session.query(Workflow).filter(Workflow.status == 'active')
explain = session.execute(
    text("EXPLAIN ANALYZE " + str(query.statement.compile(
        dialect=session.bind.dialect,
        compile_kwargs={"literal_binds": True}
    )))
).fetchall()

for row in explain:
    print(row[0])
```

**Pagination Best Practices:**
```python
# ✅ Good: Limit + Offset with index
page = 1
per_page = 50
offset = (page - 1) * per_page

workflows = session.query(Workflow).order_by(
    Workflow.created_at.desc()
).limit(per_page).offset(offset).all()

# ✅ Better: Keyset pagination (for large datasets)
last_created_at = some_datetime
workflows = session.query(Workflow).filter(
    Workflow.created_at < last_created_at
).order_by(Workflow.created_at.desc()).limit(50).all()
```

---

## Performance Monitoring

### Metrics to Track

**Connection Pool Metrics:**
- Pool size vs. checked out connections
- Connection wait time
- Connection checkout failures
- Pool overflow count

**Query Performance Metrics:**
- Query execution time (p50, p95, p99)
- Slow query count (> 1 second)
- Query count per endpoint
- N+1 query occurrences

**Database Metrics:**
- Active connections
- Idle connections
- Transaction rate
- Cache hit ratio
- Index usage ratio

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Query metrics
query_duration = Histogram(
    'autopr_db_query_duration_seconds',
    'Database query duration',
    ['operation', 'table']
)

query_counter = Counter(
    'autopr_db_queries_total',
    'Total database queries',
    ['operation', 'table', 'status']
)

# Connection pool metrics
pool_connections = Gauge(
    'autopr_db_pool_connections',
    'Database pool connections',
    ['state']  # checked_in, checked_out, overflow
)

# Usage example
with query_duration.labels(operation='select', table='workflows').time():
    workflows = session.query(Workflow).all()
```

### Slow Query Logging

**PostgreSQL Configuration:**
```sql
-- Enable slow query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1 second
ALTER SYSTEM SET log_line_prefix = '%t [%p]: ';
ALTER SYSTEM SET log_statement = 'none';
SELECT pg_reload_conf();
```

**Application Logging:**
```python
import logging
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

logger = logging.getLogger('sqlalchemy.queries')

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop()
    if total > 1.0:  # Log slow queries
        logger.warning(f"Slow query ({total:.2f}s): {statement[:200]}")
```

---

## Backup & Recovery

### Automated Backup Strategy

**PostgreSQL:**
```bash
#!/bin/bash
# backup_database.sh

DB_NAME="autopr_db"
BACKUP_DIR="/backups/autopr"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${DATE}.sql.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Dump database (compressed)
pg_dump -Fc $DB_NAME | gzip > $BACKUP_FILE

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

# Verify backup
if [ -f "$BACKUP_FILE" ]; then
    echo "Backup created: $BACKUP_FILE"
    # Optional: Upload to S3
    # aws s3 cp $BACKUP_FILE s3://my-bucket/backups/
else
    echo "Backup failed!" >&2
    exit 1
fi
```

**Cron Schedule:**
```cron
# Daily backup at 2 AM
0 2 * * * /path/to/backup_database.sh

# Hourly incremental backup (PostgreSQL WAL archiving)
0 * * * * /path/to/archive_wal.sh
```

### Recovery Procedures

**Full Restore:**
```bash
#!/bin/bash
# restore_database.sh

BACKUP_FILE=$1
DB_NAME="autopr_db"

# Drop existing database (CAUTION!)
dropdb $DB_NAME

# Create new database
createdb $DB_NAME

# Restore from backup
gunzip -c $BACKUP_FILE | pg_restore -d $DB_NAME

echo "Database restored from $BACKUP_FILE"
```

**Point-in-Time Recovery (PITR):**
```bash
# 1. Restore base backup
pg_restore -d autopr_db base_backup.dump

# 2. Configure recovery
cat > recovery.conf << EOF
restore_command = 'cp /archive/%f %p'
recovery_target_time = '2025-11-22 18:00:00'
EOF

# 3. Start PostgreSQL (will replay WAL logs)
pg_ctl start
```

---

## Troubleshooting

### Common Issues

#### 1. Connection Pool Exhausted

**Symptoms:**
```
sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 20 reached
```

**Solutions:**
```bash
# Increase pool size
export DB_POOL_SIZE=20
export DB_MAX_OVERFLOW=40

# Or reduce connection hold time
# Check for:
# - Long-running transactions
# - Connections not being returned
# - Session leaks
```

#### 2. Slow Queries

**Diagnosis:**
```sql
-- PostgreSQL: Check currently running queries
SELECT 
    pid,
    now() - query_start AS duration,
    state,
    query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY duration DESC;

-- Kill long-running query
SELECT pg_terminate_backend(12345);  -- Use pid from above
```

**Solutions:**
- Add missing indexes
- Rewrite N+1 queries
- Use eager loading
- Add query result caching

#### 3. Database Locks

**Diagnosis:**
```sql
-- Check locks
SELECT 
    l.mode,
    l.locktype,
    l.relation::regclass,
    l.page,
    l.tuple,
    l.virtualxid,
    l.transactionid,
    l.pid,
    l.granted
FROM pg_locks l
LEFT JOIN pg_stat_activity psa ON l.pid = psa.pid
WHERE l.granted = false;
```

**Solutions:**
```sql
-- Kill blocking queries
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle in transaction'
AND NOW() - query_start > interval '5 minutes';
```

#### 4. High Memory Usage

**Check PostgreSQL Memory:**
```sql
SELECT 
    pg_size_pretty(pg_database_size('autopr_db')) AS db_size,
    pg_size_pretty(pg_total_relation_size('workflows')) AS workflows_size;
```

**Solutions:**
- Run VACUUM ANALYZE
- Configure `shared_buffers` (25% of RAM)
- Configure `effective_cache_size` (50-75% of RAM)
- Enable `autovacuum`

---

## Production Checklist

### Database Configuration

- [ ] Connection pooling configured (pool_size, max_overflow)
- [ ] Pool pre-ping enabled
- [ ] Connection recycling configured (3600s)
- [ ] SQL query logging disabled in production
- [ ] All indexes created and verified
- [ ] Foreign key constraints enabled
- [ ] Query timeout configured (statement_timeout)

### Monitoring

- [ ] Slow query logging enabled
- [ ] Connection pool metrics exposed
- [ ] Query performance tracking
- [ ] Database size monitoring
- [ ] Alert thresholds configured

### Backup & Recovery

- [ ] Daily automated backups configured
- [ ] Backup verification automated
- [ ] Off-site backup storage (S3, etc.)
- [ ] Recovery procedures tested
- [ ] PITR enabled (PostgreSQL WAL archiving)
- [ ] Retention policy defined (7-30 days)

### Performance

- [ ] All production indexes created
- [ ] VACUUM ANALYZE scheduled
- [ ] Query plans reviewed for common queries
- [ ] N+1 queries eliminated
- [ ] Connection limits appropriate for workload

---

## Additional Resources

### PostgreSQL Documentation
- [Connection Pooling](https://www.postgresql.org/docs/current/runtime-config-connection.html)
- [Index Types](https://www.postgresql.org/docs/current/indexes-types.html)
- [Performance Tips](https://wiki.postgresql.org/wiki/Performance_Optimization)

### SQLAlchemy Documentation
- [Engine Configuration](https://docs.sqlalchemy.org/en/20/core/engines.html)
- [Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [ORM Performance](https://docs.sqlalchemy.org/en/20/orm/queryguide/performance.html)

### Tools
- [pgAdmin](https://www.pgadmin.org/) - PostgreSQL administration
- [pgBadger](https://github.com/dalibo/pgbadger) - Log analyzer
- [pg_stat_statements](https://www.postgresql.org/docs/current/pgstatstatements.html) - Query statistics

---

**Document Version:** 1.0  
**Last Updated:** 2025-11-22  
**Maintained by:** AutoPR Engine Team  
**Review Frequency:** Quarterly
