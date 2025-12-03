# GitHub App Integration

One-click installation and automatic secret configuration for AutoPR.

## Features

- **One-click installation** - Install AutoPR to repositories with a single click
- **Automatic secret configuration** - Secrets are configured automatically during installation
- **OAuth flow** - Secure GitHub App authentication
- **Webhook handling** - Receives and processes GitHub App events

## Setup

### 1. Create GitHub App

Follow the guide in `docs/GITHUB_APP_CONFIGURATION.md` to create your GitHub App.

### 2. Environment Variables

Add these to your `.env` or environment:

```env
# GitHub App Configuration
GITHUB_APP_ID=your_app_id
GITHUB_APP_CLIENT_ID=your_client_id
GITHUB_APP_CLIENT_SECRET=your_client_secret
GITHUB_APP_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----"
GITHUB_WEBHOOK_SECRET=your_webhook_secret
GITHUB_APP_REDIRECT_URI=https://your-app.azurewebsites.net/api/github-app/callback
GITHUB_APP_SLUG=autopr  # Your GitHub App slug

# Site Configuration
NEXT_PUBLIC_SITE_URL=https://your-app.azurewebsites.net

# Optional: Default secrets to configure automatically
DEFAULT_AZURE_CREDENTIALS=""
DEFAULT_AZURE_SUBSCRIPTION_ID=""
DEFAULT_POSTGRES_ADMIN_LOGIN=""
DEFAULT_POSTGRES_ADMIN_PASSWORD=""
DEFAULT_ADMIN_PASSWORD=""
```

### 3. Install Dependencies

PyNaCl is already included in the project dependencies. If you need to install manually:

```bash
poetry add pynacl
# or
pip install pynacl
```

### 4. Integration

The GitHub App routes are FastAPI routers. To integrate with Flask dashboard, you can:

**Option A: Use FastAPI alongside Flask (Recommended)**

Create a separate FastAPI app for GitHub App endpoints:

```python
from fastapi import FastAPI
from autopr.integrations.github_app import (
    install_router,
    callback_router,
    webhook_router,
    setup_router,
)

app = FastAPI()
app.include_router(install_router)
app.include_router(callback_router)
app.include_router(webhook_router)
app.include_router(setup_router)
```

**Option B: Mount FastAPI on Flask using WSGI**

Use `flask2fastapi` or similar to mount FastAPI routes on Flask.

**Option C: Convert to Flask routes**

Convert the FastAPI routers to Flask blueprints if you prefer Flask-only.

## API Endpoints

- `GET /api/github-app/install` - Initiate installation
- `GET /api/github-app/callback` - OAuth callback handler
- `POST /api/github-app/webhook` - Webhook event handler
- `GET /setup` - Setup completion page

## Usage

1. User clicks "Install" button → Redirects to `/api/github-app/install`
2. GitHub OAuth flow → User authorizes
3. Callback → `/api/github-app/callback` receives code
4. Webhook → GitHub sends installation event to `/api/github-app/webhook`
5. Auto-config → Secrets are configured automatically
6. Success → User redirected to `/setup` page

## Security

- Webhook signature verification using HMAC SHA-256
- Encrypted secret storage using PyNaCl (libsodium)
- Short-lived tokens
- HTTPS required in production

## Testing

Test locally using ngrok or similar:

```bash
# Expose localhost
ngrok http 8080

# Update GitHub App webhook URL to your ngrok URL
# Test installation flow
```

## Documentation

- `docs/GITHUB_APP_CONFIGURATION.md` - Complete configuration guide
- `docs/GITHUB_APP_SETUP.md` - Setup instructions
- `docs/GITHUB_APP_IMPLEMENTATION.md` - Implementation details
- `docs/GITHUB_APP_QUICK_FILL.md` - Quick fill guide for GitHub App form

