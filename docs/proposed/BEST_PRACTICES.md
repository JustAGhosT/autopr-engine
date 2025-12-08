# AutoPR Engine Best Practices
## Engineering Standards & Guidelines

**Status:** PROPOSED  
**Version:** 1.0  
**Date:** 2025-11-22  
**Purpose:** Comprehensive best practices for AutoPR Engine development

---

## Table of Contents

1. [Code Organization](#code-organization)
2. [Python Standards](#python-standards)
3. [TypeScript/React Standards](#typescriptreact-standards)
4. [API Design](#api-design)
5. [Security](#security)
6. [Testing](#testing)
7. [Documentation](#documentation)
8. [Performance](#performance)
9. [Accessibility](#accessibility)
10. [DevOps & Deployment](#devops--deployment)
11. [Code Review](#code-review)

---

## Code Organization

### Module Structure

Follow feature-based organization:

```
autopr/
├── feature_name/
│   ├── __init__.py          # Public API
│   ├── models.py            # Data models
│   ├── service.py           # Business logic
│   ├── repository.py        # Data access
│   ├── schemas.py           # API schemas (Pydantic)
│   └── routes.py            # API endpoints
```

### Dependency Injection

Use dependency injection for testability:

```python
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    
    database = providers.Singleton(Database, url=config.database_url)
    
    workflow_repository = providers.Factory(
        WorkflowRepository,
        session_factory=database.provided.session
    )
    
    workflow_service = providers.Factory(
        WorkflowService,
        repository=workflow_repository
    )
```

### Import Organization

```python
# Standard library
import asyncio
import logging
from pathlib import Path
from typing import Optional

# Third-party
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy import select

# Local
from codeflow_engine.config import settings
from codeflow_engine.database import async_session
from codeflow_engine.exceptions import WorkflowError
```

---

## Python Standards

### PEP 8 Compliance

- **Line length:** 100 characters (configured in Ruff)
- **Indentation:** 4 spaces
- **Naming:**
  - `snake_case` for functions, variables, module names
  - `PascalCase` for classes
  - `SCREAMING_SNAKE_CASE` for constants
  - Private: `_leading_underscore`

### Type Hints

Always use type hints:

```python
from typing import Optional, List, Dict, Any

def process_workflow(
    workflow_id: int,
    *,
    retry: bool = False,
    max_attempts: int = 3
) -> WorkflowResult:
    """Process a workflow."""
    ...

async def get_workflows(
    status: Optional[str] = None,
    limit: int = 100
) -> List[Workflow]:
    """Get workflows filtered by status."""
    ...
```

### Async/Await Patterns

**Always use async for I/O operations:**

```python
# Good: Async I/O
async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# Bad: Blocking I/O in async function
async def fetch_data(url: str) -> dict:
    response = requests.get(url)  # ❌ Blocking!
    return response.json()
```

### Error Handling

Use custom exceptions:

```python
# Define custom exceptions
class WorkflowError(AutoPRException):
    """Workflow-related errors."""

# Use in code
try:
    result = await execute_workflow(workflow_id)
except WorkflowError as e:
    logger.error("Workflow failed", workflow_id=workflow_id, error=str(e))
    raise
except Exception as e:
    logger.exception("Unexpected error")
    raise WorkflowError(f"Workflow {workflow_id} failed") from e
```

### Logging

Use structured logging (structlog):

```python
import structlog

logger = structlog.get_logger(__name__)

# Good: Structured logging
logger.info(
    "workflow_executed",
    workflow_id=workflow.id,
    duration=duration,
    status=result.status
)

# Bad: String formatting
logger.info(f"Workflow {workflow.id} took {duration}s")  # ❌
```

---

## TypeScript/React Standards

### Component Structure

```typescript
// Good: Functional component with proper typing
interface WorkflowCardProps {
  workflow: Workflow;
  onEdit?: (id: number) => void;
  onDelete?: (id: number) => void;
}

export const WorkflowCard: React.FC<WorkflowCardProps> = ({
  workflow,
  onEdit,
  onDelete
}) => {
  const [isLoading, setIsLoading] = useState(false);
  
  const handleEdit = useCallback(() => {
    onEdit?.(workflow.id);
  }, [workflow.id, onEdit]);
  
  return (
    <Card>
      <CardHeader>
        <h3>{workflow.name}</h3>
      </CardHeader>
      <CardContent>
        {workflow.description}
      </CardContent>
      <CardFooter>
        <Button onClick={handleEdit}>Edit</Button>
      </CardFooter>
    </Card>
  );
};
```

### State Management

```typescript
// Use useState for local state
const [count, setCount] = useState(0);

// Use useReducer for complex state
const [state, dispatch] = useReducer(reducer, initialState);

// Use Context for global state
const ThemeContext = createContext<Theme>('light');

// Use React Query for server state
const { data, isLoading } = useQuery(['workflows'], fetchWorkflows);
```

### Performance Optimization

```typescript
// Memoize expensive computations
const sortedItems = useMemo(() => {
  return items.sort((a, b) => b.createdAt - a.createdAt);
}, [items]);

// Memoize callbacks
const handleClick = useCallback(() => {
  doSomething(id);
}, [id]);

// Memoize components
export const ExpensiveComponent = React.memo(({ data }) => {
  return <div>{/* render */}</div>;
});
```

---

## API Design

### RESTful Principles

```python
# Resources should be nouns
GET    /api/v1/workflows           # List workflows
POST   /api/v1/workflows           # Create workflow
GET    /api/v1/workflows/{id}      # Get workflow
PUT    /api/v1/workflows/{id}      # Update workflow (full)
PATCH  /api/v1/workflows/{id}      # Update workflow (partial)
DELETE /api/v1/workflows/{id}      # Delete workflow

# Nested resources
GET    /api/v1/workflows/{id}/executions
POST   /api/v1/workflows/{id}/execute
```

### Request/Response Models

```python
from pydantic import BaseModel, Field

class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    config: Dict[str, Any]

class WorkflowResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True  # Allow from ORM models
```

### Error Responses

Consistent error format:

```python
{
  "error": {
    "code": "WORKFLOW_NOT_FOUND",
    "message": "Workflow with ID 123 not found",
    "details": {
      "workflow_id": 123
    }
  }
}
```

### Versioning

Use URL versioning:

```python
@app.get("/api/v1/workflows")
async def list_workflows_v1():
    pass

@app.get("/api/v2/workflows")  # Breaking changes
async def list_workflows_v2():
    pass
```

---

## Security

### Input Validation

**Always validate all inputs:**

```python
from codeflow_engine.workflows.validation import validate_workflow_input

@app.post("/api/v1/workflows")
async def create_workflow(data: WorkflowCreate):
    # Validation happens automatically via Pydantic
    # But add custom validation for complex rules
    validate_workflow_input(data.config)
    
    workflow = await workflow_service.create(data)
    return workflow
```

### Secret Management

**Never commit secrets:**

```python
# Good: Use environment variables
from codeflow_engine.config import settings

github_token = settings.github_token

# Bad: Hardcoded secrets
github_token = "ghp_xxxxxxxxxxxx"  # ❌ Never do this!
```

### SQL Injection Prevention

**Use ORM with parameterized queries:**

```python
# Good: ORM prevents SQL injection
workflow = await session.execute(
    select(Workflow).where(Workflow.id == workflow_id)
)

# Bad: String formatting
query = f"SELECT * FROM workflows WHERE id = {workflow_id}"  # ❌
```

### Authentication & Authorization

```python
from fastapi import Depends, HTTPException
from codeflow_engine.security import get_current_user, require_permission

@app.get("/api/v1/workflows/{id}")
async def get_workflow(
    id: int,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission("workflows.read"))
):
    # User is authenticated and authorized
    workflow = await workflow_service.get(id)
    return workflow
```

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/v1/workflows")
@limiter.limit("100/minute")
async def list_workflows(request: Request):
    pass
```

---

## Testing

### Test Structure (AAA Pattern)

```python
async def test_workflow_execution_success():
    # Arrange
    workflow = await create_test_workflow(name="test")
    engine = WorkflowEngine()
    
    # Act
    result = await engine.execute(workflow)
    
    # Assert
    assert result.status == "success"
    assert result.duration > 0
    assert result.output is not None
```

### Test Organization

```
tests/
├── unit/              # Unit tests (fast, isolated)
│   ├── workflows/
│   └── integrations/
├── integration/       # Integration tests
│   ├── api/
│   └── database/
├── e2e/              # End-to-end tests
└── fixtures/         # Shared fixtures
    └── conftest.py
```

### Mocking

```python
from unittest.mock import AsyncMock, patch

async def test_workflow_with_mocked_llm():
    # Mock external dependency
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = "Mocked response"
    
    with patch('autopr.ai.providers.openai.OpenAIProvider', return_value=mock_llm):
        result = await execute_workflow_with_llm()
    
    assert result.contains("Mocked response")
    mock_llm.generate.assert_called_once()
```

### Coverage Requirements

- **Overall:** 70-80% minimum
- **Critical modules:** 90%+ (security, workflows, integrations)
- **New code:** 80%+ required
- **Tests pass:** 100% required

---

## Documentation

### Docstring Format (Google Style)

```python
def process_workflow(
    workflow_id: int,
    *,
    retry: bool = False,
    max_attempts: int = 3
) -> WorkflowResult:
    """
    Process a workflow with optional retry logic.
    
    This function executes a workflow and handles errors according to the
    retry policy. If retry is enabled, it will attempt up to max_attempts
    times with exponential backoff.
    
    Args:
        workflow_id: The unique identifier of the workflow to process.
        retry: Whether to retry on transient failures. Defaults to False.
        max_attempts: Maximum number of retry attempts. Defaults to 3.
    
    Returns:
        A WorkflowResult object containing the execution status, output,
        and duration.
    
    Raises:
        WorkflowNotFoundError: If the workflow_id doesn't exist.
        WorkflowExecutionError: If execution fails after all retries.
    
    Example:
        >>> result = process_workflow(123, retry=True, max_attempts=5)
        >>> print(result.status)
        'success'
    """
    ...
```

### README Updates

Update README when adding:
- New features
- New integrations
- Breaking changes
- New configuration options

### Architecture Decision Records (ADRs)

Create ADR for significant decisions:

```markdown
# ADR-XXX: Title

## Status
Proposed / Accepted / Deprecated / Superseded

## Context
What is the issue that we're seeing that is motivating this decision?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult to do because of this change?
```

---

## Performance

### Database Optimization

```python
# Good: Use connection pooling
engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10,
    pool_recycle=3600
)

# Good: Eager loading to avoid N+1
workflows = await session.execute(
    select(Workflow)
    .options(joinedload(Workflow.executions))
    .where(Workflow.status == "active")
)

# Bad: N+1 query
workflows = await session.execute(select(Workflow))
for workflow in workflows:
    executions = workflow.executions  # Separate query each time! ❌
```

### Caching

```python
from functools import lru_cache
import redis

# Memory cache for small, frequently accessed data
@lru_cache(maxsize=1000)
def get_config(key: str) -> str:
    return config_dict[key]

# Redis cache for larger data
redis_client = redis.Redis(host='localhost', port=6379)

async def get_workflow(workflow_id: int) -> Workflow:
    # Try cache first
    cached = redis_client.get(f"workflow:{workflow_id}")
    if cached:
        return Workflow.parse_raw(cached)
    
    # Fetch from database
    workflow = await workflow_repository.get(workflow_id)
    
    # Cache for 1 hour
    redis_client.setex(
        f"workflow:{workflow_id}",
        3600,
        workflow.json()
    )
    
    return workflow
```

### Async Operations

```python
# Good: Parallel async operations
async def process_multiple_workflows(workflow_ids: List[int]):
    tasks = [process_workflow(wid) for wid in workflow_ids]
    results = await asyncio.gather(*tasks)
    return results

# Bad: Sequential async operations
async def process_multiple_workflows(workflow_ids: List[int]):
    results = []
    for wid in workflow_ids:
        result = await process_workflow(wid)  # ❌ Sequential!
        results.append(result)
    return results
```

---

## Accessibility

### WCAG 2.1 AA Compliance

**Required:**
- Color contrast ≥ 4.5:1 for normal text
- All functionality keyboard accessible
- ARIA attributes where needed
- Focus indicators visible
- Alt text for images

### Semantic HTML

```tsx
// Good: Semantic HTML
<nav>
  <ul>
    <li><a href="/">Home</a></li>
  </ul>
</nav>

<main>
  <h1>Page Title</h1>
  <section>
    <h2>Section Title</h2>
  </section>
</main>

// Bad: Divs for everything
<div className="nav">  {/* ❌ Use <nav> */}
  <div className="nav-item">
    <span onClick={...}>Home</span>  {/* ❌ Use <a> or <button> */}
  </div>
</div>
```

### ARIA Attributes

```tsx
// Button with icon only
<button aria-label="Delete workflow">
  <TrashIcon />
</button>

// Live region for dynamic updates
<div role="status" aria-live="polite" aria-atomic="true">
  {statusMessage}
</div>

// Error message
<div role="alert" aria-live="assertive">
  {errorMessage}
</div>
```

---

## DevOps & Deployment

### Docker Best Practices

```dockerfile
# Multi-stage build
FROM python:3.12-slim AS builder

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev

FROM python:3.12-slim

# Non-root user
RUN useradd -m -u 1000 autopr
USER autopr

WORKDIR /app
COPY --from=builder /app/.venv .venv
COPY autopr ./autopr

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8080/health || exit 1

CMD [".venv/bin/python", "-m", "autopr.server"]
```

### CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Run linters
        run: ruff check .
      - name: Run tests
        run: pytest --cov=autopr
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Code Review

### Review Checklist

**Before submitting PR:**
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Linters pass (ruff)
- [ ] Type checking passes (mypy)
- [ ] All tests pass
- [ ] No security vulnerabilities
- [ ] Performance impact considered
- [ ] Accessibility checked (if UI changes)

**Reviewer checklist:**
- [ ] Code follows style guide
- [ ] Tests are comprehensive
- [ ] Documentation is clear
- [ ] No security issues
- [ ] Performance acceptable
- [ ] Error handling proper
- [ ] Accessibility requirements met

### PR Description Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How has this been tested?

## Screenshots (if applicable)
Add screenshots for UI changes.

## Checklist
- [ ] Tests added
- [ ] Documentation updated
- [ ] Linters pass
```

---

## Summary

**Key Principles:**
1. **Code Quality:** Write clean, maintainable, well-tested code
2. **Security First:** Always validate inputs, never commit secrets
3. **Performance:** Use async, caching, and database optimization
4. **Accessibility:** WCAG 2.1 AA compliance for all UI
5. **Documentation:** Clear docs and docstrings for all public APIs
6. **Testing:** 70%+ coverage, comprehensive test suite
7. **DevOps:** Automated CI/CD, containerized deployments

**Resources:**
- [PEP 8](https://peps.python.org/pep-0008/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [React Best Practices](https://react.dev/learn)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

---

**Document Status:** PROPOSED - Requires team review and approval  
**Next Steps:** Review, adapt to team needs, publish as official guidelines
