# GitHub App Setup Guide

This guide explains how to set up the GitHub App for one-click installation (like Codecov).

## Overview

The GitHub App provides a true "Install" button that allows users to:

- Install the app to their repository with one click
- Automatically configure secrets via OAuth
- Streamlined setup experience

## Architecture

``` text
User clicks "Install" → GitHub OAuth → Our App → Configure Secrets → Done
```

## Prerequisites

1. **GitHub App Registration**

   - Create a GitHub App at: <https://github.com/settings/apps/new>
   - Or use the manifest flow (see below)

2. **Hosting**
   - Azure Function App or Azure App Service
   - Public HTTPS endpoint for webhooks

3. **Secrets Storage**
   - Azure Key Vault or environment variables

## Step 1: Create GitHub App

### Option A: Using GitHub App Manifest (Recommended)

1. Go to: <https://github.com/settings/apps/new?manifest=1>
2. Use the manifest from `.github/app-manifest.yml`
3. GitHub will create the app automatically

### Option B: Manual Creation

1. Go to: <https://github.com/settings/apps/new>
2. Fill in:
   - **GitHub App name:** `Twines and Straps Setup`
   - **Homepage URL:** Your app URL
   - **Webhook URL:** `https://your-app.azurewebsites.net/api/webhook`
   - **Webhook secret:** Generate and store securely
   - **Permissions:**
     - Repository secrets: Read & Write
     - Repository metadata: Read-only
     - Contents: Read-only
   - **Subscribe to events:**
     - Installation
     - Installation repositories

3. Generate a private key and download it
4. Note your App ID

## Step 2: Deploy the Installation Handler

The installation handler is deployed as an Azure Function or Next.js API route.

### Environment Variables

Set these in Azure App Service/Function App:

```env
GITHUB_APP_ID=your_app_id
GITHUB_APP_PRIVATE_KEY=your_private_key
GITHUB_APP_CLIENT_ID=your_client_id
GITHUB_APP_CLIENT_SECRET=your_client_secret
WEBHOOK_SECRET=your_webhook_secret
AZURE_SUBSCRIPTION_ID=your_subscription_id
```

## Step 3: Installation Flow

1. User clicks "Install" button
2. GitHub redirects to OAuth flow
3. User authorizes the app
4. GitHub sends installation event to webhook
5. App configures secrets automatically
6. User is redirected to success page

## Step 4: Configure Secrets Automatically

The app uses GitHub API to set secrets:

```typescript
// After installation, configure secrets
await octokit.rest.actions.createOrUpdateRepoSecret({
  owner: installation.account.login,
  repo: repository.name,
  secret_name: 'AZURE_CREDENTIALS',
  encrypted_value: encryptedValue
});
```

## Testing

1. Install the app to a test repository
2. Verify secrets are created
3. Test the setup workflow

## Security Considerations

- Private key must be stored securely (Key Vault)
- Webhook secret validates requests
- OAuth tokens are short-lived
- Secrets are encrypted in transit

## Troubleshooting

- **Installation fails:** Check webhook URL is accessible
- **Secrets not created:** Verify app permissions
- **OAuth errors:** Check client ID/secret
