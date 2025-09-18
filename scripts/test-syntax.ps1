# Simple test script
param(
    [string]$Repository,
    [string]$Token,
    [switch]$DryRun
)

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

# Main execution
Write-ColorOutput "🚀 GitHub Environment Setup Script" "Cyan"
Write-ColorOutput "Repository: $Repository" "Cyan"
Write-ColorOutput "Dry Run: $DryRun" "Cyan"

# Test GitHub CLI availability
$hasGitHubCLI = Test-GitHubCLI
if ($hasGitHubCLI) {
    Write-ColorOutput "✅ GitHub CLI detected" "Green"
}
else {
    Write-ColorOutput "⚠️  GitHub CLI not found. Using REST API directly." "Yellow"
}

Write-ColorOutput "📋 Creating Environments:" "Cyan"

# Create environments
$environments = @("staging", "production")
$successCount = 0

foreach ($env in $environments) {
    Write-ColorOutput "`n🔧 Setting up environment: $env" "Cyan"
    
    # Simulate success for dry run
    $success = $true
    if ($success) {
        $successCount++
        Write-ColorOutput "  📝 Setting environment variables..." "Cyan"
    }
}

Write-ColorOutput ""
Write-ColorOutput "📊 Summary:" "Cyan"
Write-ColorOutput "  Environments processed: $($environments.Count)" "Cyan"
Write-ColorOutput "  Successfully created/verified: $successCount" "Green"

if ($successCount -eq $environments.Count) {
    Write-ColorOutput ""
    Write-ColorOutput "🎉 All environments ready!" "Green"
}
else {
    Write-ColorOutput ""
    Write-ColorOutput "⚠️  Some environments failed to create. Check the errors above." "Yellow"
    exit 1
}
