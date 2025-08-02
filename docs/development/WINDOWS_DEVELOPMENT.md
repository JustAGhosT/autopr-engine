# Windows Development Setup for AutoPR Engine

This document provides Windows-specific development setup instructions and workarounds for common
issues.

## Known Issues with Windows Store Python

The Microsoft Store version of Python has several limitations that can cause issues with development
tools, particularly pre-commit hooks:

### Problems:

- Pre-commit hooks may fail to install or run properly
- Virtualenv creation issues with specific Python versions
- Path resolution problems with development tools
- Limited access to certain system directories
- **Python 3.13.5 compatibility issues** with Windows Store installations

### Solutions:

#### Option 1: Use Manual Code Quality Scripts (Recommended)

Instead of relying on pre-commit hooks, use our provided scripts for code quality management:

```cmd
# Run all code quality checks before committing
scripts\code_quality.bat check

# Or run individual tools
scripts\code_quality.bat format
scripts\code_quality.bat lint
scripts\code_quality.bat test
```

#### Option 2: Install Standard Python 3.13.5 (Highly Recommended)

For the best development experience with Python 3.13.5, install from
[python.org](<https://python.org)> instead of the Microsoft Store version:

1. Uninstall Python from Microsoft Store
2. Download **Python 3.13.5** from [python.org](<https://python.org/downloads/release/python-3135/)>
3. Install with "Add Python to PATH" option checked
4. Create new virtual environment: `python -m venv .venv`
5. Activate environment: `.venv\Scripts\activate`
6. Reinstall dependencies: `pip install -r requirements-dev.txt`
7. Reinstall pre-commit hooks: `python -m pre_commit install`

#### Option 3: Use Git Hooks Manually

If you want to keep Windows Store Python, you can create manual git hooks:

1. Navigate to `.git/hooks/`
2. Create `pre-commit` file (no extension) with:

```bash
#!/bin/sh
echo "Running code quality checks..."
python scripts/code_quality.py check
if [ $? -ne 0 ]; then
    echo "Code quality checks failed. Please fix issues before committing."
    exit 1
fi
```

1. Make it executable: `chmod +x .git/hooks/pre-commit`

## Development Workflow

### Before Committing

Always run code quality checks before committing:

```cmd
# Format code
python -m black . --line-length 100
python -m isort . --profile black

# Check for issues
python -m flake8 . --max-line-length 100
python -m mypy . --config-file pyproject.toml

# Or use our convenience script
scripts\code_quality.bat check
```

### Commit Message Format

Use conventional commit messages:

```text
feat: add new feature
fix: resolve bug in component
docs: update documentation
style: format code
refactor: restructure module
test: add unit tests
chore: update dependencies
```

### Testing

Run tests before pushing:

```cmd
python -m pytest -v --cov=autopr --cov-report=term-missing
```

## IDE Configuration

### VS Code

Add these settings to your VS Code workspace (`.vscode/settings.json`):

```json
{
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "100"],
  "python.sortImports.args": ["--profile", "black"],
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.linting.flake8Args": ["--max-line-length=100"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### PyCharm

1. Go to File → Settings → Tools → External Tools
2. Add tools for Black, isort, flake8, and mypy
3. Configure keyboard shortcuts for quick access
4. Enable "Reformat code" and "Optimize imports" on commit

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure you're in the project root and virtual environment is activated
2. **Path issues**: Use forward slashes or raw strings in Python paths
3. **Permission errors**: Run terminal as administrator if needed
4. **Module not found**: Reinstall dependencies with `pip install -r requirements-dev.txt`

### Performance Tips

1. **Exclude large directories**: Add patterns to `.gitignore` and tool configurations
2. **Use incremental checks**: Run tools on changed files only during development
3. **Cache results**: Most tools cache results for faster subsequent runs

## Alternative Tools

If the standard tools don't work well on your system, consider these alternatives:

- **autopep8** instead of Black for formatting
- **pylint** instead of flake8 for linting
- **pyright** instead of mypy for type checking

Install alternatives:

```cmd
pip install autopep8 pylint pyright
```

## Adding Python to PATH (PowerShell)

If Python is not in your PATH or you need to add a specific Python installation:

### Temporary (Current Session Only)

```powershell
# Add Python to PATH for current PowerShell session
$env:PATH += ";C:\Python313;C:\Python313\Scripts"

# Or for a specific installation path
$env:PATH += ";C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python313;C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python313\Scripts"

# Also add user Scripts directory (needed for --user installed packages)
$env:PATH += ";C:\Users\$env:USERNAME\AppData\Roaming\Python\Python313\Scripts"
```

### Permanent (All Sessions)

```powershell
# Add Python to PATH permanently (requires admin privileges)
[Environment]::SetEnvironmentVariable("PATH", $env:PATH + ";C:\Python313;C:\Python313\Scripts", [EnvironmentVariableTarget]::Machine)

# Or for current user only (no admin required)
[Environment]::SetEnvironmentVariable("PATH", $env:PATH + ";C:\Python313;C:\Python313\Scripts", [EnvironmentVariableTarget]::User)
```

### Verify Python is in PATH

```powershell
# Check if Python is accessible
python --version
pip --version

# Show current PATH
$env:PATH -split ';' | Where-Object { $_ -like '*Python*' }
```

## Getting Help

If you encounter issues:

1. Check this document for known solutions
2. Try the manual workflow scripts
3. Consider switching to standard Python installation
4. Ask for help in project discussions or issues

Remember: The goal is consistent, high-quality code. The specific tools are less important than
maintaining standards.
