# GitHub App Configuration Guide

Complete settings for creating the "AutoPR" GitHub App.

## Basic Information

### GitHub App name

```text
AutoPR
```

### Homepage URL

```text
https://github.com/JustAGhosT/twinesandstraps
```

Or your production app URL if deployed:

```text
https://dev-app-san-tassa.azurewebsites.net
```

### Description (Markdown supported)

```markdown
Automated setup and configuration for Twines and Straps SA platform.
One-click installation that automatically configures Azure secrets and GitHub Actions workflows.
```

## Identifying and Authorizing Users

### Callback URL

```text
https://dev-app-san-tassa.azurewebsites.net/api/github-app/callback
```

Or for local development:

```text
http://localhost:3000/api/github-app/callback
```

### Expire user authorization tokens

✅ **Check this box** - Provides refresh tokens for long-lived access

### Request user authorization (OAuth) during installation

✅ **Check this box** - Allows identifying the installing user

### Enable Device Flow

❌ **Leave unchecked** - Not needed for web-based installation

## Post Installation

### Setup URL (optional)

```text
https://dev-app-san-tassa.azurewebsites.net/setup
```

Or for local development:

```text
http://localhost:3000/setup
```

### Redirect on update

✅ **Check this box** - Redirects users when repositories are added/removed

## Webhook

### Active

✅ **Check this box** - Enable webhook events

### Webhook URL

```text
https://dev-app-san-tassa.azurewebsites.net/api/github-app/webhook
```

Or for local development (use ngrok):

```text
https://your-ngrok-url.ngrok.io/api/github-app/webhook
```

### Secret

Generate a strong random secret (save this securely):

```text
ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Or generate using:

```bash
openssl rand -hex 32
```

**⚠️ IMPORTANT:** Save this secret - you'll need it for the `GITHUB_WEBHOOK_SECRET` environment variable!

## Permissions

### Repository Permissions

| Permission        | Access Level   | Reason                                             |
| ----------------- | -------------- | -------------------------------------------------- |
| **Secrets**       | Read and write | Required to configure GitHub secrets automatically |
| **Metadata**      | Read-only      | Required to access repository information          |
| **Contents**      | Read-only      | Required to read repository structure              |
| **Actions**       | Read-only      | Optional - for checking workflow status            |
| **Pull requests** | No access      | Not needed for setup                               |
| **Issues**        | No access      | Not needed for setup                               |

**Minimum Required:**

- Secrets: **Read and write** ✅
- Metadata: **Read-only** ✅
- Contents: **Read-only** ✅

### Organization Permissions

Leave all as **No access** (unless you need organization-wide installation)

### Account Permissions

Leave all as **No access** (unless you need user-specific data)

## Subscribe to Events

Based on the permissions selected, subscribe to:

✅ **Installation** - When the app is installed/uninstalled

✅ **Installation repositories** - When repositories are added/removed from installation

**Optional (if you want more features):**

- ❌ Push (not needed for setup)
- ❌ Pull request (not needed for setup)
- ❌ Issues (not needed for setup)

## Installation Target

### Where can this GitHub App be installed?

**Recommended:** ✅ **Any account**

This allows:

- Users to install on their personal accounts
- Organizations to install on their org accounts
- Maximum flexibility

**Alternative:** If you only want it on your account:

- ❌ **Only on this account** (@JustAGhosT)

## Summary Checklist

After creating the app, you'll receive:

- [ ] **App ID** - Save for `GITHUB_APP_ID`
- [ ] **Client ID** - Save for `GITHUB_APP_CLIENT_ID`
- [ ] **Client Secret** - Save for `GITHUB_APP_CLIENT_SECRET`
- [ ] **Private Key** - Download .pem file, save for `GITHUB_APP_PRIVATE_KEY`
- [ ] **Webhook Secret** - The one you generated, save for `GITHUB_WEBHOOK_SECRET`

## Environment Variables

After creating the app, add these to your `.env.local` or Azure App Service:

```env
# GitHub App Configuration
GITHUB_APP_ID=123456
GITHUB_APP_CLIENT_ID=Iv1.xxxxxxxxxxxxxxxx
GITHUB_APP_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_APP_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----"
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here
GITHUB_APP_REDIRECT_URI=https://dev-app-san-tassa.azurewebsites.net/api/github-app/callback

# Optional: Default secrets to configure (if you want to auto-populate)
DEFAULT_AZURE_CREDENTIALS=""
DEFAULT_AZURE_SUBSCRIPTION_ID=""
DEFAULT_POSTGRES_ADMIN_LOGIN=""
DEFAULT_POSTGRES_ADMIN_PASSWORD=""
DEFAULT_ADMIN_PASSWORD=""
```

## Testing the Configuration

1. **Test Installation:**

   ```text
   https://github.com/apps/autopr/installations/new
   ```

2. **Verify Webhook:**

   - Install the app to a test repository
   - Check webhook deliveries in GitHub App settings
   - Verify events are received at your webhook URL

3. **Check Secrets:**

   - After installation, verify secrets are created in the repository
   - Go to: Repository → Settings → Secrets and variables → Actions

## Troubleshooting

### Webhook not receiving events

- ✅ Verify webhook URL is publicly accessible (HTTPS required)
- ✅ Check webhook secret matches in both GitHub and your app
- ✅ Verify webhook is "Active" in GitHub App settings

### Installation fails

- ✅ Check callback URL is correct
- ✅ Verify OAuth client ID/secret are correct
- ✅ Ensure app has required permissions

### Secrets not being set

- ✅ Verify app has "Secrets: Read and write" permission
- ✅ Check installation has access to the repository
- ✅ Verify encryption is working (libsodium-wrappers installed)

## Next Steps

1. Create the GitHub App with these settings
2. Save all credentials securely
3. Configure environment variables
4. Deploy your app
5. Test the installation flow
6. Add install button to README

## Install Button

Add this to your README after creating the app:

```markdown
[![Install AutoPR](https://img.shields.io/badge/Install-AutoPR-28a745?style=for-the-badge)](https://github.com/apps/autopr/installations/new)
```

Replace `autopr` with your actual app slug (GitHub will show this after creation).
