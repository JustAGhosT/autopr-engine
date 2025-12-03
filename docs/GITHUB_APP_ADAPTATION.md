# GitHub App Code Adaptation Guide

## ⚠️ Important Note

The GitHub App code was migrated from a **Next.js/TypeScript** project (`twinesandstraps`) to `autopr-engine`, which is a **Python/FastAPI** project. The code needs to be adapted.

## Current Situation

The following files were copied but are in **Next.js format**:

- `src/app/api/github-app/install/route.ts` - Next.js API route
- `src/app/api/github-app/callback/route.ts` - Next.js API route  
- `src/app/api/github-app/webhook/route.ts` - Next.js API route
- `src/app/setup/page.tsx` - Next.js React page
- `src/lib/github-secrets.ts` - TypeScript utility

## Options

### Option 1: Convert to FastAPI (Recommended)

Convert the Next.js routes to FastAPI endpoints in `autopr/`:

**Structure:**
```
autopr/
  integrations/
    github_app/
      __init__.py
      install.py      # /api/github-app/install
      callback.py     # /api/github-app/callback
      webhook.py      # /api/github-app/webhook
      secrets.py      # Secret encryption utilities
      setup.py        # Setup page handler
```

**Dependencies needed:**
```toml
# Add to pyproject.toml
octokit = "^2.0.0"  # Python GitHub SDK
pynacl = "^1.5.0"   # For libsodium encryption
```

### Option 2: Use autopr-desktop (React/TypeScript)

The `autopr-desktop` folder is a React/TypeScript project. You could:
1. Move the GitHub App code to `autopr-desktop/src/`
2. Set up Next.js in autopr-desktop
3. Deploy as a separate service

### Option 3: Standalone Next.js Service

Create a separate Next.js microservice for the GitHub App:
- Deploy separately
- Call autopr-engine APIs when needed
- Keep the code as-is

## Recommended: FastAPI Conversion

Since autopr-engine already has:
- FastAPI/Flask infrastructure (dashboard/server.py)
- GitHub client (`autopr/clients/github_client.py`)
- Integration system (`autopr/integrations/`)

**Best approach:** Convert to FastAPI and integrate with existing infrastructure.

## Next Steps

1. **Review the copied files** to understand the functionality
2. **Convert TypeScript to Python**:
   - `route.ts` → FastAPI route handlers
   - `github-secrets.ts` → Python encryption using `pynacl`
   - `page.tsx` → HTML template or API response
3. **Integrate with existing autopr-engine**:
   - Use `autopr/clients/github_client.py` if possible
   - Add to `autopr/integrations/` registry
4. **Update dependencies** in `pyproject.toml`
5. **Test the endpoints**

## Reference Files

The original Next.js code is in:
- `src/app/api/github-app/` (routes)
- `src/app/setup/` (frontend)
- `src/lib/github-secrets.ts` (utilities)

Use these as reference when converting to Python/FastAPI.

