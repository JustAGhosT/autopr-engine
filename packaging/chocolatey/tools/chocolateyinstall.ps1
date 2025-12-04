# Chocolatey install script for AutoPR Engine

$ErrorActionPreference = 'Stop'

$packageName = 'autopr-engine'
$toolsDir = "$(Split-Path -Parent $MyInvocation.MyCommand.Definition)"

# Check Python installation
$pythonPath = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonPath) {
    Write-Host "Python not found. Installing Python 3.12..."
    choco install python3 --version=3.12 -y
    refreshenv
}

# Verify Python version
$pythonVersion = python --version 2>&1
if ($pythonVersion -match "Python (\d+)\.(\d+)") {
    $major = [int]$Matches[1]
    $minor = [int]$Matches[2]
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 12)) {
        throw "Python 3.12+ required. Found: $pythonVersion"
    }
}

Write-Host "Installing AutoPR Engine via pip..."
pip install autopr-engine

if ($LASTEXITCODE -ne 0) {
    throw "Failed to install AutoPR Engine"
}

Write-Host ""
Write-Host "AutoPR Engine installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Set up your API keys:"
Write-Host '     $env:GITHUB_TOKEN = "ghp_your_token"'
Write-Host '     $env:OPENAI_API_KEY = "sk-your_key"'
Write-Host ""
Write-Host "  2. Run AutoPR:"
Write-Host "     autopr --help"
Write-Host ""
