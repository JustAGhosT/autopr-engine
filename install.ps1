# AutoPR Engine - Windows Installation Script
# Usage: irm https://raw.githubusercontent.com/JustAGhosT/codeflow-engine/main/install.ps1 | iex
# Or: .\install.ps1 [-Full] [-Dev] [-Minimal] [-Docker]

[CmdletBinding()]
param(
    [switch]$Full,
    [switch]$Dev,
    [switch]$Minimal,
    [switch]$Docker,
    [switch]$Action,
    [switch]$Version,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$ScriptVersion = "1.0.0"

# Colors
function Write-Status { param($Message) Write-Host "[*] $Message" -ForegroundColor Blue }
function Write-Success { param($Message) Write-Host "[+] $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "[!] $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "[-] $Message" -ForegroundColor Red }

# Banner
function Show-Banner {
    Write-Host ""
    Write-Host "  ___        _        ____  ____    _____             _            " -ForegroundColor Cyan
    Write-Host " / _ \      | |      |  _ \|  _ \  | ____|_ __   __ _(_)_ __   ___ " -ForegroundColor Cyan
    Write-Host "| |_| |_   _| |_ ___ | |_) | |_) | |  _| | '_ \ / _`` | | '_ \ / _ \" -ForegroundColor Cyan
    Write-Host "|  _  | | | | __/ _ \|  __/|  _ <  | |___| | | | (_| | | | | |  __/" -ForegroundColor Cyan
    Write-Host "|_| |_|\__,_|\__\___/|_|   |_| \_\ |_____|_| |_|\__, |_|_| |_|\___|" -ForegroundColor Cyan
    Write-Host "                                                |___/              " -ForegroundColor Cyan
    Write-Host ""
    Write-Host "AI-Powered GitHub PR Automation and Issue Management" -ForegroundColor White
    Write-Host ""
}

# Help
function Show-Help {
    Write-Host "Usage: .\install.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Minimal   Install core package only (no extras)"
    Write-Host "  -Full      Install with all features and integrations"
    Write-Host "  -Dev       Install for development (includes dev tools)"
    Write-Host "  -Docker    Set up Docker-based installation"
    Write-Host "  -Action    Set up GitHub Action workflow in current repo"
    Write-Host "  -Version   Show installer version"
    Write-Host "  -Help      Show this help message"
    Write-Host ""
}

# Check Python
function Test-Python {
    Write-Status "Checking Python installation..."

    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]

            if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 12)) {
                Write-Success "Python $major.$minor detected"
                return $true
            } else {
                Write-Error "Python 3.12+ required (found $major.$minor)"
                Write-Host "Install Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
                return $false
            }
        }
    } catch {
        Write-Error "Python not found. Please install Python 3.12+"
        Write-Host "Install Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
        return $false
    }
    return $false
}

# Check pip
function Test-Pip {
    try {
        $null = pip --version
        Write-Success "pip detected"
        return $true
    } catch {
        Write-Error "pip not found"
        return $false
    }
}

# Check Docker
function Test-Docker {
    try {
        $null = docker --version
        Write-Success "Docker detected"
        return $true
    } catch {
        Write-Error "Docker not found. Please install Docker Desktop"
        Write-Host "Install from: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
        return $false
    }
}

# Install via pip
function Install-AutoPR {
    param([string]$Type)

    Write-Status "Installing AutoPR Engine via pip..."

    # Recommend virtual environment
    if (-not $env:VIRTUAL_ENV -and $Type -ne "Minimal") {
        Write-Warning "Consider using a virtual environment: python -m venv venv && .\venv\Scripts\Activate.ps1"
    }

    switch ($Type) {
        "Minimal" {
            Write-Status "Installing minimal package (core only)..."
            pip install --no-deps codeflow-engine
        }
        "Full" {
            Write-Status "Installing full package with all features..."
            pip install "codeflow-engine[full]"
        }
        "Dev" {
            Write-Status "Installing development package..."
            if (Test-Path "pyproject.toml") {
                pip install -e ".[dev]"
            } else {
                Write-Status "Cloning repository..."
                git clone https://github.com/JustAGhosT/codeflow-engine.git
                Set-Location codeflow-engine
                pip install -e ".[dev]"
            }
        }
        default {
            Write-Status "Installing standard package..."
            pip install codeflow-engine
        }
    }

    if ($LASTEXITCODE -eq 0) {
        Write-Success "AutoPR Engine installed successfully!"
    } else {
        Write-Error "Installation failed"
        exit 1
    }
}

# Install via Docker
function Install-Docker {
    Write-Status "Setting up Docker installation..."

    if (-not (Test-Path "docker-compose.yml")) {
        Write-Status "Creating autopr directory..."
        New-Item -ItemType Directory -Force -Path "codeflow-engine" | Out-Null
        Set-Location "codeflow-engine"

        Write-Status "Downloading Docker Compose configuration..."
        try {
            Invoke-WebRequest -Uri "https://raw.githubusercontent.com/JustAGhosT/autopr-engine/main/docker-compose.yml" -OutFile "docker-compose.yml"
            Invoke-WebRequest -Uri "https://raw.githubusercontent.com/JustAGhosT/autopr-engine/main/.env.example" -OutFile ".env.example"
        } catch {
            Write-Error "Failed to download configuration files"
            exit 1
        }
    }

    if (-not (Test-Path ".env")) {
        Write-Status "Creating .env file from template..."
        Copy-Item ".env.example" ".env"
        Write-Warning "Please edit .env file with your API keys before starting"
    }

    Write-Success "Docker setup complete!"
    Write-Host ""
    Write-Status "To start AutoPR Engine:"
    Write-Host "  1. Edit .env with your API keys"
    Write-Host "  2. Run: docker compose up -d"
}

# Setup GitHub Action
function Install-GitHubAction {
    Write-Status "Setting up GitHub Action workflow..."

    $workflowDir = ".github\workflows"
    $workflowFile = "$workflowDir\autopr.yml"

    if (-not (Test-Path $workflowDir)) {
        New-Item -ItemType Directory -Force -Path $workflowDir | Out-Null
    }

    try {
        Invoke-WebRequest -Uri "https://raw.githubusercontent.com/JustAGhosT/autopr-engine/main/templates/quick-start/autopr-workflow.yml" -OutFile $workflowFile
        Write-Success "Created $workflowFile"
        Write-Warning "Remember to add OPENAI_API_KEY to your repository secrets!"
    } catch {
        Write-Error "Failed to download workflow file"
        exit 1
    }
}

# Show next steps
function Show-NextSteps {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
    Write-Success "Installation Complete!"
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host ""
    Write-Host "  1. Set up your API keys:"
    Write-Host '     $env:GITHUB_TOKEN = "ghp_your_token"'
    Write-Host '     $env:OPENAI_API_KEY = "sk-your_key"'
    Write-Host ""
    Write-Host "  2. Run AutoPR CLI:"
    Write-Host "     autopr --help"
    Write-Host ""
    Write-Host "  3. Add to your GitHub repo:"
    Write-Host "     .\install.ps1 -Action"
    Write-Host ""
    Write-Host "Documentation: https://github.com/JustAGhosT/codeflow-engine"
    Write-Host ""
}

# Main
function Main {
    Show-Banner

    if ($Version) {
        Write-Host "AutoPR Engine Installer v$ScriptVersion"
        exit 0
    }

    if ($Help) {
        Show-Help
        exit 0
    }

    if ($Action) {
        Install-GitHubAction
        exit 0
    }

    if ($Docker) {
        if (-not (Test-Docker)) { exit 1 }
        Install-Docker
        exit 0
    }

    # Standard installation
    if (-not (Test-Python)) { exit 1 }
    if (-not (Test-Pip)) { exit 1 }

    if ($Minimal) {
        Install-AutoPR -Type "Minimal"
    } elseif ($Full) {
        Install-AutoPR -Type "Full"
    } elseif ($Dev) {
        Install-AutoPR -Type "Dev"
    } else {
        Install-AutoPR -Type "Standard"
    }

    Show-NextSteps
}

Main
