# AutoPR Website Deployment Guide

This document describes the Next.js website and Azure deployment setup for autopr.io.

## Overview

The AutoPR Engine website is a Next.js application that provides:
- **Home Page**: Project promotion and key features
- **Installation Guide**: Step-by-step installation instructions  
- **Download Page**: Links to various download methods (GitHub, PyPI, Docker)

## Architecture

### Technology Stack

- **Framework**: Next.js 16+ with App Router
- **Styling**: Tailwind CSS 4
- **Deployment**: Azure Static Web Apps
- **CI/CD**: GitHub Actions

### Azure Resources

All resources follow the naming convention: `{env}-{resourcetype}-{region}-autopr`

#### Production Resources

- **Static Web App**: `prod-stapp-san-autopr`
- **Resource Group**: `prod-rg-san-autopr`
- **Location**: `eastus2` (East US 2) - Static Web Apps are only available in: westus2, centralus, eastus2, westeurope, eastasia
- **Custom Domain**: `autopr.io`

## Local Development

```bash
cd website
npm install
npm run dev
```

Visit `http://localhost:3000` to view the site.

## Deployment

### Automatic Deployment

The website is automatically deployed when:
- Changes are pushed to the `main` branch in the `website/` directory
- The workflow is manually triggered via `workflow_dispatch`

### Manual Deployment

1. **Build the site**:
   ```bash
   cd website
   npm run build
   ```

2. **Deploy using Azure CLI**:
   ```bash
   npm install -g @azure/static-web-apps-cli
   swa deploy ./out --deployment-token <YOUR_TOKEN>
   ```

### Infrastructure Deployment

To deploy the Azure infrastructure:

```bash
# Create resource group first (if it doesn't exist)
az group create \
  --name prod-rg-san-autopr \
  --location "eastus2"

# Deploy the Static Web App
az deployment group create \
  --resource-group prod-rg-san-autopr \
  --template-file infrastructure/bicep/website.bicep \
  --parameters @infrastructure/bicep/website-parameters.json
```

**Note:** The resource group must exist before deploying the Static Web App. The Static Web App will be created in the specified resource group.

## Configuration

### Required GitHub Secrets

- `AZURE_STATIC_WEB_APPS_API_TOKEN`: Deployment token from Azure Static Web App
- `AZURE_SUBSCRIPTION_ID`: Azure subscription ID
- `AZURE_CLIENT_ID`: Service principal client ID (for infrastructure deployment)
- `AZURE_CLIENT_SECRET`: Service principal client secret
- `AZURE_TENANT_ID`: Azure AD tenant ID

### Getting the Deployment Token

After creating the Static Web App, retrieve the deployment token:

```bash
az staticwebapp secrets list \
  --name prod-stapp-san-autopr \
  --resource-group prod-rg-san-autopr \
  --query "properties.apiKey" \
  --output tsv
```

## Custom Domain Setup

1. **Deploy the infrastructure** (if not already done)

2. **Get domain validation token**:
```bash
az staticwebapp hostname show \
  --name prod-stapp-san-autopr \
  --resource-group prod-rg-san-autopr \
  --hostname autopr.io
```

3. **Add DNS TXT record** to your domain provider:
   - Record type: TXT
   - Name: `asuid.autopr.io` (or as specified by Azure)
   - Value: (validation token from step 2)

4. **Wait for validation** (usually 5-10 minutes)

5. **Add CNAME record** (if not automatically created):
   - Record type: CNAME
   - Name: `autopr.io` (or `www.autopr.io`)
   - Value: `{static-web-app-name}.azurestaticapps.net`

## Project Structure

```
website/
├── app/
│   ├── page.tsx              # Home page
│   ├── installation/
│   │   └── page.tsx          # Installation guide
│   ├── download/
│   │   └── page.tsx          # Download page
│   ├── layout.tsx             # Root layout
│   └── globals.css           # Global styles
├── public/                   # Static assets
├── next.config.ts            # Next.js configuration
├── package.json
└── README.md

infrastructure/bicep/
├── website.bicep             # Azure infrastructure definition
├── website-parameters.json   # Deployment parameters
└── README-WEBSITE.md         # Infrastructure documentation

.github/workflows/
└── deploy-website.yml        # CI/CD pipeline
```

## Next.js Configuration

The site is configured for static export:

```typescript
// next.config.ts
{
  output: 'export',
  images: {
    unoptimized: true,
  },
  trailingSlash: true,
}
```

This ensures compatibility with Azure Static Web Apps.

## Monitoring

- **Azure Portal**: Monitor Static Web App metrics, logs, and performance
- **GitHub Actions**: View deployment status and logs
- **Custom Domain**: Monitor DNS and SSL certificate status

## Troubleshooting

### Build Failures

- Check Node.js version (requires 20+)
- Verify all dependencies are installed
- Review build logs in GitHub Actions

### Deployment Failures

- Verify `AZURE_STATIC_WEB_APPS_API_TOKEN` is correct
- Check Azure Static Web App exists and is accessible
- Review deployment logs in GitHub Actions

### Custom Domain Issues

- Verify DNS records are correct
- Check domain validation status in Azure Portal
- Ensure SSL certificate is provisioned (automatic for Static Web Apps)

## Cost Estimation

- **Static Web App (Standard)**: ~$9/month
- **Custom Domain**: Included
- **Bandwidth**: 100 GB included, then $0.08/GB

Total estimated monthly cost: ~$9-15 depending on traffic.

## References

- [Next.js Documentation](https://nextjs.org/docs)
- [Azure Static Web Apps Documentation](https://learn.microsoft.com/azure/static-web-apps/)
- [GitHub Actions for Azure](https://github.com/azure/login)

