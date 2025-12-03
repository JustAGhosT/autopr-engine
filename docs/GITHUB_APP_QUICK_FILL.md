# GitHub App Registration - Quick Fill Guide

Fill out the form step by step. Use your deployed app URL or localhost for testing.

## ✅ What You've Already Done

- **App name:** `AutoPR` ✓
- **Expire user authorization tokens:** ✅ Checked ✓
- **Enable Device Flow:** ❌ Unchecked ✓

## 📝 What to Fill In Now

### 1. Description

Replace the current description with:

```
Automated setup and configuration for Twines and Straps SA platform.
One-click installation that automatically configures Azure secrets and GitHub Actions workflows.
```

### 2. Homepage URL

**If your app is deployed:**
```
https://dev-app-san-tassa.azurewebsites.net
```

**If testing locally (use GitHub repo URL):**
```
https://github.com/JustAGhosT/twinesandstraps
```

### 3. Callback URL

**If your app is deployed:**
```
https://dev-app-san-tassa.azurewebsites.net/api/github-app/callback
```

**If testing locally:**
```
http://localhost:3000/api/github-app/callback
```

### 4. Request user authorization (OAuth) during installation

✅ **CHECK THIS BOX** - You need this to identify the installing user

### 5. Setup URL (optional)

**If your app is deployed:**
```
https://dev-app-san-tassa.azurewebsites.net/setup
```

**If testing locally:**
```
http://localhost:3000/setup
```

### 6. Redirect on update

✅ **CHECK THIS BOX** - Redirects users when repos are added/removed

### 7. Webhook URL

**If your app is deployed:**
```
https://dev-app-san-tassa.azurewebsites.net/api/github-app/webhook
```

**If testing locally (use ngrok):**
```
https://your-ngrok-url.ngrok.io/api/github-app/webhook
```

### 8. Webhook Secret

Generate a secret (run this in PowerShell or terminal):

```powershell
# PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

Or use OpenSSL:
```bash
openssl rand -hex 32
```

**⚠️ SAVE THIS SECRET!** You'll need it for `GITHUB_WEBHOOK_SECRET` environment variable.

### 9. Permissions

Click to expand **Repository permissions** and set:

- **Secrets:** `Read and write` ✅
- **Metadata:** `Read-only` ✅
- **Contents:** `Read-only` ✅
- **Actions:** `Read-only` (optional)
- Everything else: `No access`

**Organization permissions:** Leave all as `No access`

**Account permissions:** Leave all as `No access`

### 10. Subscribe to Events

Check these boxes:

- ✅ **Installation** - When app is installed/uninstalled
- ✅ **Installation repositories** - When repos are added/removed

Leave everything else unchecked.

### 11. Where can this GitHub App be installed?

Select: **✅ Any account** (recommended)

Or if you only want it on your account: **Only on this account**

---

## 🎯 Quick Summary

**Required Fields:**
- ✅ App name: `AutoPR`
- ✅ Description: (see above)
- ✅ Homepage URL: Your app URL or GitHub repo
- ✅ Callback URL: Your app URL + `/api/github-app/callback`
- ✅ Setup URL: Your app URL + `/setup`
- ✅ Webhook URL: Your app URL + `/api/github-app/webhook`
- ✅ Webhook Secret: Generate one (save it!)
- ✅ Permissions: Secrets (write), Metadata (read), Contents (read)
- ✅ Events: Installation, Installation repositories

**Checkboxes:**
- ✅ Expire user authorization tokens
- ✅ Request user authorization (OAuth) during installation
- ✅ Redirect on update
- ✅ Active (webhook)

**Unchecked:**
- ❌ Enable Device Flow

---

## 🚀 After Creating the App

You'll get:
1. **App ID** → Save as `GITHUB_APP_ID`
2. **Client ID** → Save as `GITHUB_APP_CLIENT_ID`
3. **Client Secret** → Save as `GITHUB_APP_CLIENT_SECRET`
4. **Private Key** → Download .pem file → Save as `GITHUB_APP_PRIVATE_KEY`
5. **Webhook Secret** → The one you generated → Save as `GITHUB_WEBHOOK_SECRET`

Add all of these to your Azure App Service environment variables or `.env.local` file.

