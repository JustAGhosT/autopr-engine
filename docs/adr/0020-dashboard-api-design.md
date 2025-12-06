# 20. Dashboard API Design

## Status

Accepted

## Context

The AutoPR Dashboard requires a well-designed API to support the React frontend. We need to establish conventions for:

- API structure and versioning
- Request/response formats
- Error handling
- Authentication flow
- Rate limiting
- Documentation

### Requirements

1. Support all dashboard features (repos, bots, workflows, settings)
2. Secure authentication via GitHub OAuth
3. Consistent error responses
4. Pagination for list endpoints
5. Real-time updates where beneficial
6. OpenAPI documentation

## Decision

We will extend the existing FastAPI application with a structured `/api` namespace following RESTful conventions.

### API Structure

```
/api
├── /auth                    # Authentication
│   ├── GET  /github/login   # Initiate OAuth
│   ├── GET  /github/callback # OAuth callback
│   ├── POST /logout          # End session
│   ├── GET  /me              # Current user
│   └── POST /refresh         # Refresh token
│
├── /repos                   # Repository management
│   ├── GET  /                # List repositories
│   ├── GET  /:owner/:name    # Get repository
│   ├── PATCH /:owner/:name   # Update settings
│   ├── POST /:owner/:name/enable  # Enable AutoPR
│   └── POST /:owner/:name/disable # Disable AutoPR
│
├── /bots                    # Bot management
│   ├── GET  /exclusions      # List exclusions
│   ├── POST /exclusions      # Add exclusion
│   ├── DELETE /exclusions/:username # Remove
│   ├── GET  /comments        # Recent bot comments
│   └── GET  /analytics       # Bot statistics
│
├── /workflows               # Workflow management
│   ├── GET  /                # List workflows
│   ├── GET  /:id             # Get workflow
│   ├── PATCH /:id            # Update workflow
│   ├── GET  /:id/executions  # Execution history
│   └── POST /:id/trigger     # Manual trigger
│
├── /integrations            # Integration management
│   ├── GET  /                # List integrations
│   ├── GET  /:name           # Get integration
│   ├── PUT  /:name           # Configure
│   ├── POST /:name/test      # Test connection
│   └── DELETE /:name         # Disconnect
│
├── /settings                # User settings
│   ├── GET  /                # Get settings
│   ├── PATCH /               # Update settings
│   ├── GET  /api-keys        # List API keys
│   ├── POST /api-keys        # Create key
│   └── DELETE /api-keys/:id  # Revoke key
│
├── /activity                # Activity feed
│   ├── GET  /                # Recent activity
│   └── GET  /stats           # Dashboard stats
│
└── /health                  # Health checks (existing)
    ├── GET  /                # Quick health
    └── GET  /?detailed=true  # Detailed health
```

### Request/Response Format

#### Standard Response Envelope

```typescript
// Success response
{
  "data": T,           // Response payload
  "meta": {            // Optional metadata
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  }
}

// Error response
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [
      { "field": "username", "message": "Required" }
    ]
  }
}
```

#### HTTP Status Codes

| Code | Usage |
|------|-------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (successful delete) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (not logged in) |
| 403 | Forbidden (no permission) |
| 404 | Not Found |
| 409 | Conflict (duplicate) |
| 422 | Unprocessable Entity |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

### FastAPI Implementation

#### Router Structure

```python
# autopr/api/__init__.py
from fastapi import APIRouter

api_router = APIRouter(prefix="/api")

# Import and include sub-routers
from .auth import router as auth_router
from .repos import router as repos_router
from .bots import router as bots_router
from .workflows import router as workflows_router
from .integrations import router as integrations_router
from .settings import router as settings_router
from .activity import router as activity_router

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(repos_router, prefix="/repos", tags=["repos"])
api_router.include_router(bots_router, prefix="/bots", tags=["bots"])
api_router.include_router(workflows_router, prefix="/workflows", tags=["workflows"])
api_router.include_router(integrations_router, prefix="/integrations", tags=["integrations"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])
api_router.include_router(activity_router, prefix="/activity", tags=["activity"])
```

#### Response Models

```python
# autopr/api/models.py
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, List

T = TypeVar('T')

class PaginationMeta(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int

class ApiResponse(BaseModel, Generic[T]):
    data: T
    meta: Optional[PaginationMeta] = None

class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str

class ApiError(BaseModel):
    code: str
    message: str
    details: Optional[List[ErrorDetail]] = None

class ErrorResponse(BaseModel):
    error: ApiError
```

#### Example Endpoint

```python
# autopr/api/bots.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..auth import get_current_user
from ..models import User, BotExclusion
from .models import ApiResponse

router = APIRouter()

class BotExclusionCreate(BaseModel):
    username: str
    reason: Optional[str] = None

class BotExclusionResponse(BaseModel):
    id: str
    username: str
    reason: Optional[str]
    created_at: datetime

@router.get("/exclusions", response_model=ApiResponse[List[BotExclusionResponse]])
async def list_exclusions(
    user: User = Depends(get_current_user),
    page: int = 1,
    per_page: int = 20
):
    """List all bot exclusions for the current user."""
    exclusions = await BotExclusion.get_for_user(user.id, page, per_page)
    total = await BotExclusion.count_for_user(user.id)

    return ApiResponse(
        data=[BotExclusionResponse.from_orm(e) for e in exclusions],
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=(total + per_page - 1) // per_page
        )
    )

@router.post("/exclusions", response_model=ApiResponse[BotExclusionResponse], status_code=201)
async def add_exclusion(
    body: BotExclusionCreate,
    user: User = Depends(get_current_user)
):
    """Add a bot to the exclusion list."""
    # Check if already exists
    existing = await BotExclusion.get_by_username(user.id, body.username)
    if existing:
        raise HTTPException(status_code=409, detail="Bot already excluded")

    exclusion = await BotExclusion.create(
        user_id=user.id,
        username=body.username,
        reason=body.reason
    )
    return ApiResponse(data=BotExclusionResponse.from_orm(exclusion))

@router.delete("/exclusions/{username}", status_code=204)
async def remove_exclusion(
    username: str,
    user: User = Depends(get_current_user)
):
    """Remove a bot from the exclusion list."""
    deleted = await BotExclusion.delete_by_username(user.id, username)
    if not deleted:
        raise HTTPException(status_code=404, detail="Exclusion not found")
    return None
```

### Pagination

All list endpoints support cursor-based or offset pagination:

```
GET /api/repos?page=2&per_page=20
GET /api/activity?cursor=abc123&limit=50
```

### Filtering and Sorting

```
GET /api/repos?owner=JustAGhosT&enabled=true&sort=-updated_at
GET /api/bots/comments?repo=owner/repo&since=2025-01-01
```

### Rate Limiting

| Tier | Limit | Window |
|------|-------|--------|
| Unauthenticated | 10 req | 1 min |
| Free | 100 req | 1 min |
| Pro | 500 req | 1 min |
| Enterprise | 2000 req | 1 min |

Headers returned:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1735689600
```

### WebSocket (Future)

For real-time updates (activity feed, workflow status):

```
WS /api/ws/activity
WS /api/ws/workflows/:id
```

### OpenAPI Documentation

FastAPI auto-generates OpenAPI spec at `/api/docs` (Swagger UI) and `/api/redoc`.

```python
app = FastAPI(
    title="AutoPR Dashboard API",
    description="API for the AutoPR Dashboard",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)
```

## Consequences

### Positive

- **Consistency**: Standard patterns across all endpoints
- **Documentation**: Auto-generated OpenAPI docs
- **Type Safety**: Pydantic models ensure valid data
- **Testability**: Clear API contracts for testing
- **Flexibility**: Frontend can evolve independently

### Negative

- **Overhead**: More boilerplate for simple endpoints
- **Versioning**: Need strategy for breaking changes
- **N+1 Queries**: Must be careful with nested resources

### Neutral

- **Learning Curve**: Team needs to follow conventions
- **Monitoring**: Need API metrics and logging
- **Caching**: Consider response caching strategy

## Related Decisions

- [ADR-0004: API Versioning Strategy](0004-api-versioning-strategy.md)
- [ADR-0007: Authentication and Authorization](0007-authn-authz.md)
- [ADR-0019: Dashboard Frontend Architecture](0019-dashboard-frontend-architecture.md)
