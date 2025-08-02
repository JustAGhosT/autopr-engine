# Environment Setup Guide

## Required Environment Variables

To use this project, you need to set up the following environment variables:

### Azure AI Services Configuration

```bash
# Azure OpenAI API Key (for GPT-4.1 and GPT-4o models)
export AZURE_OPENAI_KEY="your_azure_openai_api_key_here"

# Azure AI Services Key (for model-router)
export AZURE_AI_SERVICES_KEY="your_azure_ai_services_key_here"
```

### Optional: Azure Key Vault Configuration

```bash
# Azure Key Vault URL for secure key storage
export AZURE_KEY_VAULT_URL="https://your-keyvault.vault.azure.net/"
```

## Setting Up Environment Variables

### Option 1: Create a .env file (Recommended for development)

Create a `.env` file in the project root:

```bash
# .env
AZURE_OPENAI_KEY=your_azure_openai_api_key_here
AZURE_AI_SERVICES_KEY=your_azure_ai_services_key_here
```

**Important**: Add `.env` to your `.gitignore` file to prevent accidentally committing secrets.

### Option 2: System Environment Variables

Set the environment variables in your system:

#### Windows (PowerShell):

```powershell
$env:AZURE_OPENAI_KEY="your_azure_openai_api_key_here"
$env:AZURE_AI_SERVICES_KEY="your_azure_ai_services_key_here"
```

#### Windows (Command Prompt):

```cmd
set AZURE_OPENAI_KEY=your_azure_openai_api_key_here
set AZURE_AI_SERVICES_KEY=your_azure_ai_services_key_here
```

#### Linux/macOS:

```bash
export AZURE_OPENAI_KEY="your_azure_openai_api_key_here"
export AZURE_AI_SERVICES_KEY="your_azure_ai_services_key_here"
```

## Security Best Practices

1. **Never commit API keys to version control**
2. **Use environment variables instead of hardcoded values**
3. **Consider using Azure Key Vault for production environments**
4. **Rotate API keys regularly**
5. **Use least privilege principle for API key permissions**

## Troubleshooting

If you encounter issues with missing API keys:

1. Verify that environment variables are set correctly
2. Check that the `.env` file is in the project root (if using this method)
3. Restart your development environment after setting environment variables
4. Ensure you have the necessary Azure subscriptions and permissions

## Getting API Keys

### Azure OpenAI

1. Go to the Azure Portal
2. Navigate to your Azure OpenAI resource
3. Go to "Keys and Endpoint" in the left sidebar
4. Copy one of the keys

### Azure AI Services

1. Go to the Azure Portal
2. Navigate to your Azure AI Services resource
3. Go to "Keys and Endpoint" in the left sidebar
4. Copy one of the keys
