# Tests for install.ps1
# Run with: pwsh -File tests/scripts/test_install.ps1
# Or in PowerShell: Invoke-Pester tests/scripts/test_install.ps1

# Requires Pester module: Install-Module -Name Pester -Force

BeforeAll {
    $ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    $InstallScript = Join-Path $ProjectRoot "install.ps1"
}

Describe "install.ps1" {

    Context "Version and Help" {

        It "Shows version with -Version flag" {
            $output = & $InstallScript -Version 2>&1
            $output | Should -Match "AutoPR Engine Installer v"
        }

        It "Shows help with -Help flag" {
            $output = & $InstallScript -Help 2>&1
            $output | Should -Match "Usage:"
            $output | Should -Match "-Minimal"
            $output | Should -Match "-Full"
            $output | Should -Match "-Dev"
            $output | Should -Match "-Docker"
            $output | Should -Match "-Action"
        }
    }

    Context "Script Syntax" {

        It "Has valid PowerShell syntax" {
            $errors = $null
            $null = [System.Management.Automation.Language.Parser]::ParseFile(
                $InstallScript,
                [ref]$null,
                [ref]$errors
            )
            $errors.Count | Should -Be 0
        }

        It "Defines required functions" {
            $content = Get-Content $InstallScript -Raw
            $content | Should -Match "function Show-Banner"
            $content | Should -Match "function Show-Help"
            $content | Should -Match "function Test-Python"
            $content | Should -Match "function Test-Pip"
            $content | Should -Match "function Install-AutoPR"
            $content | Should -Match "function Install-Docker"
            $content | Should -Match "function Install-GitHubAction"
            $content | Should -Match "function Show-NextSteps"
            $content | Should -Match "function Main"
        }

        It "Has CmdletBinding attribute" {
            $content = Get-Content $InstallScript -Raw
            $content | Should -Match "\[CmdletBinding\(\)\]"
        }

        It "Uses ErrorActionPreference Stop" {
            $content = Get-Content $InstallScript -Raw
            $content | Should -Match '\$ErrorActionPreference\s*=\s*"Stop"'
        }
    }

    Context "Parameter Definitions" {

        It "Accepts -Full switch" {
            $content = Get-Content $InstallScript -Raw
            $content | Should -Match "\[switch\]\`$Full"
        }

        It "Accepts -Dev switch" {
            $content = Get-Content $InstallScript -Raw
            $content | Should -Match "\[switch\]\`$Dev"
        }

        It "Accepts -Minimal switch" {
            $content = Get-Content $InstallScript -Raw
            $content | Should -Match "\[switch\]\`$Minimal"
        }

        It "Accepts -Docker switch" {
            $content = Get-Content $InstallScript -Raw
            $content | Should -Match "\[switch\]\`$Docker"
        }

        It "Accepts -Action switch" {
            $content = Get-Content $InstallScript -Raw
            $content | Should -Match "\[switch\]\`$Action"
        }
    }

    Context "Error Handling" {

        It "Has try-catch blocks for network operations" {
            $content = Get-Content $InstallScript -Raw
            $content | Should -Match "try\s*{"
            $content | Should -Match "catch\s*{"
        }

        It "Uses Invoke-WebRequest for downloads" {
            $content = Get-Content $InstallScript -Raw
            $content | Should -Match "Invoke-WebRequest"
        }
    }

    Context "Output Functions" {

        It "Defines Write-Status function" {
            $content = Get-Content $InstallScript -Raw
            $content | Should -Match "function Write-Status"
        }

        It "Defines Write-Success function" {
            $content = Get-Content $InstallScript -Raw
            $content | Should -Match "function Write-Success"
        }

        It "Defines Write-Warning function" {
            $content = Get-Content $InstallScript -Raw
            $content | Should -Match "function Write-Warning"
        }

        It "Defines Write-Error function" {
            $content = Get-Content $InstallScript -Raw
            $content | Should -Match "function Write-Error"
        }
    }
}
