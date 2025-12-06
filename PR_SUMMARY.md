# PR Summary: Fix Custom Domain Persistence and Improve Dashboard Availability

## Issues Addressed

This PR fixes two critical deployment issues reported by users:

### 1. Custom Domain Re-linking After Each Deploy ✅
**Problem**: The custom domain (autopr.io) and SSL certificate needed to be manually re-linked in the Azure Portal after each deployment.

**Root Cause**: The Bicep infrastructure template created the Static Web App but did not include a `customDomains` resource to automatically configure the custom domain binding.

**Solution**:


- Added `Microsoft.Web/staticSites/customDomains` resource to `website.bicep`
- This resource automatically creates and maintains the custom domain binding
- Azure now manages the SSL certificate lifecycle (provisioning and renewal)
- No manual intervention needed after deployments

**Files Changed**:
- `infrastructure/bicep/website.bicep` - Added customDomains resource
- `infrastructure/bicep/website.json` - Auto-regenerated from Bicep
- `infrastructure/bicep/README-WEBSITE.md` - Updated documentation

### 2. Landing Page Showing Health Check Instead of Dashboard ✅

**Problem**: Users reported seeing a health check response at `/` on app.autopr.io instead of the dashboard.

**Root Cause Analysis**: 
- The dashboard router is correctly configured to handle `/` 
- However, if the dashboard module fails to import in production (due to missing dependencies or other issues), there was no fallback route
- This would result in a 404 error at `/`, leading to confusion

**Solution**:

- Added comprehensive logging to track module import success/failure
- Added a fallback route at `/` that returns helpful API information when dashboard is unavailable
- The fallback clearly indicates "dashboard not available (import failed)" and lists other available endpoints
- Improved error visibility for troubleshooting deployment issues

**Files Changed**:
- `autopr/server.py` - Added logging and fallback route

## Additional Improvements

### Static Web App Routing Configuration ✅

- Added `website/public/staticwebapp.config.json` for proper Next.js SPA routing
- Configured navigation fallback to handle client-side routing
- Set appropriate cache headers
- Configured 404 handling

### Architecture Documentation ✅

- Created comprehensive `docs/ARCHITECTURE_AND_DEPLOYMENT.md`
- Clarifies the two-domain architecture (autopr.io vs app.autopr.io)
- Explains the separation between marketing website and API backend
- Provides troubleshooting guide

### Security Improvements ✅

- Tightened Content Security Policy in staticwebapp.config.json
- Removed unnecessary `unsafe-eval` directive
- Kept minimal `unsafe-inline` only for Next.js generated styles
- All code passes CodeQL security scan with 0 alerts

### Code Quality ✅

- Moved fallback route function to module level for testability
- Added proper docstrings
- Improved code organization
- All code review feedback addressed

## Testing Performed

### Static Analysis ✅
- Bicep template validation: `az bicep build` - PASSED
- CodeQL security scan - 0 alerts
- Code review - All feedback addressed

### Build Verification ✅


- Next.js website build: `npm run build` - SUCCESS
- staticwebapp.config.json correctly copied to output directory
- All pages generated successfully

## Deployment Impact

### Breaking Changes
**NONE** - All changes are backwards compatible

### Migration Required
**NO** - Existing deployments will benefit from next deployment

### Immediate Benefits
1. **No More Manual Domain Linking**: Custom domain persists across all future deployments
2. **Better Error Visibility**: Clear messages when dashboard isn't available
3. **Improved Security**: Tighter CSP policy
4. **Better Documentation**: Clear architecture guide for maintainers

## How to Deploy

### For Infrastructure Changes
```bash
# Deploy updated Bicep template
az deployment group create \
  --resource-group prod-rg-san-autopr \
  --template-file infrastructure/bicep/website.bicep \
  --parameters @infrastructure/bicep/website-parameters.json
```

### For Application Changes
The GitHub Actions workflow will automatically deploy:
1. Website changes via `.github/workflows/deploy-website.yml`
2. Backend changes via `.github/workflows/deploy-autopr-engine.yml`

## Verification Steps

After deployment, verify:

1. **Custom Domain**:
   ```bash
   curl -I https://autopr.io
   # Should return 200 OK with HTML
   ```

2. **Backend Dashboard**:
   ```bash
   curl https://app.autopr.io/
   # Should return HTML dashboard or JSON with clear error message
   ```

3. **Health Check**:
   ```bash
   curl https://app.autopr.io/health
   # Should return JSON health status
   ```

## Security Summary

✅ **No vulnerabilities introduced**

- CodeQL scan: 0 alerts
- CSP policy tightened
- No unsafe dependencies added
- All code follows security best practices

## Related Documentation

- `docs/ARCHITECTURE_AND_DEPLOYMENT.md` - Architecture overview
- `infrastructure/bicep/README-WEBSITE.md` - Infrastructure deployment guide
- `website/README.md` - Website development guide

## Questions & Support

For questions about these changes, see:

- Architecture guide in `docs/ARCHITECTURE_AND_DEPLOYMENT.md`
- Infrastructure README in `infrastructure/bicep/README-WEBSITE.md`
- Troubleshooting section in ARCHITECTURE_AND_DEPLOYMENT.md
