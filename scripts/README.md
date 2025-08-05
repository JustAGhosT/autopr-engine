# Scripts Directory

This directory contains utility scripts for the AutoPR Engine project.

## 🎛️ Volume Control System

The main volume control system for managing IDE linting and commit checks:

- **`volume.py`** - Main volume control interface
- **`volume-control/`** - Complete volume control system
  - `main.py` - Volume control engine
  - `volume_knob.py` - Volume knob implementation  
  - `config_loader.py` - JSON configuration loader
  - `configs/` - Tool-specific volume configurations
  - `status.py` - Show current volume status
  - `debug.py` - Debug volume settings

## 🔍 Validation Scripts

Scripts for validating different aspects of the project:

- **`validate_build_system.py`** - Validate the build system configuration
- **`validate_configs.py`** - Validate configuration files
- **`validate_imports.py`** - Check for import issues
- **`validate_links.py`** - Validate internal and external links
- **`validate_templates.py`** - Validate template files

## 🛠️ Maintenance Scripts

- **`level-0-complete.py`** - Verify Level 0 (no linting) status
- **`disable-github-actions.py`** - Disable GitHub Actions workflows

## 📦 Archived Scripts

Legacy and one-time use scripts have been moved to the `archive/scripts/` directory.
These are kept for reference but are not part of the active codebase.

### Usage
```bash
# Set volumes
python scripts/volume.py dev 50        # Set dev volume to 50
python scripts/volume.py commit 200    # Set commit volume to 200

# Adjust volumes
python scripts/volume.py dev up 5      # Increase dev volume by 5 steps
python scripts/volume.py commit down 2 # Decrease commit volume by 2 steps

# Check status
python scripts/volume-control/status.py
```

## 📋 Volume Control Examples

### Common Scenarios

**Quiet Coding** (minimal distractions):
```bash
python scripts/volume.py dev 50        # Light IDE features
python scripts/volume.py commit 200    # Basic commit checks
```

**Development Mode** (balanced):
```bash
python scripts/volume.py dev 200       # Standard IDE features  
python scripts/volume.py commit 500    # Comprehensive commit checks
```

**Production Ready** (maximum quality):
```bash
python scripts/volume.py dev 500       # Full IDE validation
python scripts/volume.py commit 1000   # Maximum commit validation
```

**Emergency Debugging** (complete silence):
```bash
python scripts/volume.py dev 0         # No IDE noise
python scripts/volume.py commit 0      # No commit checks
```

## 🔧 Validation & Utility Scripts

- **`validate_build_system.py`** - Validates build system configuration
- **`validate_configs.py`** - Validates project configuration files  
- **`validate_imports.py`** - Validates import statements across codebase
- **`validate_links.py`** - Validates external links in documentation
- **`validate_templates.py`** - Validates template files

## 🚀 Comprehensive Commit Scripts

These scripts provide a thorough code review workflow that runs comprehensive quality analysis with
AI enhancement before committing changes.

### Available Scripts

- **`comprehensive-commit.ps1`** - PowerShell script (recommended for Windows)
- **`comprehensive-commit.bat`** - Windows batch script
- **`commit.bat`** - Basic Windows commit script

### What These Scripts Do

1. **Pre-commit Hooks** - Runs all pre-commit hooks (Black, isort, Prettier, etc.)
2. **Comprehensive Quality Analysis** - Full analysis with all available tools
3. **AI-Enhanced Analysis** - AI-powered code review and suggestions
4. **Git Commit** - Commits changes with your message

### Basic Usage

```powershell
# Run the comprehensive commit script
.\scripts\comprehensive-commit.ps1 -Message "Your commit message"

# Optional parameters:
# -Message       : Commit message (required)
# -SkipTests     : Skip running tests
# -SkipLint      : Skip linting
# -SkipTypeCheck : Skip type checking
```

### Detailed Workflow

1. **Stage Changes** - `git add .`
2. **Run Script** - Execute the comprehensive commit script
3. **Review Results** - Check quality analysis and AI suggestions
4. **Commit** - Enter commit message and complete

### Expected Duration

- **Pre-commit hooks**: ~5-10 seconds
- **Comprehensive analysis**: ~60-120 seconds
- **AI-enhanced analysis**: ~30-60 seconds
- **Total time**: ~2-3 minutes

### Features

- ✅ **Error Handling** - Graceful failure with helpful messages
- ✅ **User Confirmation** - Option to continue even with warnings
- ✅ **Progress Tracking** - Clear step-by-step progress
- ✅ **Color Output** - PowerShell version with colored output
- ✅ **Validation** - Checks for git repository and staged changes

### Example Output

```text
========================================
 AutoPR Comprehensive Commit Script
========================================

[1/4] Running pre-commit hooks...
black................................................Passed
isort................................................Passed
prettier.................................................................Passed
Handle Unstaged Changes..................................................Passed

[2/4] Running comprehensive quality analysis...
[Quality Engine output with 3000+ issues found]

[3/4] Running AI-enhanced analysis...
[AI analysis with suggestions]

[4/4] Committing changes...
Enter commit message: Add new feature with comprehensive testing

========================================
 SUCCESS: Comprehensive commit completed!
========================================

Summary:
- Pre-commit hooks: PASSED
- Comprehensive quality analysis: COMPLETED
- AI-enhanced analysis: COMPLETED
- Git commit: SUCCESSFUL
```

## 🚨 Emergency/Nuclear Scripts

Legacy scripts for extreme linting control (use volume control instead):

- `nuclear-problems-fix.py` - Nuclear option to disable all IDE problems
- `super-nuclear-fix.py` - Temporarily disable problematic files
- `kill-all-validation.py` - Kill all validation systems
- `fix-extension-errors.py` - Fix extension cache errors
- `final-level-0-fix.py` - Apply Level 0 (silence) fixes

## 🔌 IDE Integration

### VS Code Setup

Add this to your `.vscode/tasks.json` to run the comprehensive commit script directly from VS Code:

```json
{
  "tasks": [
    {
      "label": "Comprehensive Commit",
      "type": "shell",
      "command": "powershell",
      "args": [
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "${workspaceFolder}/scripts/comprehensive-commit.ps1"
      ],
      "group": {
        "kind": "build",
        "isDefault": true
      },
      "presentation": {
        "reveal": "always",
        "panel": "shared"
      },
      "problemMatcher": []
    }
  ]
}
```

## 🛠 Troubleshooting

### Common Issues

**AI-Enhanced Analysis Fails**
- Verify your OpenAI API key is properly configured
- Check your internet connection
- You can continue with the commit using `-SkipAI` parameter

**Quality Analysis Finds Issues**
- Review the reported issues in detail
- Use volume control to adjust validation strictness
- For quick checks: `python -m autopr.actions.quality_engine --mode=fast`

**Pre-commit Hooks Fail**
- Fix any formatting/linting issues reported
- Run `pre-commit run --all-files` to test hooks separately
- Use volume control to temporarily reduce strictness if needed

## Customization

You can modify the scripts to:
- Change AI provider/model
- Add additional quality checks
- Customize error handling
- Add specific file patterns to analyze
