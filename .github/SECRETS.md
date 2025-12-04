# Required GitHub Secrets

This document lists the required GitHub Secrets for the CI/CD pipeline.

## Azure Credentials

- `AZURE_CREDENTIALS`: Azure service principal credentials for authenticating with Azure.
- `ACR_LOGIN_SERVER`: The login server for the Azure Container Registry.
- `ACR_USERNAME`: The username for the Azure Container Registry.
- `ACR_PASSWORD`: The password for the Azure Container Registry.

## API Keys

- `OPENAI_API_KEY`: The API key for the OpenAI service.

## Database

- `DATABASE_URL`: The connection string for the PostgreSQL database.
- `REDIS_URL`: The connection string for the Redis cache.
