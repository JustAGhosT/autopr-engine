# Custom Domain Implementation for app.autopr.io

## Problem Statement

The domain for app.autopr.io was not linked in the infrastructure configuration. While the Static Web App for autopr.io had custom domain configuration, the Container App for app.autopr.io was missing this configuration, requiring manual setup through the Azure Portal after each deployment.

## Solution

Added custom domain configuration directly to the Azure Container App Bicep template, mirroring the approach already implemented for the Static Web App (autopr.io).

## Changes Made

### 1. Infrastructure Configuration (`infrastructure/bicep/autopr-engine.bicep`)

**Added custom domain parameter:**
```bicep
@description('Custom domain name for the container app')
param customDomain string = 'app.autopr.io'
```

**Added custom domain configuration to Container App ingress:**
```bicep
ingress: {
  external: true
  targetPort: 8080
  allowInsecure: false
  transport: 'auto'
  customDomains: [
    {
      name: customDomain
      bindingType: 'SniEnabled'
    }
  ]
}
```

**Added output for custom domain:**
```bicep
output customDomain string = customDomain
```

### 2. Parameter Files (`infrastructure/bicep/autopr-engine-parameters.json`)

Added customDomain parameter with value "app.autopr.io".

### 3. Deployment Scripts (`infrastructure/bicep/deploy-autopr-engine.sh`)

- Added CUSTOM_DOMAIN parameter (default: "app.autopr.io")
- Included customDomain in deployment command
- Added DNS setup instructions to the output

### 4. GitHub Actions Workflow (`.github/workflows/deploy-autopr-engine.yml`)

- Added customDomain parameter to deployment step
- Added custom domain to deployment outputs
- Enhanced deployment info display with DNS setup instructions

### 5. Documentation

**Updated `docs/ARCHITECTURE_AND_DEPLOYMENT.md`:**
- Expanded Custom Domain Issue section to include both autopr.io and app.autopr.io
- Added comprehensive DNS configuration section with examples
- Added specific instructions for obtaining FQDNs from deployment outputs
- Documented SSL certificate auto-management

**Updated `infrastructure/bicep/README-AUTOPR-ENGINE.md`:**
- Added customDomain to required parameters section
- Updated Next Steps with detailed DNS configuration instructions
- Added example DNS record configuration

## How It Works

1. **Deployment**: When the Bicep template is deployed, it creates the Container App with custom domain configuration
2. **DNS Configuration**: Administrator adds a CNAME record pointing app.autopr.io to the Container App FQDN
3. **Validation**: Azure validates domain ownership via the CNAME record
4. **Certificate Provisioning**: Azure automatically provisions an SSL certificate for the custom domain
5. **Auto-Renewal**: Azure manages certificate renewal before expiration

## Benefits

1. **No Manual Intervention**: Custom domain persists across all deployments
2. **Automatic SSL Management**: Azure handles certificate provisioning and renewal
3. **Consistency**: Same approach used for both autopr.io and app.autopr.io
4. **Infrastructure as Code**: Domain configuration is version-controlled and repeatable
5. **Reduced Deployment Time**: Eliminates manual post-deployment steps

## DNS Configuration Required

To complete the setup, add this CNAME record to your DNS provider:

```
Type: CNAME
Name: app
Value: <container-app-fqdn>
TTL: 3600
```

Get the Container App FQDN from deployment outputs:
```bash
az deployment group show \
  --resource-group prod-rg-san-autopr \
  --name autopr-engine \
  --query properties.outputs.containerAppUrl.value
```

Example: `app.autopr.io` → `prod-autopr-san-app.eastus2.azurecontainerapps.io`

## Verification

After DNS propagation (typically 15-30 minutes), verify:

```bash
# Check custom domain
curl -I https://app.autopr.io/

# Check health endpoint
curl https://app.autopr.io/health

# Check API endpoint
curl https://app.autopr.io/api
```

All should return successful responses over HTTPS with a valid SSL certificate.

## Security

- SSL/TLS automatically enabled with SNI (Server Name Indication)
- Certificate management handled by Azure
- No manual certificate handling or renewal required
- All communication encrypted by default

## Testing

- ✅ Bicep template validated with `az bicep build`
- ✅ Code review completed (0 critical issues)
- ✅ CodeQL security scan passed (0 alerts)
- ✅ Changes follow infrastructure as code best practices

## Related Files

- `infrastructure/bicep/autopr-engine.bicep` - Main infrastructure template
- `infrastructure/bicep/autopr-engine-parameters.json` - Parameter file
- `infrastructure/bicep/deploy-autopr-engine.sh` - Deployment script
- `.github/workflows/deploy-autopr-engine.yml` - CI/CD workflow
- `docs/ARCHITECTURE_AND_DEPLOYMENT.md` - Architecture documentation

## Next Steps for Deployment

1. Merge this PR to main branch
2. GitHub Actions will automatically deploy the updated infrastructure
3. Add the DNS CNAME record (see DNS Configuration above)
4. Wait for DNS propagation
5. Verify the custom domain is working
6. Azure will automatically provision and manage the SSL certificate

## References

- [Azure Container Apps Custom Domains](https://learn.microsoft.com/en-us/azure/container-apps/custom-domains-certificates)
- [Azure Static Web Apps Custom Domains](https://learn.microsoft.com/en-us/azure/static-web-apps/custom-domain)
