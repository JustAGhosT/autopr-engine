param(
    [string]$Repository = "test/repo",
    [switch]$DryRun
)

Write-Host "Repository: $Repository" -ForegroundColor Cyan
Write-Host "Dry Run: $DryRun" -ForegroundColor Cyan

$environments = @("staging", "production")

foreach ($env in $environments) {
    Write-Host "Setting up environment: $env" -ForegroundColor Yellow
    
    if ($DryRun) {
        Write-Host "  [DRY RUN] Would create environment: $env" -ForegroundColor Green
    }
    else {
        Write-Host "  Creating environment: $env" -ForegroundColor Green
    }
}

Write-Host "Done!" -ForegroundColor Green
