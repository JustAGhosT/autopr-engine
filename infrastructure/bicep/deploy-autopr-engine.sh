#!/bin/bash
# Script to deploy AutoPR Engine infrastructure
# Creates resource group if it doesn't exist, then deploys the infrastructure

set -e

ENVIRONMENT=${1:-prod}
REGION_ABBR=${2:-san}
LOCATION=${3:-"eastus2"}
POSTGRES_LOCATION=${4:-"southafricanorth"}
CONTAINER_IMAGE=${5:-""}
RESOURCE_GROUP="prod-rg-${REGION_ABBR}-autopr"

# Use placeholder if no image specified
if [ -z "$CONTAINER_IMAGE" ]; then
  echo "⚠️  WARNING: No container image specified. Using placeholder image for testing."
  echo "   Build and push the image first, then update the Container App."
  echo "   See: infrastructure/bicep/BUILD_AND_PUSH_IMAGE.md"
  echo ""
  CONTAINER_IMAGE="mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
fi

echo "Deploying AutoPR Engine infrastructure..."
echo "Environment: $ENVIRONMENT"
echo "Region: $REGION_ABBR"
echo "Location: $LOCATION"
echo "Resource Group: $RESOURCE_GROUP"

# Check if resource group exists, create if not
if ! az group show --name "$RESOURCE_GROUP" &>/dev/null; then
  echo "Creating resource group..."
  az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --output none
else
  echo "Resource group already exists."
fi

# Generate passwords if not provided
if [ -z "$POSTGRES_PASSWORD" ]; then
  echo "Generating PostgreSQL password..."
  POSTGRES_PASSWORD=$(openssl rand -base64 32)
fi

if [ -z "$REDIS_PASSWORD" ]; then
  echo "Generating Redis password..."
  REDIS_PASSWORD=$(openssl rand -base64 32)
fi

# Deploy the infrastructure
echo "Deploying infrastructure..."
az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --template-file infrastructure/bicep/autopr-engine.bicep \
  --parameters \
    environment="$ENVIRONMENT" \
    regionAbbr="$REGION_ABBR" \
    location="$LOCATION" \
    postgresLocation="$POSTGRES_LOCATION" \
    containerImage="$CONTAINER_IMAGE" \
    postgresPassword="$POSTGRES_PASSWORD" \
    redisPassword="$REDIS_PASSWORD" \
  --output json > deployment-output.json

echo "Deployment complete!"
echo "PostgreSQL password: $POSTGRES_PASSWORD"
echo "Redis password: $REDIS_PASSWORD"
echo ""
echo "⚠️  IMPORTANT: Save these passwords securely!"
echo ""
echo "Container App URL:"
jq -r '.properties.outputs.containerAppUrl.value' deployment-output.json

