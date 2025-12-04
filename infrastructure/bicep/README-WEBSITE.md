# Azure Infrastructure for AutoPR Website

This directory contains the Azure Bicep infrastructure definitions for deploying the AutoPR Engine website to Azure Static Web Apps.

## Naming Convention

All resources follow the pattern: `{env}-{resourcetype}-{region}-autopr`

- **env**: Environment (prod, dev, staging)
- **resourcetype**: Resource type abbreviation (stapp for Static Web App, rg for Resource Group)
- **region**: Azure region abbreviation (eus for East US, wus for West US, etc.)
- **autopr**: Project identifier

### Examples

- `prod-stapp-san-autopr` - Production Static Web App (region: san)
- `prod-rg-san-autopr` - Resource Group (must be created before deployment)
- `dev-stapp-eus-autopr` - Development Static Web App in East US

**Note:** The resource group must be created before deploying the Static Web App. Use `az group create` to create it first.

## Deployment

### Prerequisites

1. Azure CLI installed and configured
2. Appropriate Azure subscription permissions
3. GitHub repository access token (for Static Web Apps integration)

### Deploy Infrastructure

```bash
# Login to Azure
az login

# Set your subscription
az account set --subscription <SUBSCRIPTION_ID>

# Create resource group first (if it doesn't exist)
# Note: Static Web Apps are only available in: westus2, centralus, eastus2, westeurope, eastasia
az group create \
  --name prod-rg-san-autopr \
  --location "eastus2"

# Deploy the infrastructure
az deployment group create \
  --resource-group prod-rg-san-autopr \
  --template-file infrastructure/bicep/website.bicep \
  --parameters @infrastructure/bicep/website-parameters.json

# Or use the deployment script
bash infrastructure/bicep/deploy-website.sh prod san "eastus2"
```

### Get Deployment Token

After deployment, retrieve the deployment token:

```bash
az staticwebapp secrets list \
  --name prod-stapp-san-autopr \
  --resource-group prod-rg-san-autopr \
  --query "properties.apiKey" \
  --output tsv
```

Add this token as `AZURE_STATIC_WEB_APPS_API_TOKEN` in your GitHub repository secrets.

### Configure Custom Domain

1. Get the domain validation token from Azure portal or CLI
2. Add the required DNS TXT record to your domain provider
3. Once validated, the custom domain will be automatically configured

```bash
# Get domain validation token
az staticwebapp hostname show \
  --name prod-stapp-san-autopr \
  --resource-group prod-rg-san-autopr \
  --hostname autopr.io
```

## Resource Details

### Static Web App

- **SKU**: Standard (supports custom domains)
- **Repository**: AutoPR Engine GitHub repository
- **Branch**: main
- **Build Configuration**:
  - App Location: `website`
  - Output Location: `out`
  - API Location: (empty, no API)

### Resource Group

- Contains all website-related resources
- Follows naming convention: `{env}-rg-{region}-autopr`

## Environment Variables

The following GitHub secrets are required for deployment:

- `AZURE_STATIC_WEB_APPS_API_TOKEN`: Deployment token from Azure Static Web App
- `AZURE_SUBSCRIPTION_ID`: Azure subscription ID
- `AZURE_CLIENT_ID`: Service principal client ID (for infrastructure deployment)
- `AZURE_CLIENT_SECRET`: Service principal client secret
- `AZURE_TENANT_ID`: Azure AD tenant ID

## Cost Estimation

- **Static Web App (Standard)**: ~$9/month
- **Custom Domain**: Included
- **Bandwidth**: 100 GB included, then $0.08/GB

Total estimated monthly cost: ~$9-15 depending on traffic.

