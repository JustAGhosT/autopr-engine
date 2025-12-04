# Required GitHub Secrets

This document lists the required GitHub Secrets for the CI/CD pipeline.

## Azure Credentials

- `AZURE_CREDENTIALS`: Azure service principal credentials for authenticating with Azure. This should be a JSON object with the following format:
  ```json
  {
    "clientId": "<app-id>",
    "clientSecret": "<password>",
    "subscriptionId": "<subscription-id>",
    "tenantId": "<tenant-id>"
  }
  ```
  
  To create this secret, run the following Azure CLI command:
  ```bash
  az ad sp create-for-rbac --name "github-actions-sp" --role contributor \
    --scopes /subscriptions/{subscription-id} \
    --json-auth
  ```
  
  Copy the entire JSON output and paste it as the value of the `AZURE_CREDENTIALS` secret in GitHub.

- `AZURE_STATIC_WEB_APPS_API_TOKEN`: The deployment token for Azure Static Web Apps.
- `ACR_LOGIN_SERVER`: The login server for the Azure Container Registry.
- `ACR_USERNAME`: The username for the Azure Container Registry.
- `ACR_PASSWORD`: The password for the Azure Container Registry.

## API Keys

- `OPENAI_API_KEY`: The API key for the OpenAI service.

## Database

- `DATABASE_URL`: The connection string for the PostgreSQL database.
- `REDIS_URL`: The connection string for the Redis cache.
