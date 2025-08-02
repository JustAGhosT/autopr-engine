# Comprehensive Commit Script with AI-Enhanced Quality Analysis
# This script runs a thorough quality check with AI suggestions before committing

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " AutoPR Comprehensive Commit Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in a git repository
try {
    git rev-parse --git-dir | Out-Null
}
catch {
    Write-Host "ERROR: Not in a git repository" -ForegroundColor Red
    Write-Host "Please run this script from a git repository root" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if there are staged changes
$stagedFiles = git diff --cached --name-only
if (-not $stagedFiles) {
    Write-Host "ERROR: No staged changes found" -ForegroundColor Red
    Write-Host "Please stage your changes first with: git add ." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[1/4] Running pre-commit hooks..." -ForegroundColor Green
Write-Host ""
$preCommitResult = pre-commit run --all-files
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Pre-commit hooks failed" -ForegroundColor Red
    Write-Host "Please fix the issues above and try again" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[2/4] Running comprehensive quality analysis..." -ForegroundColor Green
Write-Host ""
$comprehensiveResult = python -m autopr.actions.quality_engine --mode=comprehensive --verbose
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "WARNING: Quality analysis found issues" -ForegroundColor Yellow
    Write-Host "Review the results above and consider fixing critical issues" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Continue with commit anyway? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        Write-Host "Commit cancelled by user" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host ""
Write-Host "[3/4] Running AI-enhanced analysis..." -ForegroundColor Green
Write-Host ""
$aiResult = python -m autopr.actions.quality_engine --mode=ai_enhanced --ai-provider openai --ai-model gpt-4 --verbose
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "WARNING: AI-enhanced analysis encountered issues" -ForegroundColor Yellow
    Write-Host "This is experimental and may not work in all environments" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Continue with commit anyway? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        Write-Host "Commit cancelled by user" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host ""
Write-Host "[4/4] Committing changes..." -ForegroundColor Green
Write-Host ""

# Get commit message from user
$commitMsg = Read-Host "Enter commit message"
if ([string]::IsNullOrWhiteSpace($commitMsg)) {
    Write-Host "ERROR: Commit message cannot be empty" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Commit the changes
$commitResult = git commit -m $commitMsg
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Commit failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " SUCCESS: Comprehensive commit completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor White
Write-Host "- Pre-commit hooks: PASSED" -ForegroundColor Green
Write-Host "- Comprehensive quality analysis: COMPLETED" -ForegroundColor Green
Write-Host "- AI-enhanced analysis: COMPLETED" -ForegroundColor Green
Write-Host "- Git commit: SUCCESSFUL" -ForegroundColor Green
Write-Host ""
Write-Host "Your code has been thoroughly reviewed and committed." -ForegroundColor White
Read-Host "Press Enter to continue" 