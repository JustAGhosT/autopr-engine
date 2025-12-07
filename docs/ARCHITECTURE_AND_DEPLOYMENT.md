# AutoPR Architecture and Deployment Guide

## Domain Architecture

AutoPR uses a two-domain architecture to separate concerns:

### 1. **autopr.io** - Marketing Website (Static Web App)

- **Technology**: Next.js 16 (Static Site Generation)
- **Deployment**: Azure Static Web App
- **Purpose**: Marketing, documentation, downloads, integration guides
- **Routes**:
  - `/` - Homepage
  - `/installation` - Installation guide
  - `/integration` - Integration guide
  - `/download` - Download links

**Custom Domain Configuration**: Now automatically configured via Bicep template. Certificate is automatically managed by Azure.

### 2. **app.autopr.io** - Application Backend (Container App)

- **Technology**: FastAPI (Python 3.13)
- **Deployment**: Azure Container Apps
- **Purpose**: Backend API, GitHub App integration, dashboard
- **Routes**:
  - `/` - Dashboard UI (Python-based, Jinja2 templates)
  - `/api` - API information
  - `/health` - Health check endpoint
  - `/api/status` - Dashboard status API
  - `/api/quality-check` - Quality check API
  - `/api/github-app/*` - GitHub App integration endpoints

## Why Two Separate Domains?

1. **Performance**: Static website (autopr.io) is faster and globally distributed via Azure Static Web Apps CDN
2. **Scalability**: Backend (app.autopr.io) can scale independently based on API load
3. **Security**: API credentials and secrets are isolated to the backend
4. **Development**: Website and backend can be developed and deployed independently
5. **Cost**: Static Web Apps are cheaper for serving static content

## Dashboard Clarification

There are TWO dashboards in this project:

### Marketing Website Dashboard (Next.js)

- Location: `website/` directory
- Served at: **autopr.io**
- Purpose: Public-facing marketing and documentation
- Technology: React/Next.js with Tailwind CSS

### Application Dashboard (Python)

- Location: `autopr/dashboard/` directory  
- Served at: **app.autopr.io/**
- Purpose: Internal monitoring and quality checks
- Technology: FastAPI + Jinja2 templates
- Features: Real-time stats, quality checks, activity history

## Deployment Updates

### Custom Domain Issue - FIXED ✅

**Problem**: Custom domain and certificate needed to be re-linked after each deployment

**Solution**: Added custom domain configuration directly in the Bicep templates:

**For autopr.io (Static Web App)**:
- Added `Microsoft.Web/staticSites/customDomains` resource to `website.bicep`
- This resource automatically creates and maintains the custom domain binding
- Azure manages the SSL certificate lifecycle (provisioning and renewal)

**For app.autopr.io (Container App)**:
- Added `customDomains` configuration to the ingress settings in `autopr-engine.bicep`
- Specified `bindingType: 'SniEnabled'` for automatic SSL certificate management
- Azure manages the SSL certificate lifecycle (provisioning and renewal)

**How it works**:

1. Bicep template creates the resources (Static Web App and Container App)
2. Automatically adds custom domain binding configuration
3. Azure validates domain ownership via CNAME record
4. Azure provisions and manages SSL certificates automatically
5. No manual intervention needed after deployments

### Static Web App Routing - FIXED ✅

**Problem**: SPA routing wasn't configured properly

**Solution**: Added `staticwebapp.config.json` that:

- Configures fallback routing for Next.js
- Sets proper cache headers
- Handles 404 redirects to index.html
- Excludes API routes from fallback

## DNS Configuration

For custom domain setup, add these DNS records:

### autopr.io (Static Web App)
```
Type: CNAME
Name: autopr.io (or @ for root domain)
Value: <static-web-app-default-hostname>
TTL: 3600
```

The Static Web App default hostname can be found in the deployment outputs:
```bash
az deployment group show \
  --resource-group prod-rg-san-autopr \
  --name website \
  --query properties.outputs.staticWebAppUrl.value
```

### app.autopr.io (Container App)
```
Type: CNAME  
Name: app
Value: <container-app-fqdn>
TTL: 3600
```

The Container App FQDN can be found in the deployment outputs:
```bash
az deployment group show \
  --resource-group prod-rg-san-autopr \
  --name autopr-engine \
  --query properties.outputs.containerAppUrl.value
```

**Note:** After adding the DNS records:
1. Wait for DNS propagation (can take up to 48 hours, typically 15-30 minutes)
2. Azure will automatically provision and manage SSL certificates for both domains
3. Certificates are automatically renewed before expiration
4. No manual certificate management is required

## Verifying Deployments

### Check Website (autopr.io)

```bash
curl -I https://autopr.io
# Should return 200 OK with HTML content
```

### Check Backend (app.autopr.io)

```bash
# Dashboard
curl https://app.autopr.io/
# Should return HTML dashboard

# API
curl https://app.autopr.io/api
# Should return JSON with API info

# Health check
curl https://app.autopr.io/health
# Should return JSON health status
```

## Common Issues

### "Why is autopr.io not showing the website?"

- Check DNS propagation (can take up to 48 hours)
- Verify custom domain binding exists in Azure portal
- Check that website build deployed successfully in GitHub Actions
- Verify `staticwebapp.config.json` exists in the `out/` directory

### "Why is app.autopr.io showing a health check at /"

- This is incorrect - it should show the Python dashboard
- Check that `DASHBOARD_AVAILABLE` is True in server logs
- Verify `autopr/dashboard/templates/index.html` exists in container
- Check container logs for import errors

### "Certificate keeps expiring"

- Should not happen anymore with the new Bicep configuration
- Azure automatically renews certificates for custom domains
- Verify the `customDomains` resource exists in Bicep template

## Next Steps

1. Deploy updated infrastructure: `az deployment group create ...`
2. Wait for DNS propagation (if changing DNS)
3. Verify both domains are working
4. Monitor certificate auto-renewal

## Related Files

- `infrastructure/bicep/website.bicep` - Static Web App infrastructure
- `infrastructure/bicep/autopr-engine.bicep` - Container App infrastructure  
- `website/public/staticwebapp.config.json` - Routing configuration
- `autopr/server.py` - FastAPI application entry point
- `autopr/dashboard/router.py` - Dashboard routes
