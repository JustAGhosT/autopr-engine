# Python 3.13.5 Upgrade Guide

## Overview

This document outlines the upgrade of the AutoPR Engine project from Python 3.8+ to Python 3.13.5,
including all necessary configuration changes, dependency updates, and compatibility considerations.

## What Changed

### 1. Python Version Requirements

- **Minimum Python version**: Upgraded from `>=3.8` to `>=3.9`
- **Target Python version**: Updated to Python 3.13.5
- **Dropped support**: Python 3.8 is no longer supported

### 2. Configuration Files Updated

#### Pyproject.toml

- Updated `requires-python = ">=3.9"`
- Added Python 3.13 classifier
- Updated Black target version to `py313`
- Updated all core dependencies to Python 3.13 compatible versions

#### Setup.py

- Updated `python_requires=">=3.9"`

#### .pre-commit-config.yaml

- Updated Black version to `24.8.0`
- Set `language_version: python3.13` for Black hook
- Updated `default_language_version` to `python3.13`

#### Requirements-dev.txt

- Updated all development dependencies to latest Python 3.13 compatible versions

### 3. Dependency Updates

#### Core Dependencies (pyproject.toml)

```toml
# Major version updates
"pydantic>=2.9.0,<3.0.0"          # Was: 2.0.0
"aiohttp>=3.10.0,<4.0.0"          # Was: 3.8.0
"structlog>=24.4.0,<25.0.0"       # Was: 22.0.0
"pygithub>=2.4.0,<3.0.0"          # Was: 1.58.0
"openai>=1.51.0,<2.0.0"           # Was: 1.0.0
"anthropic>=0.34.0,<1.0.0"        # Was: 0.25.0
"httpx>=0.27.0,<1.0.0"            # Was: 0.24.0
"websockets>=13.1.0,<14.0.0"      # Was: 11.0.0
```

#### Development Dependencies

```txt
# Testing framework
pytest>=8.3.0,<9.0.0              # Was: 7.4.0
pytest-cov>=5.0.0,<6.0.0          # Was: 4.1.0

# Code quality tools
black>=24.8.0,<25.0.0             # Was: 23.7.0
flake8>=7.0.0,<8.0.0              # Was: 6.0.0
mypy>=1.11.0,<2.0.0               # Was: 1.5.0
pre-commit>=3.0.0,<4.0.0          # Was: 3.4.0, updated to use available versions

# Documentation
sphinx>=8.1.0,<9.0.0              # Was: 7.1.0
sphinx-rtd-theme>=3.0.0,<4.0.0    # Was: 1.3.0
myst-parser>=4.0.0,<5.0.0         # Was: 2.0.0
```

### 4. Removed Dependencies

- **asyncio**: Removed as it's built into Python 3.13
- **toml**: Replaced with `tomli>=2.0.1,<3.0.0` for better Python 3.13 compatibility

## Python 3.13.5 New Features

### Performance Improvements

- **Free-threaded CPython**: Experimental support for running without the Global Interpreter Lock
  (GIL)
- **JIT Compiler**: Experimental Just-In-Time compiler for improved performance
- **Improved asyncio**: Better performance and memory usage for async operations

### Language Features

- **Enhanced error messages**: More detailed and helpful error messages
- **Improved typing**: Better type inference and error reporting
- **New syntax features**: Various syntax improvements and new operators

### Standard Library Updates

- **pathlib improvements**: Enhanced Path operations
- **asyncio enhancements**: Better async context management
- **typing improvements**: More precise type annotations

## Migration Steps

### 1. Install Python 3.13.5

#### Windows (Recommended)

```cmd
# Download from python.org (NOT Microsoft Store)
# https://www.python.org/downloads/release/python-3135/

# Verify installation
python --version
# Should output: Python 3.13.5
```

#### Alternative: Using pyenv (Windows/Linux/macOS)

```bash
# Install pyenv if not already installed
pyenv install 3.13.5
pyenv global 3.13.5
```

### 2. Update Virtual Environment

```cmd
# Remove old virtual environment
rmdir /s .venv

# Create new virtual environment with Python 3.13.5
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# Verify Python version
python --version
```

### 3. Install Updated Dependencies

```cmd
# Install production dependencies
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
pre-commit install --hook-type commit-msg
```

### 4. Verify Installation

```cmd
# Run code quality checks
scripts\code_quality.bat check

# Run tests
pytest

# Verify pre-commit hooks
pre-commit run --all-files
```

## Compatibility Notes

### Breaking Changes

1. **Python 3.8 no longer supported**: Code using Python 3.8-specific features may need updates
2. **Dependency version bumps**: Some dependencies have breaking changes in major version updates
3. **Type checking improvements**: MyPy 1.11+ may catch new type errors

### Known Issues

1. **Windows Store Python**: Still not recommended due to pre-commit compatibility issues
2. **Some packages**: May not have Python 3.13 wheels available yet - will build from source

### Backward Compatibility

- **Python 3.9+**: All features remain compatible
- **Existing code**: Should work without modifications
- **Configuration**: All existing configurations remain valid

## Testing Strategy

### 1. Automated Testing

```cmd
# Run full test suite
pytest --cov=autopr --cov-report=html

# Run specific test categories
pytest -m "not slow"  # Skip slow tests
pytest -m integration # Integration tests only
```

### 2. Code Quality Verification

```cmd
# Full code quality check
scripts\code_quality.bat check

# Individual checks
scripts\code_quality.bat format
scripts\code_quality.bat lint
scripts\code_quality.bat security
```

### 3. Pre-commit Hook Testing

```cmd
# Test all hooks
pre-commit run --all-files

# Test specific hooks
pre-commit run black --all-files
pre-commit run mypy --all-files
```

## Rollback Plan

If issues arise, you can rollback to Python 3.11:

### 1. Revert Configuration Files

```cmd
git checkout HEAD~1 -- pyproject.toml setup.py .pre-commit-config.yaml requirements-dev.txt
```

### 2. Reinstall Python 3.13

```cmd
# Install Python 3.13
pyenv install 3.13.5
pyenv global 3.13.5

# Recreate virtual environment
rmdir /s .venv
python -m venv .venv
.venv\Scripts\activate
```

### 3. Reinstall Dependencies

```cmd
pip install -e .
pip install -r requirements-dev.txt
pre-commit install
```

## Benefits of Python 3.13.5

### 1. Performance

- **Up to 15% faster** execution for many workloads
- **Improved memory usage** for async operations
- **Better garbage collection** performance

### 2. Developer Experience

- **Enhanced error messages** with better context
- **Improved type checking** with MyPy integration
- **Better debugging** capabilities

### 3. Security

- **Latest security patches** and improvements
- **Enhanced SSL/TLS** support
- **Improved cryptographic** libraries

### 4. Future-Proofing

- **Long-term support** until 2029
- **Access to latest features** and improvements
- **Better ecosystem compatibility**

## Support and Troubleshooting

### Common Issues

1. **Import errors**: Some packages may need updates

   ```cmd
   pip install --upgrade package-name
   ```

1. **Type checking errors**: Update type annotations

   ```python
   # Old (Python 3.8)
   from typing import List, Dict

   # New (Python 3.13)
   # Can use built-in types directly
   def func(items: list[str]) -> dict[str, int]:
       pass
   ```

1. **Pre-commit failures**: Update hook versions

   ```cmd
   pre-commit autoupdate
   pre-commit run --all-files
   ```

### Getting Help

- **Documentation**: Check Python 3.13 release notes
- **Issues**: Create GitHub issues for project-specific problems
- **Community**: Python Discord, Stack Overflow for general Python 3.13 questions

## Conclusion

The upgrade to Python 3.13.5 provides significant performance improvements, enhanced developer
experience, and future-proofing for the AutoPR Engine project. All dependencies have been updated to
compatible versions, and the migration process is straightforward.

The project now benefits from the latest Python features while maintaining backward compatibility
with existing code and configurations.
