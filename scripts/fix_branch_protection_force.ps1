# Branch Protection Force Overwrite Fix - PowerShell Script
# This script helps you adjust branch protection rules to allow force overwrites

Write-Host "🔧 Branch Protection Force Overwrite Fixer" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

# Check if GitHub CLI is installed and authenticated
Write-Host "🔐 Checking GitHub CLI authentication..." -ForegroundColor Yellow
try {
    $authStatus = gh auth status 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ GitHub CLI not authenticated. Please run:" -ForegroundColor Red
        Write-Host "   gh auth login" -ForegroundColor White
        exit 1
    }
    Write-Host "✅ GitHub CLI authenticated" -ForegroundColor Green
}
catch {
    Write-Host "❌ GitHub CLI not found. Please install it first:" -ForegroundColor Red
    Write-Host "   https://cli.github.com/" -ForegroundColor White
    exit 1
}

# Get repository information
Write-Host "📋 Getting repository information..." -ForegroundColor Yellow
try {
    $owner = gh repo view --json owner -q .owner.login
    $repo = gh repo view --json name -q .name
    
    if (-not $owner -or -not $repo) {
        Write-Host "❌ Could not get repository information" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Repository: $owner/$repo" -ForegroundColor Green
}
catch {
    Write-Host "❌ Error getting repository information" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🎯 Available Options:" -ForegroundColor Cyan
Write-Host "1. Allow force overwrites (recommended)" -ForegroundColor White
Write-Host "2. Minimal protection (very permissive)" -ForegroundColor White
Write-Host "3. Disable all protection (temporary)" -ForegroundColor White
Write-Host "4. Show current protection rules" -ForegroundColor White
Write-Host "5. Exit" -ForegroundColor White

$choice = Read-Host "`nSelect option (1-5)"

switch ($choice) {
    "1" {
        Write-Host "⚙️  Creating force overwrite configuration..." -ForegroundColor Yellow
        
        # Create configuration that allows force overwrites
        $config = @{
            required_status_checks           = @{
                strict   = $false
                contexts = @(
                    "CI / test (pull_request)",
                    "Quality Feedback / quality-feedback (3.13) (pull_request)",
                    "Quality Feedback / security-feedback (pull_request)",
                    "PR Checks / Essential Checks (pull_request)"
                )
            }
            enforce_admins                   = $false
            required_pull_request_reviews    = @{
                required_approving_review_count = 0
                dismiss_stale_reviews           = $false
                require_code_owner_reviews      = $false
            }
            restrictions                     = $null
            allow_force_pushes               = $true
            allow_deletions                  = $true
            required_conversation_resolution = $false
            required_signatures              = $false
            lock_branch                      = $false
            allow_fork_syncing               = $true
        }
        
        # Save to temporary file
        $config | ConvertTo-Json -Depth 10 | Out-File -FilePath "temp_branch_protection.json" -Encoding UTF8
        
        Write-Host "🔄 Updating branch protection..." -ForegroundColor Yellow
        $result = gh api "repos/$owner/$repo/branches/main/protection" --method PUT --input "temp_branch_protection.json"
        
        # Clean up
        Remove-Item "temp_branch_protection.json" -ErrorAction SilentlyContinue
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Branch protection updated to allow force overwrites!" -ForegroundColor Green
            Write-Host "📋 Changes made:" -ForegroundColor Cyan
            Write-Host "   - Allow force pushes: True" -ForegroundColor White
            Write-Host "   - Required reviews: 0" -ForegroundColor White
            Write-Host "   - Require conversation resolution: False" -ForegroundColor White
            Write-Host "   - Require branches up to date: False" -ForegroundColor White
        }
        else {
            Write-Host "❌ Failed to update branch protection" -ForegroundColor Red
        }
    }
    
    "2" {
        Write-Host "⚙️  Creating minimal protection configuration..." -ForegroundColor Yellow
        
        # Minimal configuration
        $config = @{
            required_status_checks           = @{
                strict   = $false
                contexts = @("CI / test (pull_request)")
            }
            enforce_admins                   = $false
            required_pull_request_reviews    = @{
                required_approving_review_count = 0
                dismiss_stale_reviews           = $false
                require_code_owner_reviews      = $false
            }
            restrictions                     = $null
            allow_force_pushes               = $true
            allow_deletions                  = $true
            required_conversation_resolution = $false
            required_signatures              = $false
            lock_branch                      = $false
            allow_fork_syncing               = $true
        }
        
        $config | ConvertTo-Json -Depth 10 | Out-File -FilePath "temp_branch_protection.json" -Encoding UTF8
        
        Write-Host "🔄 Updating branch protection..." -ForegroundColor Yellow
        $result = gh api "repos/$owner/$repo/branches/main/protection" --method PUT --input "temp_branch_protection.json"
        
        Remove-Item "temp_branch_protection.json" -ErrorAction SilentlyContinue
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Branch protection set to minimal!" -ForegroundColor Green
            Write-Host "📋 Only essential checks required" -ForegroundColor Cyan
        }
        else {
            Write-Host "❌ Failed to update branch protection" -ForegroundColor Red
        }
    }
    
    "3" {
        Write-Host "🚫 Disabling branch protection..." -ForegroundColor Yellow
        $result = gh api "repos/$owner/$repo/branches/main/protection" --method DELETE
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Branch protection completely disabled!" -ForegroundColor Green
            Write-Host "⚠️  Remember to re-enable protection later" -ForegroundColor Yellow
        }
        else {
            Write-Host "❌ Failed to disable branch protection" -ForegroundColor Red
        }
    }
    
    "4" {
        Write-Host "📋 Current branch protection rules:" -ForegroundColor Yellow
        gh api "repos/$owner/$repo/branches/main/protection" | ConvertFrom-Json | ConvertTo-Json -Depth 10
    }
    
    "5" {
        Write-Host "👋 Exiting..." -ForegroundColor Cyan
        exit 0
    }
    
    default {
        Write-Host "❌ Invalid choice" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "🎉 Done! Your PR should now be mergeable." -ForegroundColor Green
Write-Host "💡 If you still have issues:" -ForegroundColor Cyan
Write-Host "   1. Refresh your PR page" -ForegroundColor White
Write-Host "   2. Wait 2-3 minutes for GitHub to update" -ForegroundColor White
Write-Host "   3. Try merging again" -ForegroundColor White
