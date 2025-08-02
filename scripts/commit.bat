@echo off
REM Comprehensive Commit Script with AI-Enhanced Quality Analysis
REM This script runs a thorough quality check with AI suggestions before committing

echo ========================================
echo  AutoPR Comprehensive Commit Script
echo ========================================
echo.

REM Check if we're in a git repository
git rev-parse --git-dir >nul 2>&1
if errorlevel 1 (
    echo ERROR: Not in a git repository
    echo Please run this script from a git repository root
    pause
    exit /b 1
)

REM Check if there are staged changes
git diff --cached --name-only >nul 2>&1
if errorlevel 1 (
    echo ERROR: No staged changes found
    echo Please stage your changes first with: git add .
    pause
    exit /b 1
)

echo [1/4] Running pre-commit hooks...
echo.
pre-commit run --all-files
if errorlevel 1 (
    echo.
    echo ERROR: Pre-commit hooks failed
    echo Please fix the issues above and try again
    pause
    exit /b 1
)

echo.
echo [2/4] Running comprehensive quality analysis...
echo.
python -m autopr.actions.quality_engine --mode=comprehensive --verbose
if errorlevel 1 (
    echo.
    echo WARNING: Quality analysis found issues
    echo Review the results above and consider fixing critical issues
    echo.
    set /p continue="Continue with commit anyway? (y/N): "
    if /i not "%continue%"=="y" (
        echo Commit cancelled by user
        pause
        exit /b 1
    )
)

echo.
echo [3/4] Running AI-enhanced analysis...
echo.
python -m autopr.actions.quality_engine --mode=ai_enhanced --ai-provider openai --ai-model gpt-4 --verbose
if errorlevel 1 (
    echo.
    echo WARNING: AI-enhanced analysis encountered issues
    echo This is experimental and may not work in all environments
    echo.
    set /p continue="Continue with commit anyway? (y/N): "
    if /i not "%continue%"=="y" (
        echo Commit cancelled by user
        pause
        exit /b 1
    )
)

echo.
echo [4/4] Committing changes...
echo.

REM Get commit message from user
set /p commit_msg="Enter commit message: "
if "%commit_msg%"=="" (
    echo ERROR: Commit message cannot be empty
    pause
    exit /b 1
)

REM Commit the changes
git commit -m "%commit_msg%"
if errorlevel 1 (
    echo.
    echo ERROR: Commit failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo  SUCCESS: Comprehensive commit completed!
echo ========================================
echo.
echo Summary:
echo - Pre-commit hooks: PASSED
echo - Comprehensive quality analysis: COMPLETED
echo - AI-enhanced analysis: COMPLETED
echo - Git commit: SUCCESSFUL
echo.
echo Your code has been thoroughly reviewed and committed.
pause 