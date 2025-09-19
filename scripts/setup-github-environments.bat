@echo off
setlocal enabledelayedexpansion

REM GitHub Environment Setup Script for Windows
REM Creates staging and production environments with protection rules

set "REPO="
set "TOKEN="
set "DRY_RUN=false"

REM Parse command line arguments
:parse_args
if "%~1"=="" goto :validate_args
if "%~1"=="-r" (
    set "REPO=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="--repo" (
    set "REPO=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="-t" (
    set "TOKEN=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="--token" (
    set "TOKEN=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="-d" (
    set "DRY_RUN=true"
    shift
    goto :parse_args
)
if "%~1"=="--dry-run" (
    set "DRY_RUN=true"
    shift
    goto :parse_args
)
if "%~1"=="-h" goto :show_help
if "%~1"=="--help" goto :show_help

echo Unknown option: %~1
goto :show_help

:show_help
echo Usage: %~nx0 -r ^<repository^> -t ^<token^> [options]
echo.
echo Options:
echo   -r, --repo     GitHub repository in format 'owner/repo'
echo   -t, --token    GitHub personal access token
echo   -d, --dry-run  Show what would be created without creating
echo   -h, --help     Show this help message
echo.
echo Example:
echo   %~nx0 -r your-org/autopr-engine -t ghp_xxx
echo   %~nx0 -r your-org/autopr-engine -t ghp_xxx --dry-run
goto :end

:validate_args
if "%REPO%"=="" (
    echo Error: Repository is required
    goto :show_help
)
if "%TOKEN%"=="" (
    echo Error: Token is required
    goto :show_help
)

REM Validate repository format (basic check)
echo %REPO% | findstr /r "^[^/]*/[^/]*$" >nul
if errorlevel 1 (
    echo Error: Invalid repository format. Use 'owner/repo' format.
    goto :end
)

REM Main execution
echo.
echo [1;36mGitHub Environment Setup Script[0m
echo =================================
echo Repository: %REPO%
echo Dry Run: %DRY_RUN%
echo.

REM Check if curl is available
curl --version >nul 2>&1
if errorlevel 1 (
    echo Error: curl is required but not found. Please install curl or use PowerShell script.
    goto :end
)

echo [1;36mCreating Environments:[0m

REM Create staging environment
echo.
echo [1;36mSetting up environment: staging[0m
call :create_environment staging
if errorlevel 1 goto :error

REM Create production environment
echo.
echo [1;36mSetting up environment: production[0m
call :create_environment production
if errorlevel 1 goto :error

echo.
echo [1;36mSummary:[0m
echo   Environments processed: 2
echo   Successfully created/verified: 2
echo.
echo [1;32mAll environments ready![0m
echo.
echo [1;36mNext steps:[0m
echo   1. Review environment settings in GitHub repository
echo   2. Add required reviewers if needed
echo   3. Configure deployment secrets (API keys, etc.)
echo   4. Test your CI/CD pipeline
goto :end

:create_environment
set "ENV_NAME=%~1"
set "BASE_URL=https://api.github.com/repos/%REPO%/environments"

REM Create environment configuration
if "%ENV_NAME%"=="staging" (
    set "CONFIG={\"name\":\"staging\",\"protection_rules\":[{\"type\":\"wait_timer\",\"wait_timer\":0},{\"type\":\"required_reviewers\",\"required_reviewers\":{\"users\":[],\"teams\":[]}}],\"deployment_branch_policy\":{\"protected_branches\":true,\"custom_branch_policies\":false}}"
    echo   [1;36mStaging: Manual workflow dispatch required[0m
) else (
    set "CONFIG={\"name\":\"production\",\"protection_rules\":[{\"type\":\"wait_timer\",\"wait_timer\":300},{\"type\":\"required_reviewers\",\"required_reviewers\":{\"users\":[],\"teams\":[]}}],\"deployment_branch_policy\":{\"protected_branches\":true,\"custom_branch_policies\":false}}"
    echo   [1;33mProduction: Requires approval + 5min wait[0m
)

if "%DRY_RUN%"=="true" (
    echo   [1;36m[DRY RUN] Would create environment: %ENV_NAME%[0m
    goto :eof
)

REM Make API call to create environment
curl -s -w "%%{http_code}" -o temp_response.json ^
    -H "Authorization: Bearer %TOKEN%" ^
    -H "Accept: application/vnd.github.v3+json" ^
    -H "User-Agent: AutoPR-Environment-Setup" ^
    -X POST "%BASE_URL%" ^
    -d "%CONFIG%" ^
    -H "Content-Type: application/json" > temp_status.txt

set /p HTTP_CODE=<temp_status.txt

if "%HTTP_CODE%"=="201" (
    echo   [1;32mCreated environment: %ENV_NAME%[0m
) else if "%HTTP_CODE%"=="422" (
    echo   [1;33mEnvironment '%ENV_NAME%' already exists[0m
) else (
    echo   [1;31mFailed to create environment '%ENV_NAME%' (HTTP %HTTP_CODE%)[0m
    del temp_response.json temp_status.txt 2>nul
    goto :error
)

REM Set environment variables
echo   [1;36mSetting environment variables...[0m
call :set_environment_variables %ENV_NAME%

del temp_response.json temp_status.txt 2>nul
goto :eof

:set_environment_variables
set "ENV_NAME=%~1"
set "BASE_URL=https://api.github.com/repos/%REPO%/environments/%ENV_NAME%/secrets"

if "%ENV_NAME%"=="staging" (
    set "NODE_ENV=staging"
    set "LOG_LEVEL=debug"
) else (
    set "NODE_ENV=production"
    set "LOG_LEVEL=info"
)

REM Set DEPLOYMENT_ENV variable
if "%DRY_RUN%"=="true" (
    echo   [1;36m[DRY RUN] Would set variable: DEPLOYMENT_ENV = %ENV_NAME%[0m
) else (
    set "VAR_CONFIG={\"name\":\"DEPLOYMENT_ENV\",\"value\":\"%ENV_NAME%\"}"
    curl -s -w "%%{http_code}" -o temp_var_response.json ^
        -H "Authorization: Bearer %TOKEN%" ^
        -H "Accept: application/vnd.github.v3+json" ^
        -H "User-Agent: AutoPR-Environment-Setup" ^
        -X POST "%BASE_URL%" ^
        -d "%VAR_CONFIG%" ^
        -H "Content-Type: application/json" > temp_var_status.txt
    
    set /p VAR_HTTP_CODE=<temp_var_status.txt
    
    if "!VAR_HTTP_CODE!"=="201" (
        echo   [1;32mSet variable: DEPLOYMENT_ENV[0m
    ) else (
        echo   [1;31mFailed to set variable 'DEPLOYMENT_ENV' (HTTP !VAR_HTTP_CODE!)[0m
    )
    
    del temp_var_response.json temp_var_status.txt 2>nul
)

REM Set NODE_ENV variable
if "%DRY_RUN%"=="true" (
    echo   [1;36m[DRY RUN] Would set variable: NODE_ENV = %NODE_ENV%[0m
) else (
    set "VAR_CONFIG={\"name\":\"NODE_ENV\",\"value\":\"%NODE_ENV%\"}"
    curl -s -w "%%{http_code}" -o temp_var_response.json ^
        -H "Authorization: Bearer %TOKEN%" ^
        -H "Accept: application/vnd.github.v3+json" ^
        -H "User-Agent: AutoPR-Environment-Setup" ^
        -X POST "%BASE_URL%" ^
        -d "%VAR_CONFIG%" ^
        -H "Content-Type: application/json" > temp_var_status.txt
    
    set /p VAR_HTTP_CODE=<temp_var_status.txt
    
    if "!VAR_HTTP_CODE!"=="201" (
        echo   [1;32mSet variable: NODE_ENV[0m
    ) else (
        echo   [1;31mFailed to set variable 'NODE_ENV' (HTTP !VAR_HTTP_CODE!)[0m
    )
    
    del temp_var_response.json temp_var_status.txt 2>nul
)

REM Set LOG_LEVEL variable
if "%DRY_RUN%"=="true" (
    echo   [1;36m[DRY RUN] Would set variable: LOG_LEVEL = %LOG_LEVEL%[0m
) else (
    set "VAR_CONFIG={\"name\":\"LOG_LEVEL\",\"value\":\"%LOG_LEVEL%\"}"
    curl -s -w "%%{http_code}" -o temp_var_response.json ^
        -H "Authorization: Bearer %TOKEN%" ^
        -H "Accept: application/vnd.github.v3+json" ^
        -H "User-Agent: AutoPR-Environment-Setup" ^
        -X POST "%BASE_URL%" ^
        -d "%VAR_CONFIG%" ^
        -H "Content-Type: application/json" > temp_var_status.txt
    
    set /p VAR_HTTP_CODE=<temp_var_status.txt
    
    if "!VAR_HTTP_CODE!"=="201" (
        echo   [1;32mSet variable: LOG_LEVEL[0m
    ) else (
        echo   [1;31mFailed to set variable 'LOG_LEVEL' (HTTP !VAR_HTTP_CODE!)[0m
    )
    
    del temp_var_response.json temp_var_status.txt 2>nul
)

goto :eof

:error
echo.
echo [1;31mSome environments failed to create. Check the errors above.[0m
exit /b 1

:end
endlocal
