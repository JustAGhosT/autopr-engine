<#
.SYNOPSIS
    Complete setup script for AutoPR Engine deployment to Azure.

.DESCRIPTION
    This script performs the full deployment of AutoPR Engine including:
    1. Creating Azure resource group
    2. Deploying infrastructure via Bicep templates
    3. Triggering GitHub Actions deployment (optional)
    4. Configuring custom domain for app.autopr.io
    5. Adding GitHub App credentials to Container App

.PARAMETER Environment
    Environment name (prod, dev, staging). Default: prod

.PARAMETER RegionAbbr
    Azure region abbreviation. Default: san

.PARAMETER Location
    Azure region for deployment. Default: eastus2

.PARAMETER CustomDomain
    Custom domain for the app (e.g., app.autopr.io). Optional.

.PARAMETER GitHubAppId
    GitHub App ID. Required for GitHub App integration.

.PARAMETER GitHubAppPrivateKeyPath
    Path to GitHub App private key .pem file. Required for GitHub App integration.

.PARAMETER GitHubWebhookSecret
    GitHub webhook secret. Required for GitHub App integration.

.PARAMETER SkipInfrastructure
    Skip infrastructure deployment (useful when updating credentials only).

.PARAMETER TriggerGitHubWorkflow
    Trigger GitHub Actions workflow instead of local deployment.

.EXAMPLE
    .\setup-autopr-complete.ps1 -GitHubAppId "123456" -GitHubAppPrivateKeyPath ".\private-key.pem" -GitHubWebhookSecret "secret123"

.EXAMPLE
    .\setup-autopr-complete.ps1 -CustomDomain "app.autopr.io" -TriggerGitHubWorkflow

.NOTES
    Prerequisites:
    - Azure CLI installed and logged in (az login)
    - GitHub CLI installed and authenticated (gh auth login) - if using TriggerGitHubWorkflow
    - Appropriate Azure subscription permissions
#>

param(
    [string]$Environment = "prod",
    [string]$RegionAbbr = "san",
    [string]$Location = "eastus2",
    [string]$PostgresLocation = "southafricanorth",
    [string]$CustomDomain = "",
    [string]$GitHubAppId = "",
    [string]$GitHubAppPrivateKeyPath = "",
    [string]$GitHubWebhookSecret = "",
    [string]$RepoOwner = "JustAGhosT",
    [string]$RepoName = "autopr-engine",
    [string]$ContainerImage = "",
    [switch]$SkipInfrastructure,
    [switch]$TriggerGitHubWorkflow
)

$ErrorActionPreference = "Stop"

# Configuration
$ResourceGroup = "${Environment}-rg-${RegionAbbr}-autopr"
$ContainerAppName = "${Environment}-autopr-${RegionAbbr}-app"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  AutoPR Engine Complete Setup Script" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:"
Write-Host "  Environment:    $Environment"
Write-Host "  Region:         $RegionAbbr"
Write-Host "  Location:       $Location"
Write-Host "  Resource Group: $ResourceGroup"
Write-Host "  Container App:  $ContainerAppName"
if ($CustomDomain) { Write-Host "  Custom Domain:  $CustomDomain" }
Write-Host ""

# Step 1: Verify Azure CLI is logged in
Write-Host "Step 1: Verifying Azure CLI authentication..." -ForegroundColor Yellow
$accountJson = az account show 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Azure CLI not logged in. Run 'az login' first."
    exit 1
}
try {
    $account = $accountJson | ConvertFrom-Json
    Write-Host "  ✅ Logged in as: $($account.user.name)" -ForegroundColor Green
    Write-Host "  ✅ Subscription: $($account.name)" -ForegroundColor Green
} catch {
    Write-Error "Failed to parse Azure account info. Run 'az login' to authenticate."
    exit 1
}

# Step 2: Create Resource Group
Write-Host ""
Write-Host "Step 2: Creating resource group..." -ForegroundColor Yellow
$rgExists = az group exists --name $ResourceGroup 2>&1
if ($rgExists -eq "true") {
    Write-Host "  ✅ Resource group already exists" -ForegroundColor Green
} else {
    az group create --name $ResourceGroup --location $Location --output none
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Resource group created" -ForegroundColor Green
    } else {
        Write-Error "Failed to create resource group"
        exit 1
    }
}

# Step 3: Deploy Infrastructure or Trigger GitHub Workflow
if (-not $SkipInfrastructure) {
    Write-Host ""
    Write-Host "Step 3: Deploying infrastructure..." -ForegroundColor Yellow
    
    if ($TriggerGitHubWorkflow) {
        # Trigger GitHub Actions workflow
        Write-Host "  Triggering GitHub Actions workflow..."
        
        # Check if gh CLI is available
        try {
            gh --version | Out-Null
        } catch {
            Write-Error "GitHub CLI (gh) not installed. Install from https://cli.github.com/"
            exit 1
        }
        
        gh workflow run deploy-autopr-engine.yml --repo "$RepoOwner/$RepoName"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ Workflow triggered successfully" -ForegroundColor Green
            Write-Host "  📋 View progress: https://github.com/$RepoOwner/$RepoName/actions" -ForegroundColor Cyan
        } else {
            Write-Error "Failed to trigger workflow"
            exit 1
        }
    } else {
        # Deploy locally using Bicep
        Write-Host "  Deploying via Bicep templates..."
        
        # Generate passwords using cryptographically secure random generation
        Add-Type -AssemblyName System.Security
        $rng = [System.Security.Cryptography.RNGCryptoServiceProvider]::new()
        $bytes = New-Object byte[] 32
        $rng.GetBytes($bytes)
        $PostgresPassword = [Convert]::ToBase64String($bytes)
        $rng.GetBytes($bytes)
        $RedisPassword = [Convert]::ToBase64String($bytes)
        $rng.Dispose()
        
        # Use provided container image or placeholder for initial deployment
        if ([string]::IsNullOrEmpty($ContainerImage)) {
            Write-Host "  ⚠️  No container image specified. Using placeholder for initial deployment." -ForegroundColor Yellow
            $DeployContainerImage = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
        } else {
            $DeployContainerImage = $ContainerImage
        }
        
        az deployment group create `
            --name autopr-engine `
            --resource-group $ResourceGroup `
            --template-file infrastructure/bicep/autopr-engine.bicep `
            --parameters `
                environment=$Environment `
                regionAbbr=$RegionAbbr `
                location=$Location `
                postgresLocation=$PostgresLocation `
                containerImage=$DeployContainerImage `
                postgresPassword=$PostgresPassword `
                redisPassword=$RedisPassword `
            --output json | Out-File -FilePath deployment-output.json -Encoding utf8
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ Infrastructure deployed" -ForegroundColor Green
            Write-Host ""
            Write-Host "  ⚠️  CREDENTIALS GENERATED (save securely, not logged):" -ForegroundColor Yellow
            Write-Host "     PostgreSQL and Redis passwords have been generated."
            Write-Host "     To retrieve them, check deployment-output.json or Azure Portal."
            
            # Save credentials to a secure file (not displayed on console)
            $credFile = "credentials-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
            @{
                PostgresPassword = $PostgresPassword
                RedisPassword = $RedisPassword
                GeneratedAt = (Get-Date -Format "o")
            } | ConvertTo-Json | Out-File -FilePath $credFile -Encoding utf8
            Write-Host "     Credentials saved to: $credFile" -ForegroundColor Cyan
            Write-Host "     ⚠️  Delete this file after saving credentials securely!" -ForegroundColor Yellow
        } else {
            Write-Error "Infrastructure deployment failed"
            exit 1
        }
    }
} else {
    Write-Host ""
    Write-Host "Step 3: Skipping infrastructure deployment" -ForegroundColor Yellow
}

# Step 4: Configure Custom Domain
if ($CustomDomain) {
    Write-Host ""
    Write-Host "Step 4: Configuring custom domain ($CustomDomain)..." -ForegroundColor Yellow
    
    # Get Container App FQDN
    $containerAppFqdn = az containerapp show `
        --name $ContainerAppName `
        --resource-group $ResourceGroup `
        --query "properties.configuration.ingress.fqdn" `
        --output tsv 2>&1
    
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrEmpty($containerAppFqdn)) {
        Write-Host "  ⚠️  Container App not found. Deploy infrastructure first." -ForegroundColor Yellow
    } else {
        Write-Host "  Container App FQDN: $containerAppFqdn" -ForegroundColor Cyan
        
        # Add custom domain
        az containerapp hostname add `
            --name $ContainerAppName `
            --resource-group $ResourceGroup `
            --hostname $CustomDomain 2>&1 | Out-Null
        
        Write-Host ""
        Write-Host "  📋 DNS Configuration Required:" -ForegroundColor Cyan
        Write-Host "     Add the following DNS records to your domain:" -ForegroundColor White
        Write-Host ""
        Write-Host "     Record Type: CNAME" -ForegroundColor White
        Write-Host "     Name:        $CustomDomain" -ForegroundColor White
        Write-Host "     Value:       $containerAppFqdn" -ForegroundColor White
        Write-Host ""
        Write-Host "  After DNS propagation, Azure will automatically provision SSL certificate."
        Write-Host "  ✅ Custom domain configuration initiated" -ForegroundColor Green
    }
} else {
    Write-Host ""
    Write-Host "Step 4: Skipping custom domain configuration (not specified)" -ForegroundColor Yellow
}

# Step 5: Configure GitHub App Credentials
if ($GitHubAppId -and $GitHubAppPrivateKeyPath -and $GitHubWebhookSecret) {
    Write-Host ""
    Write-Host "Step 5: Configuring GitHub App credentials..." -ForegroundColor Yellow
    
    # Read private key from file
    if (Test-Path $GitHubAppPrivateKeyPath) {
        $GitHubAppPrivateKey = Get-Content $GitHubAppPrivateKeyPath -Raw
        
        # Add secrets to Container App
        az containerapp secret set `
            --name $ContainerAppName `
            --resource-group $ResourceGroup `
            --secrets github-app-id=$GitHubAppId `
                      github-app-private-key="$GitHubAppPrivateKey" `
                      github-webhook-secret=$GitHubWebhookSecret 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            # Update environment variables to reference secrets
            az containerapp update `
                --name $ContainerAppName `
                --resource-group $ResourceGroup `
                --set-env-vars `
                    GITHUB_APP_ID=secretref:github-app-id `
                    GITHUB_APP_PRIVATE_KEY=secretref:github-app-private-key `
                    GITHUB_WEBHOOK_SECRET=secretref:github-webhook-secret 2>&1 | Out-Null
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ GitHub App credentials configured" -ForegroundColor Green
            } else {
                Write-Host "  ⚠️  Failed to update environment variables" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  ⚠️  Failed to add secrets to Container App" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ⚠️  Private key file not found: $GitHubAppPrivateKeyPath" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "Step 5: Skipping GitHub App credentials (not all parameters provided)" -ForegroundColor Yellow
    Write-Host "  To configure later, run with:" -ForegroundColor Cyan
    Write-Host "  -GitHubAppId <id> -GitHubAppPrivateKeyPath <path> -GitHubWebhookSecret <secret>"
}

# Summary
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Deployment Summary" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Get Container App URL if available
$containerAppUrl = az containerapp show `
    --name $ContainerAppName `
    --resource-group $ResourceGroup `
    --query "properties.configuration.ingress.fqdn" `
    --output tsv 2>&1

if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrEmpty($containerAppUrl)) {
    Write-Host "  Container App URL: https://$containerAppUrl" -ForegroundColor Green
    if ($CustomDomain) {
        Write-Host "  Custom Domain:     https://$CustomDomain (after DNS setup)" -ForegroundColor Green
    }
} else {
    Write-Host "  Container App: Pending deployment" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  Next Steps:" -ForegroundColor Cyan
Write-Host "  1. If using GitHub workflow, wait for deployment to complete"
Write-Host "  2. Configure DNS records for custom domain"
Write-Host "  3. Register GitHub App at https://github.com/settings/apps/new"
Write-Host "  4. Add GitHub App credentials using this script or Azure Portal"
Write-Host ""
Write-Host "  Documentation: https://github.com/$RepoOwner/$RepoName/blob/main/docs/GITHUB_APP_QUICKSTART.md"
Write-Host ""
Write-Host "✅ Setup script completed!" -ForegroundColor Green
