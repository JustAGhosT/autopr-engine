# 22. Dashboard Session Management

## Status

Accepted

## Context

The AutoPR Dashboard requires user authentication and session management. Since AutoPR is a GitHub-focused tool, we need to:

1. Authenticate users via GitHub OAuth
2. Maintain secure sessions across requests
3. Access GitHub API on behalf of users
4. Handle token refresh and expiration
5. Support "remember me" functionality
6. Enable secure logout

### Security Requirements

- No storage of plain-text credentials
- Protection against CSRF attacks
- Protection against XSS token theft
- Secure session invalidation
- Audit logging for auth events

## Decision

We implement a **GitHub OAuth + JWT session** system with the following architecture:

### Authentication Flow

```
┌──────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐
│  Browser │     │   FastAPI    │     │   GitHub    │     │  Redis   │
└────┬─────┘     └──────┬───────┘     └──────┬──────┘     └────┬─────┘
     │                  │                    │                  │
     │  1. Click Login  │                    │                  │
     │─────────────────►│                    │                  │
     │                  │                    │                  │
     │  2. Redirect to GitHub OAuth          │                  │
     │◄─────────────────│                    │                  │
     │                  │                    │                  │
     │  3. User authorizes app               │                  │
     │─────────────────────────────────────►│                  │
     │                  │                    │                  │
     │  4. Redirect with code                │                  │
     │◄─────────────────────────────────────│                  │
     │                  │                    │                  │
     │  5. Send code to callback             │                  │
     │─────────────────►│                    │                  │
     │                  │                    │                  │
     │                  │  6. Exchange code  │                  │
     │                  │───────────────────►│                  │
     │                  │                    │                  │
     │                  │  7. Access token   │                  │
     │                  │◄───────────────────│                  │
     │                  │                    │                  │
     │                  │  8. Get user info  │                  │
     │                  │───────────────────►│                  │
     │                  │                    │                  │
     │                  │  9. User profile   │                  │
     │                  │◄───────────────────│                  │
     │                  │                    │                  │
     │                  │ 10. Create/update user               │
     │                  │ 11. Create session ──────────────────►│
     │                  │                    │                  │
     │ 12. Set cookies  │                    │                  │
     │◄─────────────────│                    │                  │
     │                  │                    │                  │
     │ 13. Redirect to dashboard             │                  │
     │◄─────────────────│                    │                  │
```

### Session Storage Strategy

We use a **hybrid approach**:

| Data | Storage | Rationale |
|------|---------|-----------|
| Session ID | HttpOnly Cookie | Secure, CSRF protection |
| Session Data | Redis | Fast lookups, easy invalidation |
| GitHub Token | Encrypted in DB | Long-term storage, encrypted at rest |
| User Claims | JWT (optional) | Stateless verification for simple reads |

### Cookie Configuration

```python
# Session cookie settings
SESSION_COOKIE_CONFIG = {
    "key": "autopr_session",
    "httponly": True,          # Prevent XSS access
    "secure": True,            # HTTPS only in production
    "samesite": "lax",         # CSRF protection
    "max_age": 7 * 24 * 60 * 60,  # 7 days
    "path": "/",
    "domain": ".autopr.io",    # Shared across subdomains
}

# CSRF token cookie (readable by JS)
CSRF_COOKIE_CONFIG = {
    "key": "autopr_csrf",
    "httponly": False,         # JS needs to read this
    "secure": True,
    "samesite": "strict",
    "max_age": 24 * 60 * 60,   # 24 hours
}
```

### Implementation

#### OAuth Configuration

```python
# autopr/auth/oauth.py
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

config = Config('.env')

oauth = OAuth()
oauth.register(
    name='github',
    client_id=config('GITHUB_CLIENT_ID'),
    client_secret=config('GITHUB_CLIENT_SECRET'),
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={
        'scope': 'read:user user:email repo',
    },
)
```

#### Session Model

```python
# autopr/auth/session.py
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import secrets
import json
import redis

@dataclass
class Session:
    id: str
    user_id: str
    github_id: int
    github_login: str
    created_at: datetime
    expires_at: datetime
    last_active: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class SessionManager:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.session_ttl = timedelta(days=7)

    def create_session(
        self,
        user_id: str,
        github_id: int,
        github_login: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> Session:
        """Create a new session."""
        session_id = secrets.token_urlsafe(32)
        now = datetime.utcnow()

        session = Session(
            id=session_id,
            user_id=user_id,
            github_id=github_id,
            github_login=github_login,
            created_at=now,
            expires_at=now + self.session_ttl,
            last_active=now,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Store in Redis
        self.redis.setex(
            f"session:{session_id}",
            self.session_ttl,
            json.dumps(session.__dict__, default=str)
        )

        # Track user's active sessions
        self.redis.sadd(f"user_sessions:{user_id}", session_id)

        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by ID."""
        data = self.redis.get(f"session:{session_id}")
        if not data:
            return None

        session_data = json.loads(data)
        session = Session(**session_data)

        # Check expiration
        if datetime.fromisoformat(session.expires_at) < datetime.utcnow():
            self.delete_session(session_id)
            return None

        # Update last active
        session.last_active = datetime.utcnow()
        self.redis.setex(
            f"session:{session_id}",
            self.session_ttl,
            json.dumps(session.__dict__, default=str)
        )

        return session

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        data = self.redis.get(f"session:{session_id}")
        if data:
            session_data = json.loads(data)
            self.redis.srem(f"user_sessions:{session_data['user_id']}", session_id)
        return bool(self.redis.delete(f"session:{session_id}"))

    def delete_all_user_sessions(self, user_id: str) -> int:
        """Logout from all devices."""
        session_ids = self.redis.smembers(f"user_sessions:{user_id}")
        count = 0
        for sid in session_ids:
            if self.redis.delete(f"session:{sid.decode()}"):
                count += 1
        self.redis.delete(f"user_sessions:{user_id}")
        return count
```

#### Auth Routes

```python
# autopr/api/auth.py
from fastapi import APIRouter, Request, Response, HTTPException, Depends
from fastapi.responses import RedirectResponse

router = APIRouter()

@router.get("/github/login")
async def github_login(request: Request):
    """Initiate GitHub OAuth flow."""
    redirect_uri = request.url_for('github_callback')
    return await oauth.github.authorize_redirect(request, redirect_uri)

@router.get("/github/callback")
async def github_callback(request: Request, response: Response):
    """Handle GitHub OAuth callback."""
    try:
        token = await oauth.github.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail="OAuth failed")

    # Get user info from GitHub
    resp = await oauth.github.get('user', token=token)
    github_user = resp.json()

    # Create or update user in database
    user = await User.get_or_create(
        github_id=github_user['id'],
        defaults={
            'github_login': github_user['login'],
            'email': github_user.get('email'),
            'avatar_url': github_user.get('avatar_url'),
        }
    )

    # Store GitHub token (encrypted)
    await user.update_github_token(token['access_token'])

    # Create session
    session = session_manager.create_session(
        user_id=str(user.id),
        github_id=github_user['id'],
        github_login=github_user['login'],
        ip_address=request.client.host,
        user_agent=request.headers.get('user-agent'),
    )

    # Set session cookie
    response = RedirectResponse(url='/', status_code=302)
    response.set_cookie(**SESSION_COOKIE_CONFIG, value=session.id)

    # Audit log
    await audit_log.log('user.login', user_id=user.id, ip=request.client.host)

    return response

@router.post("/logout")
async def logout(request: Request, response: Response):
    """End the current session."""
    session_id = request.cookies.get('autopr_session')
    if session_id:
        session_manager.delete_session(session_id)

    response = Response(status_code=204)
    response.delete_cookie('autopr_session')
    return response

@router.get("/me")
async def get_current_user(user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return {
        "id": str(user.id),
        "github_login": user.github_login,
        "email": user.email,
        "avatar_url": user.avatar_url,
    }
```

#### Auth Dependency

```python
# autopr/auth/dependencies.py
from fastapi import Request, HTTPException, Depends

async def get_current_user(request: Request) -> User:
    """Get the current authenticated user from session."""
    session_id = request.cookies.get('autopr_session')
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")

    user = await User.get(id=session.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user

async def get_optional_user(request: Request) -> Optional[User]:
    """Get user if authenticated, None otherwise."""
    try:
        return await get_current_user(request)
    except HTTPException:
        return None
```

### GitHub Token Management

```python
# autopr/auth/github_token.py
from cryptography.fernet import Fernet
import os

class TokenManager:
    def __init__(self):
        self.key = os.getenv('TOKEN_ENCRYPTION_KEY')
        self.fernet = Fernet(self.key)

    def encrypt_token(self, token: str) -> str:
        return self.fernet.encrypt(token.encode()).decode()

    def decrypt_token(self, encrypted: str) -> str:
        return self.fernet.decrypt(encrypted.encode()).decode()

    async def get_github_client(self, user: User):
        """Get authenticated GitHub client for user."""
        encrypted_token = await user.get_github_token()
        if not encrypted_token:
            raise HTTPException(401, "GitHub not connected")

        token = self.decrypt_token(encrypted_token)

        # Check if token is still valid
        # Refresh if needed (GitHub App tokens)

        return Github(token)
```

### Security Measures

#### CSRF Protection

```python
# For state-changing operations
@router.post("/settings")
async def update_settings(
    request: Request,
    body: SettingsUpdate,
    user: User = Depends(get_current_user)
):
    # Verify CSRF token from header matches cookie
    csrf_cookie = request.cookies.get('autopr_csrf')
    csrf_header = request.headers.get('X-CSRF-Token')

    if not csrf_cookie or csrf_cookie != csrf_header:
        raise HTTPException(403, "CSRF validation failed")

    # Process request...
```

#### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/github/login")
@limiter.limit("10/minute")
async def github_login(request: Request):
    ...
```

### Database Schema

```sql
-- User table with encrypted token storage
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    github_id BIGINT UNIQUE NOT NULL,
    github_login VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    avatar_url TEXT,
    github_token_encrypted TEXT,  -- Fernet encrypted
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP
);

-- Audit log for security events
CREATE TABLE auth_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    event_type VARCHAR(50) NOT NULL,  -- 'login', 'logout', 'token_refresh'
    ip_address INET,
    user_agent TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_auth_audit_user ON auth_audit_log(user_id);
CREATE INDEX idx_auth_audit_created ON auth_audit_log(created_at DESC);
```

## Consequences

### Positive

- **Security**: HttpOnly cookies prevent XSS token theft
- **Scalability**: Redis sessions support horizontal scaling
- **Control**: Can invalidate sessions server-side
- **Audit**: Full login/logout history
- **UX**: "Remember me" with long session TTL

### Negative

- **Complexity**: More moving parts than stateless JWT
- **Redis Dependency**: Requires Redis for sessions
- **Token Storage**: Need encryption key management

### Neutral

- **Session Limits**: May need to limit concurrent sessions
- **Cleanup**: Need periodic cleanup of expired sessions
- **Monitoring**: Need to track session metrics

## Related Decisions

- [ADR-0007: Authentication and Authorization](0007-authn-authz.md)
- [ADR-0013: Security Strategy](0013-security-strategy.md)
- [ADR-0019: Dashboard Frontend Architecture](0019-dashboard-frontend-architecture.md)
