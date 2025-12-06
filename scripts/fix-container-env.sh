#!/bin/bash
# Script to fix container app environment variables after manual image update
# Usage: ./scripts/fix-container-env.sh

set -e

RESOURCE_GROUP="prod-rg-san-autopr"
CONTAINER_APP="prod-autopr-san-app"
REDIS_NAME="prod-autopr-san-redis"

echo "Fetching resource information..."

# Get PostgreSQL FQDN
POSTGRES_FQDN=$(az postgres flexible-server list -g $RESOURCE_GROUP --query "[0].fullyQualifiedDomainName" -o tsv)
echo "PostgreSQL FQDN: $POSTGRES_FQDN"

# Get Redis hostname
REDIS_HOST=$(az redis show -n $REDIS_NAME -g $RESOURCE_GROUP --query "hostName" -o tsv)
echo "Redis Host: $REDIS_HOST"

# Get Redis primary key
REDIS_KEY=$(az redis list-keys -n $REDIS_NAME -g $RESOURCE_GROUP --query "primaryKey" -o tsv)
echo "Redis Key: Retrieved"

echo ""
echo "Updating container app environment variables..."

az containerapp update \
  -n $CONTAINER_APP \
  -g $RESOURCE_GROUP \
  --set-env-vars \
    AUTOPR_ENV=prod \
    HOST=0.0.0.0 \
    PORT=8080 \
    POSTGRES_HOST="$POSTGRES_FQDN" \
    POSTGRES_PORT=5432 \
    POSTGRES_DB=autopr \
    POSTGRES_USER=autopr \
    POSTGRES_SSLMODE=require \
    REDIS_HOST="$REDIS_HOST" \
    REDIS_PORT=6380 \
    REDIS_SSL=true

echo ""
echo "Environment variables updated. Checking revision status..."

# Wait for new revision
sleep 10

az containerapp revision list -n $CONTAINER_APP -g $RESOURCE_GROUP --query "[0].{name:name, active:properties.active, healthy:properties.runningState}" -o table

echo ""
echo "Done! Check the Azure portal for container logs if issues persist."
echo ""
echo "NOTE: POSTGRES_PASSWORD and REDIS_PASSWORD are managed as secrets."
echo "If the container still can't connect to the database, you may need to reset the PostgreSQL password."
