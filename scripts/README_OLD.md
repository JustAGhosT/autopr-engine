# AutoPR Scripts

This directory contains utility scripts for the AutoPR Engine project.

## Comprehensive Commit Scripts

These scripts provide a thorough code review workflow that runs comprehensive quality analysis with
AI enhancement before committing changes.

### Available Scripts

- **`comprehensive-commit.bat`** - Windows batch script
- **`comprehensive-commit.ps1`** - PowerShell script (recommended for Windows)

### What These Scripts Do

1. **Pre-commit Hooks** - Runs all pre-commit hooks (Black, isort, Prettier, etc.)
2. **Comprehensive Quality Analysis** - Full analysis with all available tools
3. **AI-Enhanced Analysis** - AI-powered code review and suggestions
4. **Git Commit** - Commits changes with your message

### Usage

#### Prerequisites

1. Stage your changes first:

   ```bash
   git add .
   ```

2. Make sure you have the required dependencies:
   - Python with AutoPR Engine installed
   - Pre-commit hooks configured
   - OpenAI API key (for AI-enhanced analysis)

#### Running the Scripts

**PowerShell (Recommended):**

```powershell
.\scripts\comprehensive-commit.ps1
```

**Batch Script:**

```cmd
scripts\comprehensive-commit.bat
```

### Workflow

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

Your code has been thoroughly reviewed and committed.
```

### Troubleshooting

#### AI-Enhanced Analysis Fails

- This is experimental and may not work in all environments
- You can continue with the commit even if AI analysis fails
- Check your OpenAI API key configuration

#### Quality Analysis Finds Issues

- Review the issues and fix critical problems
- You can choose to continue with the commit anyway
- Consider running `python -m autopr.actions.quality_engine --mode=fast` for quick checks

#### Pre-commit Hooks Fail

- Fix the formatting/linting issues
- Re-run the script after fixing issues
- Use `pre-commit run --all-files` to test hooks separately

### Integration with IDE

> You can integrate these scripts into your IDE:

**VS Code:**

```json
{
  "tasks": [
    {
      "label": "Comprehensive Commit",
      "type": "shell",
      "command": "powershell",
      "args": ["-ExecutionPolicy", "Bypass", "-File", "./scripts/comprehensive-commit.ps1"],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      }
    }
  ]
}
```

### Customization

You can modify the scripts to:

- Change AI provider/model
- Add additional quality checks
- Customize error handling
- Add specific file patterns to analyze
