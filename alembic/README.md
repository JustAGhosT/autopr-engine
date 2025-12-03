# Alembic Database Migrations

This directory contains database migrations for AutoPR Engine using Alembic.

## **Quick Start**

### **1. Environment Setup**

Ensure your `DATABASE_URL` environment variable is set:

```bash
# Development
export DATABASE_URL="postgresql://autopr_user:autopr_password@localhost:5432/autopr"

# Production (use secrets management!)
export DATABASE_URL="${DB_CONNECTION_STRING}"
```

### **2. Create Initial Migration**

Generate the initial migration from your models:

```bash
poetry run alembic revision --autogenerate -m "Initial database schema"
```

### **3. Apply Migrations**

Run all pending migrations:

```bash
poetry run alembic upgrade head
```

### **4. Rollback Migrations**

Downgrade by one revision:

```bash
poetry run alembic downgrade -1
```

Downgrade to a specific revision:

```bash
poetry run alembic downgrade <revision_id>
```

Rollback all migrations:

```bash
poetry run alembic downgrade base
```

---

## **Common Commands**

### **View Migration History**

```bash
# Show current version
poetry run alembic current

# Show migration history
poetry run alembic history

# Show detailed history with diffs
poetry run alembic history --verbose
```

### **Create New Migration**

```bash
# Auto-generate migration from model changes
poetry run alembic revision --autogenerate -m "Add user authentication"

# Create empty migration for manual SQL
poetry run alembic revision -m "Add custom index"
```

### **Apply Specific Migration**

```bash
# Upgrade to specific revision
poetry run alembic upgrade <revision_id>

# Upgrade by relative steps
poetry run alembic upgrade +2
```

### **Generate SQL Without Applying**

```bash
# Generate SQL for upgrade
poetry run alembic upgrade head --sql

# Generate SQL for downgrade
poetry run alembic downgrade -1 --sql
```

---

## **Migration Best Practices**

### **1. Always Review Auto-Generated Migrations**

Alembic's autogenerate is powerful but not perfect. Always review generated migrations:

```python
# Check for:
# - Correct column types
# - Proper constraints
# - Index definitions
# - Foreign key relationships
# - Data migrations needed
```

### **2. Add Data Migrations When Needed**

For schema changes that require data transformation:

```python
def upgrade():
    # Add column with default value
    op.add_column('workflows', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    
    # Remove server default after backfill
    op.alter_column('workflows', 'version', server_default=None)

def downgrade():
    op.drop_column('workflows', 'version')
```

### **3. Test Migrations Thoroughly**

```bash
# Test upgrade
poetry run alembic upgrade head

# Test downgrade
poetry run alembic downgrade -1

# Test upgrade again
poetry run alembic upgrade head
```

### **4. Use Transactions**

Alembic runs migrations in transactions by default. Keep migrations atomic:

```python
def upgrade():
    # All operations in single transaction
    op.create_table('new_table', ...)
    op.add_column('existing_table', ...)
    # Both succeed or both fail
```

### **5. Add Indexes Concurrently (PostgreSQL)**

For large tables, add indexes concurrently to avoid locks:

```python
from alembic import op

def upgrade():
    op.create_index(
        'idx_workflows_status',
        'workflows',
        ['status'],
        postgresql_concurrently=True
    )
```

---

## **Migration Workflow**

### **Development**

1. Modify models in `autopr/database/models.py`
2. Generate migration: `poetry run alembic revision --autogenerate -m "Description"`
3. Review generated migration in `alembic/versions/`
4. Test migration: `poetry run alembic upgrade head`
5. Test rollback: `poetry run alembic downgrade -1`
6. Commit migration file with code changes

### **Production Deployment**

1. **Backup Database**
   ```bash
   pg_dump -h $DB_HOST -U $DB_USER -Fc autopr > backup_$(date +%Y%m%d_%H%M%S).dump
   ```

2. **Review Migration**
   ```bash
   poetry run alembic upgrade head --sql > migration.sql
   # Review migration.sql
   ```

3. **Apply Migration**
   ```bash
   poetry run alembic upgrade head
   ```

4. **Verify Application**
   ```bash
   # Check application health
   curl http://localhost:8000/health
   ```

5. **Rollback if Needed**
   ```bash
   poetry run alembic downgrade -1
   ```

---

## **Troubleshooting**

### **"Target database is not up to date"**

Your database is not at the latest version:

```bash
# Check current version
poetry run alembic current

# Upgrade to latest
poetry run alembic upgrade head
```

### **"Can't locate revision identified by 'xyz'"**

Migration file is missing or corrupted:

```bash
# Check migration history
poetry run alembic history

# If migration is truly lost, create new baseline
poetry run alembic stamp head
```

### **"Multiple head revisions are present"**

You have conflicting migration branches:

```bash
# Merge branches
poetry run alembic merge -m "Merge migration branches" <rev1> <rev2>

# Then upgrade
poetry run alembic upgrade head
```

### **Autogenerate Not Detecting Changes**

- Ensure models are imported in `env.py`
- Check that `target_metadata` is set correctly
- Verify database connection is working
- Some changes (like CHECK constraints) may not be detected

---

## **Migration File Structure**

```python
"""Add user authentication

Revision ID: abc123def456
Revises: previous_revision
Create Date: 2025-01-20 10:30:00.123456

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'abc123def456'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None

def upgrade():
    # Upgrade operations
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    # Downgrade operations
    op.drop_table('users')
```

---

## **Advanced Usage**

### **Branching and Merging**

For feature branch development:

```bash
# Create branch
poetry run alembic revision --autogenerate -m "Feature branch" --head=head --branch-label=feature

# Merge branches
poetry run alembic merge -m "Merge feature" feature main
```

### **Offline SQL Generation**

For environments without direct database access:

```bash
# Generate SQL file
poetry run alembic upgrade head --sql > upgrade.sql

# Apply manually
psql -h $DB_HOST -U $DB_USER -d autopr -f upgrade.sql
```

### **Custom Migration Scripts**

For complex data migrations:

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

def upgrade():
    # Define table for data manipulation
    workflows = table('workflows',
        column('id', sa.UUID),
        column('status', sa.String),
    )
    
    # Update data
    op.execute(
        workflows.update()
        .where(workflows.c.status == 'deprecated')
        .values(status='archived')
    )
```

---

## **TODO: Production Enhancements**

- [ ] Set up automated migration testing in CI/CD
- [ ] Implement migration approval workflow
- [ ] Add pre-migration health checks
- [ ] Create rollback automation
- [ ] Set up migration monitoring and alerting
- [ ] Document zero-downtime migration strategies
- [ ] Implement migration lock mechanism for multi-instance deployments
- [ ] Add migration performance profiling

---

## **Resources**

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Database Schema Documentation](../docs/database/DATABASE_SCHEMA.md)
- [Deployment Guide](../docs/deployment/DEPLOYMENT_GUIDE.md)

---

**Last Updated**: 2025-01-20  
**Alembic Version**: 1.17.2
