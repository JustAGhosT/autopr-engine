# AutoPR Engine Website

Marketing and documentation website for AutoPR Engine, built with Next.js and deployed to Azure Static Web Apps.

## Features

- **Home Page**: Project promotion and key features
- **Installation Guide**: Step-by-step installation instructions
- **Integration Guide**: How to integrate with the deployed AutoPR instance at app.autopr.io
- **Download Page**: Links to various download methods

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm start
```

## Deployment

The website is automatically deployed to Azure Static Web Apps via GitHub Actions when changes are pushed to the `main` branch.

### Manual Deployment

1. Build the site:

   ```bash
   npm run build
   ```

2. Deploy using Azure Static Web Apps CLI:

   ```bash
   npm install -g @azure/static-web-apps-cli
   swa deploy ./out --deployment-token <YOUR_DEPLOYMENT_TOKEN>
   ```

## Infrastructure

The Azure infrastructure is defined in `infrastructure/bicep/website.bicep` using the naming convention:

- `{env}-stapp-{region}-autopr` - Static Web App
- `{env}-rg-{region}-autopr` - Resource Group (must be created before deployment)

Example: `prod-stapp-san-autopr` in resource group `prod-rg-san-autopr`

**Note:** The resource group must be created before deploying the Static Web App.

## Custom Domain

The website is configured for `autopr.io`. After deploying the infrastructure, configure the custom domain in the Azure portal or using Azure CLI.
