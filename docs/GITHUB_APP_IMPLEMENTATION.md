# GitHub App Implementation Guide

## Quick Start

### 1. Create GitHub App

Visit: <https://github.com/settings/apps/new?manifest=1>

Or use the manifest file: `.github/app-manifest.yml`

### 2. Configure Environment Variables

Add to your `.env` or Azure App Service:

```env
GITHUB_APP_ID=your_app_id
GITHUB_APP_PRIVATE_KEY=your_private_key
GITHUB_APP_CLIENT_ID=your_client_id
GITHUB_APP_CLIENT_SECRET=your_client_secret
GITHUB_WEBHOOK_SECRET=your_webhook_secret
GITHUB_APP_REDIRECT_URI=https://your-app.azurewebsites.net/api/github-app/callback
```

### 3. Deploy

The API routes are already created:

- `/api/github-app/install` - Initiates installation
- `/api/github-app/callback` - Handles OAuth callback
- `/api/github-app/webhook` - Receives webhook events
- `/setup` - Setup completion page

### 4. Add Install Button

Add to your README:

```markdown
[![Install App](https://img.shields.io/badge/Install-GitHub%20App-blue)](https://github.com/apps/twines-and-straps-setup/installations/new)
```

## How It Works

1. **User clicks "Install"** → Redirects to `/api/github-app/install`
2. **OAuth flow** → User authorizes on GitHub
3. **Callback** → `/api/github-app/callback` receives code
4. **Webhook** → GitHub sends installation event to `/api/github-app/webhook`
5. **Auto-config** → Secrets are configured automatically
6. **Success** → User redirected to `/setup` page

## Security

- Webhook signature verification
- Encrypted secret storage
- Short-lived tokens
- HTTPS required

## Testing Locally

1. Use ngrok or similar to expose localhost
2. Set webhook URL to your ngrok URL
3. Test installation flow

## Production Deployment

1. Deploy to Azure App Service
2. Configure environment variables
3. Update webhook URL in GitHub App settings
4. Test installation flow
