# Code Quality Management for AutoPR Engine

This document describes the code quality tools and processes implemented for the AutoPR Engine
project.

## Overview

The AutoPR Engine project uses a comprehensive set of code quality tools to ensure consistent,
maintainable, and secure code:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting with additional plugins
- **mypy**: Static type checking
- **bandit**: Security vulnerability scanning
- **pydocstyle**: Docstring style checking
- **pre-commit**: Git hooks for automated quality checks
- **commitizen**: Conventional commit message formatting

## Pre-commit Hooks

Pre-commit hooks are automatically installed and will run on every commit. The hooks include:

### Code Formatting

- **Black**: Formats Python code with 100-character line length
- **isort**: Sorts and organizes imports

### Linting and Type Checking

- **flake8**: Comprehensive linting with plugins:
  - `flake8-docstrings`: Docstring linting
  - `flake8-bugbear`: Bug and design problem detection
  - `flake8-comprehensions`: List/dict comprehension improvements
  - `flake8-simplify`: Code simplification suggestions
- **mypy**: Static type checking with strict configuration
- **bandit**: Security vulnerability scanning
- **pydocstyle**: Docstring style enforcement

### File Quality Checks

- Trailing whitespace removal
- End-of-file fixing
- YAML, TOML, and JSON validation
- Large file detection
- Merge conflict detection
- Debug statement detection

### Documentation and Configuration

- **Prettier**: YAML formatting
- **hadolint**: Dockerfile linting
- **shellcheck**: Shell script linting

## Manual Usage

### Using the Python Script

The `scripts/code_quality.py` script provides convenient commands:

```bash
# Format code
python scripts/code_quality.py format

# Run linting tools
python scripts/code_quality.py lint

# Run tests
python scripts/code_quality.py test

# Check dependencies for vulnerabilities
python scripts/code_quality.py security

# Install pre-commit hooks
python scripts/code_quality.py pre-commit install

# Run pre-commit hooks manually
python scripts/code_quality.py pre-commit run

# Run all quality checks
python scripts/code_quality.py check
```

### Using the Windows Batch Script

For Windows users, `scripts/code_quality.bat` provides the same functionality:

```cmd
# Format code
scripts\code_quality.bat format

# Run linting tools
scripts\code_quality.bat lint

# Run tests
scripts\code_quality.bat test

# Check dependencies for vulnerabilities
scripts\code_quality.bat security

# Install pre-commit hooks
scripts\code_quality.bat install

# Run all quality checks
scripts\code_quality.bat check
```

### Direct Tool Usage

You can also run tools directly:

```bash
# Format code
python -m black . --line-length 100
python -m isort . --profile black

# Lint code
python -m flake8 . --max-line-length 100
python -m mypy . --config-file pyproject.toml
python -m bandit -r . -c pyproject.toml

# Run tests
python -m pytest -v --cov=autopr --cov-report=term-missing

# Check dependencies
python -m safety check

# Run pre-commit hooks
python -m pre_commit run --all-files
```

## Configuration

All tools are configured in `pyproject.toml`:

### Black Configuration

- Line length: 100 characters
- Target Python version: 3.8+
- Excludes common build directories

### Isort Configuration

- Profile: black (compatible with Black)
- Line length: 100 characters
- Known first-party: autopr
- Known third-party packages listed

### Mypy Configuration

- Strict type checking enabled
- Python version: 3.8
- Comprehensive warnings enabled
- Third-party modules with missing stubs ignored

### Flake8 Configuration

- Max line length: 100 characters
- Ignores: E203 (whitespace before ':'), W503 (line break before binary operator)
- Per-file ignores: F401 in `__init__.py` files

### Bandit Configuration

- Skips: B101 (assert used), B601 (shell injection)
- Excludes: tests, docs, migrations directories

### Pydocstyle Configuration

- Relaxed docstring requirements for development
- Excludes test files
- Focuses on critical docstring issues

## CI/CD Integration

The pre-commit hooks ensure code quality before commits reach the repository. For CI/CD pipelines,
you can run:

```bash
# Install and run all pre-commit hooks
python -m pre_commit install
python -m pre_commit run --all-files

# Or use the comprehensive check
python scripts/code_quality.py check
```

## Development Workflow

1. **Before committing**: Pre-commit hooks run automatically
2. **Manual checks**: Use `scripts/code_quality.py check` for comprehensive validation
3. **Fix issues**: Address any linting or formatting issues
4. **Commit**: Use conventional commit messages (enforced by commitizen)

## Conventional Commits

The project uses conventional commit messages enforced by commitizen:

````text
feat: add new feature
fix: fix bug
docs: update documentation
style: formatting changes
refactor: code refactoring
test: add tests
chore: maintenance tasks

```text

## Troubleshooting

### Pre-commit Hook Failures

If pre-commit hooks fail:

1. Review the error messages
2. Fix the issues manually or run the formatting tools
3. Stage the changes and commit again

### Skipping Hooks (Emergency Only)

To skip pre-commit hooks in emergencies:

```bash
git commit --no-verify -m "emergency commit message"

```text

### Updating Hooks

To update pre-commit hook versions:

```bash
python -m pre_commit autoupdate

```text

## Benefits

This code quality setup provides:

- **Consistency**: Uniform code style across the project
- **Quality**: Early detection of bugs and issues
- **Security**: Automated vulnerability scanning
- **Maintainability**: Well-formatted, typed, and documented code
- **Efficiency**: Automated checks reduce manual review time
- **Standards**: Enforced coding standards and best practices

## Dependencies

All code quality tools are included in `requirements-dev.txt` and will be installed with:

```bash
pip install -r requirements-dev.txt

```text

The tools are also available as optional dependencies:

```bash
pip install -e ".[dev]"

```text
````
