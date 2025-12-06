# Remaining Code Review Fixes

This document provides detailed instructions for the remaining code review issues that need to be addressed.

**Status**: 3 critical fixes completed (P0 docstring, P1 quality mode, DATABASE_URL)  
**Remaining**: 18 fixes across multiple priority levels

---

## Priority 1: Critical Runtime Issues

### 1. Add Engine None Guards in database/config.py ⚠️

**Issue**: `engine` can be None but functions assume it's valid, causing obscure AttributeErrors.

**Files**: `autopr/database/config.py` lines 107-113, 147-215

**Fix**: Add guard checks at start of functions:

```python
def get_db() -> Generator:
    """Get database session with connection check."""
    if engine is None:
        raise RuntimeError(
            "Database engine is not initialized. "
            "Ensure DATABASE_URL is set and AUTOPR_SKIP_DB_INIT is not set when running DB operations. "
            "Check that psycopg2-binary is installed: poetry add psycopg2-binary"
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """Initialize database schema."""
    if engine is None:
        raise RuntimeError(
            "Cannot initialize database: engine is None. "
            "Set DATABASE_URL environment variable to a valid PostgreSQL connection string. "
            "Example: postgresql://user:password@localhost:5432/dbname"
        )
    Base.metadata.create_all(bind=engine)

def drop_db() -> None:
    """Drop all database tables (WARNING: destructive!)."""
    if engine is None:
        raise RuntimeError(
            "Cannot drop database: engine is None. DATABASE_URL must be set."
        )
    Base.metadata.drop_all(bind=engine)

def get_connection_info() -> dict[str, Any]:
    """Get database connection information for monitoring."""
    if engine is None:
        return {
            "status": "unavailable",
            "error": "Database engine not initialized (AUTOPR_SKIP_DB_INIT may be set)"
        }
    # ... rest of function
```

### 2. Fix ImportError Handling in features/__init__.py

**Issue**: Only one symbol set to None in except blocks, leaving others undefined.

**Files**: `autopr/features/__init__.py` lines 15-70

**Fix**:

```python
# AI Learning System imports
try:
    from autopr.features.ai_learning_system import (
        AILearningSystem,
        CodeIssue,
        IssueSeverity,
        ReviewFeedback,
        ReviewFeedbackType,
        ReviewSession,
    )
except ImportError:
    AILearningSystem = None
    CodeIssue = None
    IssueSeverity = None
    ReviewFeedback = None
    ReviewFeedbackType = None
    ReviewSession = None

# Workflow Builder imports
try:
    from autopr.features.workflow_builder import (
        Workflow,
        WorkflowBuilder,
        WorkflowEdge,
        WorkflowNode,
        NodeType,
        TriggerType,
        ActionType,
    )
except ImportError:
    Workflow = None
    WorkflowBuilder = None
    WorkflowEdge = None
    WorkflowNode = None
    NodeType = None
    TriggerType = None
    ActionType = None

# Update __all__ to include all names
__all__ = [
    "AILearningSystem",
    "CodeIssue",
    "IssueSeverity",
    "ReviewFeedback",
    "ReviewFeedbackType",
    "ReviewSession",
    "Workflow",
    "WorkflowBuilder",
    "WorkflowEdge",
    "WorkflowNode",
    "NodeType",
    "TriggerType",
    "ActionType",
    "RealtimeDashboard",  # if present
]
```

### 3. Fix Pydantic Imports in workflow_builder.py

**Issue**: Using `dataclasses.field` instead of `pydantic.Field`.

**Files**: `autopr/features/workflow_builder.py` line 26, 70-109

**Fix**:

```python
# Line 26 - Update import
from pydantic import BaseModel, Field, validator

# Lines 70-74 - WorkflowNode
class WorkflowNode(BaseModel):
    """Workflow node configuration."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: NodeType
    config: dict = Field(default_factory=dict)
    
# Lines 82-85 - WorkflowEdge  
class WorkflowEdge(BaseModel):
    """Workflow edge (connection between nodes)."""
    source: str
    target: str
    condition: Optional[str] = None

# Lines 98-109 - Workflow
class Workflow(BaseModel):
    """Complete workflow definition."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    nodes: list[WorkflowNode] = Field(default_factory=list)
    edges: list[WorkflowEdge] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

---

## Priority 2: Feature Bugs

### 4. Fix recommend_reviewers Limit Parameter

**Issue**: Hard-coded 2-item list ignores limit parameter.

**Files**: `autopr/features/ai_learning_system.py` lines 366-379

**Fix**:

```python
def recommend_reviewers(self, code_changes: str, limit: int = 5) -> list[dict]:
    """
    Recommend reviewers based on expertise and availability.
    
    Args:
        code_changes: Code diff or changed files
        limit: Maximum number of reviewers to return
        
    Returns:
        List of reviewer recommendations (up to limit items)
    """
    # TODO: PRODUCTION - Implement reviewer recommendation ML model
    #   - Analyze file paths and content
    #   - Match with historical reviewer expertise
    #   - Consider reviewer availability and workload
    #   - Use graph-based or collaborative filtering model
    
    candidates = [
        {
            "reviewer": "senior-dev",
            "confidence": 0.85,
            "expertise_match": ["python", "backend"],
            "avg_review_time": "2 hours"
        },
        {
            "reviewer": "qa-lead",
            "confidence": 0.75,
            "expertise_match": ["testing", "quality"],
            "avg_review_time": "4 hours"
        },
        {
            "reviewer": "architect",
            "confidence": 0.65,
            "expertise_match": ["system-design", "architecture"],
            "avg_review_time": "6 hours"
        },
    ]
    
    # Respect limit parameter
    if limit <= 0:
        return []
    return candidates[:limit]
```

### 5. Replace Pydantic V1 dict() with model_dump()

**Issue**: Using deprecated `.dict()` method.

**Files**: `autopr/features/ai_learning_system.py` lines 447-468

**Fix**:

```python
def export_training_data(self) -> dict:
    """Export training data for ML model training."""
    # TODO: PRODUCTION - Export in proper ML format (TFRecords, etc.)
    #   - Convert to TFRecord format for TensorFlow
    #   - Or Parquet format for efficient storage
    #   - Include feature engineering pipeline
    #   - Split into train/validation/test sets
    
    return {
        "feedback_history": [
            {
                "issue_id": f.issue_id,
                "feedback_type": f.feedback_type.value,
                "confidence_adjustment": f.confidence_adjustment,
                "timestamp": f.timestamp.isoformat(),
            }
            for f in self.feedback_history
        ],
        "review_sessions": [
            s.model_dump() for s in self.review_sessions  # Changed from s.dict()
        ],
        "total_samples": len(self.feedback_history),
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
    }
```

### 6. Fix Numpy Float Serialization

**Issue**: `np.mean()` returns `numpy.float64` which fails JSON serialization.

**Files**: `autopr/features/ai_learning_system.py` lines 385-422

**Fix**:

```python
# Around line 410-415
if scores:
    severity_acc = float(np.mean(scores))  # Cast to Python float
else:
    severity_acc = 0.0
```

---

## Priority 3: Test Fixes

### 7. Fix Platform Detector Test Fallback Assertions

**Issue**: Tests don't explicitly verify "unknown" fallback behavior.

**Files**: `tests/test_platform_detector_improvements.py` lines 74-78, 136-140

**Fix for lines 74-78**:

```python
def test_empty_workspace_returns_unknown():
    """Test that empty workspace returns 'unknown' fallback."""
    detector = PlatformDetector()
    result = detector.detect_platform(PlatformDetectorInputs(
        workspace_path=empty_temp_dir,
        repository_url="",
        commit_messages=[],
        package_json_content=None
    ))
    
    # Explicitly verify unknown fallback
    assert result.primary_platform == "unknown"
    score = result.confidence_scores.get("unknown")
    assert score is not None
    assert isinstance(score, float)
    assert score == 1.0  # Expected fallback confidence
```

**Fix for lines 136-140**:

```python
def test_weak_signals_returns_unknown():
    """Test that weak signals below threshold return 'unknown' fallback."""
    detector = PlatformDetector()
    result = detector.detect_platform(PlatformDetectorInputs(
        workspace_path=weak_signals_dir,
        repository_url="",
        commit_messages=[],
        package_json_content=None
    ))
    
    # Remove conditional guard, directly assert unknown
    assert result.primary_platform == "unknown"
    assert result.confidence_scores.get("unknown") == 1.0
    
    # Verify no other platforms exceeded threshold
    for platform, score in result.confidence_scores.items():
        if platform != "unknown":
            assert score < 0.5, f"Platform {platform} should be below 0.5 threshold"
```

---

## Priority 4: UI/UX Fixes

### 8. Fix Modal Focus Restoration in Dashboard Template

**Issue**: Overcomplicated focus restoration that doesn't work reliably.

**Files**: `autopr/dashboard/templates/index.html` lines 609-631

**Fix**:

```javascript
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.style.display = 'block';
    modal.setAttribute('aria-hidden', 'false');
    
    // Store last focused element directly on modal object
    modal.lastFocusedElement = document.activeElement;
    
    // Focus first focusable element in modal
    setTimeout(() => {
        const firstFocusable = modal.querySelector('button, input, select, textarea');
        if (firstFocusable) {
            firstFocusable.focus();
        }
    }, 100);
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.style.display = 'none';
    modal.setAttribute('aria-hidden', 'true');
    
    // Restore focus to last focused element
    if (modal.lastFocusedElement) {
        modal.lastFocusedElement.focus();
    }
}
```

---

## Priority 5: Configuration & Documentation

### 9. Remove Hardcoded Paths from mcp-servers.json

**Issue**: Line 8 has hardcoded Windows path.

**Fix**: Either:
1. Move `mcp-servers.json` to `.gitignore` and create `mcp-servers.json.example`, OR
2. Replace with environment variable:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "node",
      "args": [
        "${AUTOPR_ROOT_PATH}\\node_modules\\@modelcontextprotocol\\server-filesystem\\dist\\index.js",
        "${AUTOPR_ROOT_PATH}"
      ]
    }
  }
}
```

Add to `.env.example`:
```bash
# MCP Server Root Path (for mcp-servers.json)
AUTOPR_ROOT_PATH=.
```

### 10. Remove Hardcoded Credentials from mcp-servers.json

**Issue**: Lines 28-29, 92-93 have hardcoded PostgreSQL credentials.

**Fix**:

```json
{
  "database": {
    "connectionString": "${DATABASE_URL}"
  }
}
```

### 11. Fix Typo in VERIFICATION_CHECKLIST.md

**Issue**: Line 311 says "None Critical" instead of "Non-Critical".

**Fix**: Change line 311 from:
```markdown
### **None Critical**
```
to:
```markdown
### **Non-Critical**
```

---

## Priority 6: Documentation Accuracy

### 12. Fix Markdown Table Spacing in WCAG_COMPLIANCE.md

**Issue**: Tables at lines 69-76, 152-162 lack surrounding blank lines (MD058).

**Fix**: Add blank line before and after each table.

### 13. Fix Integrations Table Schema Documentation

**Issue**: DATABASE_SCHEMA.md references `created_by` column that doesn't exist in table definition.

**Fix**: Either add column to table definition (lines 326-357):
```sql
created_by UUID,  -- User who created this integration
```

Or update RLS policy example to use existing column.

### 14. Fix Workflow Builder TODO Count

**Issue**: Inconsistent counts: summary shows 5, section lists 6, total is off by 1.

**Fix in PRODUCTION_READINESS.md**:
- Line 13-17: Change "5" to "6"
- Line 133: Change "5 TODOs" to "6 TODOs"  
- Line 460-462: Change "Total TODOs: 28" to "Total TODOs: 29"

### 15. Fix Security Docs sanitize_filename Description

**Issue**: Lines 255-260 document non-existent regex implementation.

**Fix**: Replace with:

```markdown
#### Path Validation Implementation

The `autopr/dashboard/server.py` module implements path validation using Python's Path library:

- **Canonicalization**: Uses `Path.expanduser().resolve(strict=False)` to normalize paths
  - Handles null bytes, path separators, and leading dots automatically
  - Resolves symbolic links and relative paths

- **Validation Functions**:
  - `_get_allowed_directories()` (line ~67): Returns list of approved base paths
  - `_validate_path()` (line ~83): Checks if path is within allowed directories
  - `_sanitize_file_list()` (line ~115): Bulk validation for file lists

Example usage:
```python
is_valid, error = self._validate_path(user_input)
if not is_valid:
    return jsonify({"error": error}), 403
```

This approach is more robust than regex as it handles OS-specific path formats and edge cases.
```

---

## Priority 7: Tool Fixes (Complex)

### 16. Fix whitespace_fixer Error Handling

**Issue**: No error tracking, dry-run counts as modifications, missing error exit codes.

**Files**: `tools/whitespace_fixer/fixer.py` lines 307-311, 457, 463-491

**Complex fix - see separate implementation guide in this file below.**

### 17. Remove Redundant Pass in yaml_lint CLI

**Issue**: Line 291 has unnecessary `pass` after print.

**Files**: `tools/yaml_lint/cli.py` line 291

**Fix**: Simply delete line 291.

### 18. Fix Socket.IO Session Management

**Issue**: client_id never stored, disconnect cleanup fails, sender not excluded from broadcasts.

**Files**: `autopr/features/realtime_dashboard.py` lines 66-269

**Complex fix - see separate implementation guide in this file below.**

---

## Complex Fix Guides

### Whitespace Fixer Implementation

```python
# Add had_errors flag initialization (around line 307)
had_errors = False
total_files_modified = 0
total_files_would_modify = 0  # New counter for dry-run

# In directory mode loop (around line 457)
for result in results:
    if result["errors"]:
        had_errors = True
        
# In single-file mode (around line 463-465)
except Exception as e:
    had_errors = True
    
# Update counters (around line 479-481)
if dry_run:
    if has_changes:
        total_files_would_modify += 1
else:
    if has_changes:
        total_files_modified += 1

# Update summary text (around line 484-491)
if dry_run:
    print(f"\nSummary: Would modify {total_files_would_modify} files")
else:
    print(f"\nSummary: Modified {total_files_modified} files")
    
# Update exit logic (end of file)
if had_errors or total_files_modified > 0:
    sys.exit(1)
else:
    sys.exit(0)
```

### Socket.IO Session Management Implementation

```python
# In handle_connect (line 66-80)
@socketio.on('connect')
def handle_connect():
    client_id = str(uuid.uuid4())
    
    # Store in Flask-SocketIO session
    session['client_id'] = client_id
    
    # Also maintain mapping for quick lookup
    self.sid_to_client[request.sid] = client_id
    
    self.active_users[client_id] = {
        'connected_at': datetime.now(timezone.utc).isoformat(),
        'sid': request.sid
    }
    
    emit('connection_established', {'client_id': client_id})

# In handle_disconnect (line 100-116)
@socketio.on('disconnect')
def handle_disconnect():
    # Look up client_id from session or mapping
    client_id = session.get('client_id') or self.sid_to_client.get(request.sid)
    
    if client_id and client_id in self.active_users:
        del self.active_users[client_id]
    
    if request.sid in self.sid_to_client:
        del self.sid_to_client[request.sid]

# In _broadcast_event (line 244-269)
def _broadcast_event(self, event: str, data: dict):
    """Broadcast event to all connected clients except sender."""
    socketio.emit(
        event,
        data,
        skip_sid=request.sid,  # Exclude sender
        namespace='/'
    )
```

---

## Verification Commands

After applying fixes:

```bash
# Test imports
poetry run python -c "from autopr.dashboard.router import DashboardState; print('✅ Dashboard imports')"
poetry run python -c "from autopr.database.config import get_db; print('✅ Database config imports')"
poetry run python -c "from autopr.features import *; print('✅ Features import')"

# Run tests
poetry run pytest tests/test_platform_detector_improvements.py -v

# Check markdown
poetry run markdownlint docs/**/*.md

# Verify JSON
python -c "import json; json.load(open('mcp-servers.json'))"
```

---

## Summary

- **Completed**: 3 critical fixes (P0 docstring, P1 quality mode, DATABASE_URL)
- **Remaining**: 18 fixes documented above
- **Estimated Time**: 2-3 hours for all remaining fixes
- **Priority Order**: Database guards → Feature imports → Pydantic fixes → Tests → Documentation

Apply fixes in batches, test after each batch, and commit incrementally.
