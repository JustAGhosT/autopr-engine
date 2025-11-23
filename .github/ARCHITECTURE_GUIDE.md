# AutoPR Engine - Architecture Guide for AI Assistants

## Project Overview
AutoPR Engine is an AI-powered automation platform for GitHub pull request workflows, featuring intelligent analysis, automated issue creation, and multi-agent collaboration for code review and quality assurance.

## Architecture Principles (STRICT)

### Layered Architecture
- **API Layer** (`autopr/api/`): FastAPI routes, request/response handling only
- **Service Layer** (`autopr/services/`, `autopr/workflows/`): Business logic, orchestration
- **Domain Layer** (`autopr/models/`, `autopr/actions/`): Core domain entities and business rules
- **Infrastructure Layer** (`autopr/database/`, `autopr/integrations/`): External dependencies, I/O
- **Security Layer** (`autopr/security/`): Authentication, authorization, rate limiting, exception handling

### Separation of Concerns
- Controllers should ONLY handle HTTP concerns (validation, serialization)
- Business logic belongs in services and workflows
- Database access should be abstracted through repositories/models
- External integrations should be isolated in the integrations layer

## Technology Stack

### Backend
- **Language**: Python 3.12+
- **Framework**: FastAPI (async REST API), Flask-SocketIO (WebSocket support)
- **Database**: PostgreSQL with SQLAlchemy 2.0 ORM (async)
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Package Manager**: Poetry

### Frontend (Desktop UI)
- **Framework**: React 18 with TypeScript
- **UI Library**: Tailwind CSS, shadcn/ui components
- **Desktop**: Tauri (Rust-based desktop wrapper)
- **State Management**: React Context/Hooks

### AI/LLM Integration
- **Providers**: OpenAI, Anthropic, Mistral, Groq
- **Orchestration**: Multi-agent workflows with volume-aware scaling (0-1000)

### Infrastructure
- **Database**: PostgreSQL 14+
- **Containerization**: Docker, Docker Compose
- **CI/CD**: GitHub Actions
- **Observability**: structlog (structured logging)

## Code Generation Rules

### When Creating API Endpoints

```python
# FastAPI pattern (ALWAYS use this structure):
from fastapi import APIRouter, Depends, HTTPException, status
from autopr.security.auth import get_current_user
from autopr.services.workflow_service import WorkflowService
from autopr.models.workflow import WorkflowCreate, WorkflowResponse

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])

@router.post("/", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    workflow_service: WorkflowService = Depends()
):
    """
    Create a new workflow.
    
    Controller should ONLY:
    - Validate request via Pydantic
    - Call service layer
    - Return response
    """
    return await workflow_service.create_workflow(workflow, user_id=current_user.id)
```

### When Creating Services

```python
# Service layer pattern:
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from autopr.database.models import Workflow
from autopr.models.workflow import WorkflowCreate, WorkflowResponse
from autopr.exceptions import ValidationError, WorkflowError

class WorkflowService:
    """
    Service layer handles:
    - Business logic
    - Orchestration
    - Transaction management
    - Error handling
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_workflow(
        self, 
        workflow_data: WorkflowCreate, 
        user_id: int
    ) -> WorkflowResponse:
        """Create workflow with business validation."""
        # Validate business rules
        if not self._is_valid_workflow_config(workflow_data.config):
            raise ValidationError("Invalid workflow configuration")
        
        # Create entity
        workflow = Workflow(
            name=workflow_data.name,
            config=workflow_data.config,
            user_id=user_id
        )
        
        # Persist
        self.db.add(workflow)
        await self.db.commit()
        await self.db.refresh(workflow)
        
        return WorkflowResponse.from_orm(workflow)
    
    def _is_valid_workflow_config(self, config: dict) -> bool:
        """Business validation logic (private method)."""
        return "actions" in config and len(config["actions"]) > 0
```

### When Creating Database Models

```python
# SQLAlchemy 2.0 pattern with type hints:
from datetime import datetime
from sqlalchemy import String, Integer, JSON, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from autopr.database.base import Base

class Workflow(Base):
    """
    Workflow domain entity.
    
    Database models should:
    - Define schema only
    - Include relationships
    - Have proper indexes
    - Use type hints (Mapped)
    """
    __tablename__ = "workflows"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="workflows")
    runs: Mapped[list["WorkflowRun"]] = relationship("WorkflowRun", back_populates="workflow")
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_workflow_user_status', 'user_id', 'status'),
        Index('idx_workflow_created', 'created_at'),
    )
```

### When Creating Pydantic Models

```python
# Request/Response models:
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

class WorkflowBase(BaseModel):
    """Base schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Workflow name")
    config: dict = Field(..., description="Workflow configuration JSON")

class WorkflowCreate(WorkflowBase):
    """Schema for creating a workflow (input)."""
    pass

class WorkflowUpdate(BaseModel):
    """Schema for updating a workflow (partial)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    config: Optional[dict] = None
    status: Optional[str] = Field(None, pattern="^(draft|active|paused|archived)$")

class WorkflowResponse(WorkflowBase):
    """Schema for workflow responses (output)."""
    id: int
    status: str
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)  # SQLAlchemy 2.0 compatibility
```

### When Creating Tests

```python
# pytest pattern (AAA: Arrange, Act, Assert):
import pytest
from httpx import AsyncClient
from autopr.database.models import User, Workflow
from autopr.security.auth import create_access_token

@pytest.mark.asyncio
async def test_create_workflow_success(async_client: AsyncClient, test_user: User):
    """Test successful workflow creation."""
    # Arrange
    token = create_access_token({"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "Test Workflow",
        "config": {"actions": ["lint", "test"]}
    }
    
    # Act
    response = await async_client.post("/api/v1/workflows/", json=payload, headers=headers)
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Workflow"
    assert data["status"] == "draft"
    assert data["user_id"] == test_user.id

@pytest.mark.asyncio
async def test_create_workflow_invalid_config(async_client: AsyncClient, test_user: User):
    """Test workflow creation with invalid config."""
    # Arrange
    token = create_access_token({"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "Invalid Workflow",
        "config": {}  # Missing 'actions'
    }
    
    # Act
    response = await async_client.post("/api/v1/workflows/", json=payload, headers=headers)
    
    # Assert
    assert response.status_code == 422  # Validation error
```

## Security Patterns

### Always Use These Patterns

```python
# 1. Input validation (Pydantic)
from pydantic import BaseModel, Field, validator

class SafeInput(BaseModel):
    user_input: str = Field(..., max_length=1000)
    
    @validator('user_input')
    def validate_no_sql_injection(cls, v):
        if any(keyword in v.lower() for keyword in ['drop', 'delete', 'truncate']):
            raise ValueError("Invalid input detected")
        return v

# 2. Exception sanitization
from autopr.security.exception_handling import SafeExceptionHandler

handler = SafeExceptionHandler(debug=False)
response = handler.handle_exception(exc, context={"user_id": user.id})

# 3. Rate limiting
from autopr.security.rate_limiting import rate_limit

@rate_limit(limit=100, window=60, tier="authenticated")
async def protected_endpoint(request):
    pass

# 4. Authentication
from autopr.security.auth import get_current_user

@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"user": current_user.email}

# 5. Path sanitization
from autopr.security.path_validation import validate_file_path

safe_path = validate_file_path(user_provided_path, allowed_dirs=["/tmp/uploads"])
```

## Volume-Aware Development

The system uses a volume scale (0-1000) to control feature intensity:

```python
from autopr.config import VolumeConfig

def process_pr(pr_data: dict, volume: int):
    """Process PR with volume-aware behavior."""
    config = VolumeConfig(volume)
    
    if config.is_ultra_fast:  # 0-199
        return quick_analysis(pr_data)
    elif config.is_fast:  # 200-399
        return basic_analysis(pr_data)
    elif config.is_smart:  # 400-599
        return standard_analysis(pr_data)
    elif config.is_comprehensive:  # 600-799
        return thorough_analysis(pr_data)
    else:  # 800-1000
        return ai_enhanced_analysis(pr_data)
```

## Async/Await Patterns

### Always Use Async for I/O

```python
# ✅ CORRECT: Non-blocking I/O
import httpx
from aiofiles import open as aio_open

async def fetch_external_api():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
        return response.json()

async def read_file(path: str):
    async with aio_open(path, 'r') as f:
        return await f.read()

# ❌ WRONG: Blocking I/O in async function
import requests

async def fetch_external_api_blocking():
    # This blocks the event loop!
    response = requests.get("https://api.example.com/data")
    return response.json()
```

## Database Patterns

### Use Async Session Context Manager

```python
from autopr.database.config import get_db_session

async def get_workflow(workflow_id: int):
    async with get_db_session() as db:
        result = await db.execute(
            select(Workflow).where(Workflow.id == workflow_id)
        )
        return result.scalar_one_or_none()
```

### Use Dependency Injection in FastAPI

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from autopr.database.config import get_db

@router.get("/workflows/{workflow_id}")
async def get_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow
```

## Error Handling

### Use Custom Exception Hierarchy

```python
from autopr.exceptions import (
    AutoPRException,      # Base exception
    ValidationError,       # Input validation errors
    WorkflowError,        # Workflow execution errors
    IntegrationError,     # External service errors
    AuthenticationError,  # Auth errors
    AuthorizationError    # Permission errors
)

# In service layer:
def validate_workflow(workflow: Workflow):
    if not workflow.config:
        raise ValidationError("Workflow config is required", workflow_id=workflow.id)
    
    if workflow.status == "archived":
        raise WorkflowError("Cannot modify archived workflow", workflow_id=workflow.id)

# In API layer:
from autopr.security.exception_handling import setup_fastapi_exception_handlers

app = FastAPI()
setup_fastapi_exception_handlers(app, debug=False)  # Automatic sanitization
```

## Testing Requirements

### Coverage Standards
- **New code**: 80%+ coverage required
- **Critical paths**: 90%+ coverage (auth, security, payments)
- **Test types**: Unit (fast), Integration (database), E2E (full flow)

### Test Organization
```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Fast, isolated tests
│   ├── test_services/
│   ├── test_models/
│   └── test_utils/
├── integration/             # Database + service tests
│   ├── test_workflows/
│   └── test_integrations/
├── security/                # Security-specific tests
│   ├── test_auth.py
│   ├── test_rate_limiting.py
│   └── test_exception_handling.py
└── e2e/                     # Full workflow tests
    └── test_pr_workflow.py
```

## Documentation Requirements

### Docstrings (Google Style)
```python
async def create_workflow(
    name: str,
    config: dict,
    user_id: int
) -> Workflow:
    """
    Create a new workflow for a user.
    
    Args:
        name: Human-readable workflow name
        config: Workflow configuration with actions and settings
        user_id: ID of the user creating the workflow
    
    Returns:
        Created workflow instance with generated ID
    
    Raises:
        ValidationError: If config is invalid
        WorkflowError: If workflow creation fails
    
    Example:
        >>> workflow = await create_workflow(
        ...     name="CI Pipeline",
        ...     config={"actions": ["lint", "test"]},
        ...     user_id=123
        ... )
    """
```

## Common Mistakes to Avoid

### ❌ DON'T: Business Logic in Controllers
```python
@router.post("/workflows/")
async def create_workflow(workflow: WorkflowCreate, db: AsyncSession = Depends(get_db)):
    # DON'T put business logic here!
    if not workflow.config.get("actions"):
        raise HTTPException(400, "Actions required")
    
    new_workflow = Workflow(**workflow.dict())
    db.add(new_workflow)
    await db.commit()
    return new_workflow
```

### ✅ DO: Business Logic in Services
```python
@router.post("/workflows/")
async def create_workflow(
    workflow: WorkflowCreate,
    service: WorkflowService = Depends()
):
    # Controller only dispatches to service
    return await service.create_workflow(workflow)
```

### ❌ DON'T: Synchronous I/O in Async Functions
```python
async def process_file(path: str):
    with open(path, 'r') as f:  # Blocks event loop!
        return f.read()
```

### ✅ DO: Async I/O Everywhere
```python
async def process_file(path: str):
    async with aio_open(path, 'r') as f:
        return await f.read()
```

### ❌ DON'T: Expose Sensitive Info in Errors
```python
except Exception as e:
    raise HTTPException(500, detail=str(e))  # May leak DB connection strings!
```

### ✅ DO: Use Safe Exception Handling
```python
from autopr.security.exception_handling import SafeExceptionHandler

handler = SafeExceptionHandler(debug=False)
response = handler.handle_exception(e, context={"operation": "create_workflow"})
```

## Resources

- **Main Documentation**: `/docs/`
- **API Reference**: `/docs/api/`
- **Architecture Decisions**: `/docs/architecture/adr/`
- **Security Guide**: `/docs/security/SECURITY_AUDIT_PHASE1.md`
- **Master PRD**: `/docs/MASTER_PRD.md`
- **Best Practices**: `/docs/proposed/BEST_PRACTICES.md`
- **Contributing Guide**: `CONTRIBUTING.md`

## Quick Reference

### Commands
```bash
# Install dependencies
poetry install --with dev,database

# Run tests
pytest
pytest --cov=autopr --cov-report=html

# Run linting
ruff check autopr/
ruff format autopr/

# Type checking
mypy autopr/

# Run dev server
uvicorn autopr.main:app --reload

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
```

### Environment Variables
```bash
# Required
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/autopr
GITHUB_TOKEN=ghp_xxx

# Optional
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
LOG_LEVEL=INFO
ENVIRONMENT=development
```

## Contact

- **Issues**: https://github.com/JustAGhosT/autopr-engine/issues
- **Discussions**: https://github.com/JustAGhosT/autopr-engine/discussions
- **Security**: security@justaghost.com
