# Infrastructure as Code

This directory contains the Infrastructure as Code (IaC) for the AutoPR project, defining the necessary Azure resources to run the application in a production environment.

## Infrastructure Components

### 1. AutoPR Engine Application (`bicep/autopr-engine.bicep`)

Production-ready infrastructure for the AutoPR Engine application:
- **Azure Container Apps**: Serverless container hosting
- **Azure Database for PostgreSQL**: Primary database
- **Azure Cache for Redis**: Caching and session storage
- **Log Analytics Workspace**: Centralized logging

See [README-AUTOPR-ENGINE.md](bicep/README-AUTOPR-ENGINE.md) for deployment instructions.

### 2. Website (`bicep/website.bicep`)

Marketing website infrastructure:
- **Azure Static Web Apps**: Hosting for Next.js website

See [README-WEBSITE.md](bicep/README-WEBSITE.md) for deployment instructions.

### 3. Legacy Infrastructure (`bicep/main.bicep`)

Original infrastructure template (AKS, ACR, PostgreSQL, Redis):
- **Azure Kubernetes Service (AKS)**: Container orchestration
- **Azure Container Registry (ACR)**: Container image storage
- **PostgreSQL**: Database server
- **Redis**: Cache server

## Deployment Options

### Bicep (Recommended for Azure)

Bicep is the native Azure IaC language and is recommended for Azure deployments:

**AutoPR Engine:**
```bash
bash infrastructure/bicep/deploy-autopr-engine.sh prod san "eastus2"
```

**Website:**
```bash
az group create --name prod-rg-san-autopr --location "eastus2"
az deployment group create \
  --resource-group prod-rg-san-autopr \
  --template-file infrastructure/bicep/website.bicep \
  --parameters @infrastructure/bicep/website-parameters.json
```

### Terraform

Terraform is located in the `terraform` directory and provides a cloud-agnostic option:

```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

## Naming Convention

All resources follow the pattern: `{env}-{resourcetype}-{region}-autopr`

- **env**: Environment (prod, dev, staging)
- **resourcetype**: Resource type abbreviation (stapp, autopr, rg, etc.)
- **region**: Azure region abbreviation (san, eus, wus, etc.)

Examples:
- `prod-stapp-san-autopr` - Static Web App
- `prod-autopr-san-app` - Container App
- `prod-rg-san-autopr` - Resource Group
