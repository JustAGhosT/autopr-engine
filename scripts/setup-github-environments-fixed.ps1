#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup GitHub environments for staging and production deployments.

.DESCRIPTION
    This script creates staging and production environments in the GitHub repository
    with appropriate protection rules and deployment settings.

.PARAMETER Repository
    The GitHub repository in format "owner/repo" (e.g., "octocat/Hello-World")

.PARAMETER Token
    GitHub personal access token with repo permissions

.PARAMETER DryRun
    Show what would be created without actually creating environments

.EXAMPLE
    .\setup-github-environments.ps1 -Repository "your-org/autopr-engine" -Token "ghp_xxx"
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$Repository,
    
    [Parameter(Mandatory = $true)]
    [string]$Token,
    
    [switch]$DryRun
)

# Colors for output
$ErrorColor = "Red"
$SuccessColor = "Green"
$InfoColor = "Cyan"
$WarningColor = "Yellow"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-GitHubCLI {
    try {
        $null = gh --version
        return $true
    }
    catch {
        return $false
    }
}

function Create-GitHubEnvironment {
    param(
        [string]$Repo,
        [string]$EnvName,
        [string]$AuthToken,
        [bool]$IsDryRun
    )
    
    $headers = @{
        "Authorization" = "Bearer $AuthToken"
        "Accept" = "application/vnd.github.v3+json"
        "User-Agent" = "AutoPR-Environment-Setup"
    }
    
    $baseUrl = "https://api.github.com/repos/$Repo/environments"
    
    # Environment configuration
    $envConfig = @{
        name = $EnvName
        protection_rules = @(
            @{
                type = "wait_timer"
                wait_timer = 0
            }
        )
        deployment_branch_policy = @{
            protected_branches = $true
            custom_branch_policies = $false
        }
    }
    
    # Add specific protection rules based on environment
    switch ($EnvName) {
        "staging" {
            $envConfig.protection_rules += @{
                type = "required_reviewers"
                required_reviewers = @{
                    users = @()
                    teams = @()
                }
            }
            Write-ColorOutput "  📋 Staging: Manual workflow dispatch required" $InfoColor
        }
        "production" {
            $envConfig.protection_rules += @{
                type = "required_reviewers"
                required_reviewers = @{
                    users = @()
                    teams = @()
                }
            }
            $envConfig.protection_rules += @{
                type = "wait_timer"
                wait_timer = 300
            }
            Write-ColorOutput "  🚀 Production: Requires approval + 5min wait" $WarningColor
        }
    }
    
    if ($IsDryRun) {
        Write-ColorOutput "  [DRY RUN] Would create environment: $EnvName" $InfoColor
        Write-ColorOutput "  [DRY RUN] Configuration: $($envConfig | ConvertTo-Json -Depth 3)" $InfoColor
        return $true
    }
    
    try {
        $body = $envConfig | ConvertTo-Json -Depth 3
        $response = Invoke-RestMethod -Uri $baseUrl -Method POST -Headers $headers -Body $body -ContentType "application/json"
        
        Write-ColorOutput "  ✅ Created environment: $EnvName" $SuccessColor
        Write-ColorOutput "  🔗 URL: $($response.html_url)" $InfoColor
        return $true
    }
    catch {
        if ($_.Exception.Response.StatusCode -eq 422) {
            Write-ColorOutput "  ⚠️  Environment '$EnvName' already exists" $WarningColor
            return $true
        }
        else {
            Write-ColorOutput "  ❌ Failed to create environment '$EnvName': $($_.Exception.Message)" $ErrorColor
            return $false
        }
    }
}

function Set-EnvironmentVariables {
    param(
        [string]$Repo,
        [string]$EnvName,
        [string]$AuthToken,
        [bool]$IsDryRun
    )
    
    $headers = @{
        "Authorization" = "Bearer $AuthToken"
        "Accept" = "application/vnd.github.v3+json"
        "User-Agent" = "AutoPR-Environment-Setup"
    }
    
    $baseUrl = "https://api.github.com/repos/$Repo/environments/$EnvName/secrets"
    
    # Common environment variables
    $variables = @{
        "DEPLOYMENT_ENV" = $EnvName
        "NODE_ENV" = if ($EnvName -eq "production") { "production" } else { "staging" }
        "LOG_LEVEL" = if ($EnvName -eq "production") { "info" } else { "debug" }
    }
    
    foreach ($var in $variables.GetEnumerator()) {
        if ($IsDryRun) {
            Write-ColorOutput "  [DRY RUN] Would set variable: $($var.Key) = $($var.Value)" $InfoColor
        }
        else {
            try {
                $body = @{
                    name = $var.Key
                    value = $var.Value
                } | ConvertTo-Json
                
                $response = Invoke-RestMethod -Uri $baseUrl -Method POST -Headers $headers -Body $body -ContentType "application/json"
                Write-ColorOutput "  ✅ Set variable: $($var.Key)" $SuccessColor
            }
            catch {
                Write-ColorOutput "  ❌ Failed to set variable '$($var.Key)': $($_.Exception.Message)" $ErrorColor
            }
        }
    }
}

# Main execution
Write-ColorOutput "🚀 GitHub Environment Setup Script" $InfoColor
Write-ColorOutput "=================================" $InfoColor
Write-ColorOutput "Repository: $Repository" $InfoColor
Write-ColorOutput "Dry Run: $DryRun" $InfoColor
Write-ColorOutput ""

# Validate repository format
if ($Repository -notmatch "^[^/]+/[^/]+$") {
    Write-ColorOutput "❌ Invalid repository format. Use 'owner/repo' format." $ErrorColor
    exit 1
}

# Test GitHub CLI availability
$hasGitHubCLI = Test-GitHubCLI
if ($hasGitHubCLI) {
    Write-ColorOutput "✅ GitHub CLI detected" $SuccessColor
} else {
    Write-ColorOutput "⚠️  GitHub CLI not found. Using REST API directly." $WarningColor
}

Write-ColorOutput ""
Write-ColorOutput "📋 Creating Environments:" $InfoColor

# Create environments
$environments = @("staging", "production")
$successCount = 0

foreach ($env in $environments) {
    Write-ColorOutput "`n🔧 Setting up environment: $env" $InfoColor
    
    $success = Create-GitHubEnvironment -Repo $Repository -EnvName $env -AuthToken $Token -IsDryRun $DryRun
    if ($success) {
        $successCount++
        
        # Set environment variables
        Write-ColorOutput "  📝 Setting environment variables..." $InfoColor
        Set-EnvironmentVariables -Repo $Repository -EnvName $env -AuthToken $Token -IsDryRun $DryRun
    }
}

Write-ColorOutput ""
Write-ColorOutput "📊 Summary:" $InfoColor
Write-ColorOutput "  Environments processed: $($environments.Count)" $InfoColor
Write-ColorOutput "  Successfully created/verified: $successCount" $SuccessColor

if ($successCount -eq $environments.Count) {
    Write-ColorOutput ""
    Write-ColorOutput "🎉 All environments ready!" $SuccessColor
    Write-ColorOutput ""
    Write-ColorOutput "Next steps:" $InfoColor
    Write-ColorOutput "  1. Review environment settings in GitHub repository" $InfoColor
    Write-ColorOutput "  2. Add required reviewers if needed" $InfoColor
    Write-ColorOutput "  3. Configure deployment secrets (API keys, etc.)" $InfoColor
    Write-ColorOutput "  4. Test your CI/CD pipeline" $InfoColor
} else {
    Write-ColorOutput ""
    Write-ColorOutput "⚠️  Some environments failed to create. Check the errors above." $WarningColor
    exit 1
}
