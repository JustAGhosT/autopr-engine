# Script to deploy AutoPR Engine infrastructure
# Creates resource group if it doesn't exist, then deploys the infrastructure

param(
    [string]$Environment = "prod",
    [string]$RegionAbbr = "san",
    [string]$Location = "eastus2",
    [string]$PostgresLocation = "southafricanorth"
)

$ErrorActionPreference = "Stop"

$ResourceGroup = "prod-rg-${RegionAbbr}-autopr"

Write-Host "Deploying AutoPR Engine infrastructure..."
Write-Host "Environment: $Environment"
Write-Host "Region: $RegionAbbr"
Write-Host "Location: $Location"
Write-Host "PostgreSQL Location: $PostgresLocation"
Write-Host "Resource Group: $ResourceGroup"
Write-Host ""

# Check if resource group exists, create if not
$rgExists = az group show --name $ResourceGroup 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating resource group..."
    az group create --name $ResourceGroup --location $Location --output none
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create resource group"
        exit 1
    }
} else {
    Write-Host "Resource group already exists."
}

# Generate passwords if not provided
if (-not $env:POSTGRES_PASSWORD) {
    Write-Host "Generating PostgreSQL password..."
    $env:POSTGRES_PASSWORD = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
}

if (-not $env:REDIS_PASSWORD) {
    Write-Host "Generating Redis password..."
    $env:REDIS_PASSWORD = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
}

# Get container image (use parameter or default)
$ContainerImage = if ($args.Count -gt 4) { $args[4] } else { "" }

if ([string]::IsNullOrEmpty($ContainerImage)) {
    Write-Host "⚠️  WARNING: No container image specified. Using placeholder image for testing." -ForegroundColor Yellow
    Write-Host "   Build and push the image first, then update the Container App." -ForegroundColor Yellow
    Write-Host "   See: infrastructure/bicep/BUILD_AND_PUSH_IMAGE.md" -ForegroundColor Yellow
    Write-Host ""
    $ContainerImage = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
}

# Deploy the infrastructure
Write-Host "Deploying infrastructure..."
Write-Host "Container Image: $ContainerImage"
Write-Host ""

az deployment group create `
    --resource-group $ResourceGroup `
    --template-file infrastructure/bicep/autopr-engine.bicep `
    --parameters `
        environment=$Environment `
        regionAbbr=$RegionAbbr `
        location=$Location `
        postgresLocation=$PostgresLocation `
        containerImage=$ContainerImage `
        postgresPassword="$env:POSTGRES_PASSWORD" `
        redisPassword="$env:REDIS_PASSWORD" `
    --output json | Out-File -FilePath deployment-output.json -Encoding utf8

if ($LASTEXITCODE -ne 0) {
    Write-Error "Deployment failed"
    exit 1
}

Write-Host ""
Write-Host "Deployment complete!"
Write-Host "PostgreSQL password: $env:POSTGRES_PASSWORD"
Write-Host "Redis password: $env:REDIS_PASSWORD"
Write-Host ""
Write-Host "⚠️  IMPORTANT: Save these passwords securely!"
Write-Host ""

# Get container app URL
$outputs = Get-Content deployment-output.json | ConvertFrom-Json
$containerAppUrl = $outputs.properties.outputs.containerAppUrl.value
Write-Host "Container App URL: $containerAppUrl"

