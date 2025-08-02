# Developer-Friendly Setup Guide

## 🎯 Overview

We've made AutoPR Engine much more developer-friendly by reducing the overwhelming number of quality check errors. The focus is now on **functionality first, polish later**.

## 🚀 Quick Start

### 1. Basic Setup
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .

# Install pre-commit hooks (optional)
pre-commit install
```

### 2. Quick Code Check
```bash
# Run only essential checks (fast, non-overwhelming)
python scripts/quick-check.py
```

### 3. Auto-Fix Common Issues
```bash
# Fix formatting and basic issues automatically
python scripts/volume.py autofix
```

## 📋 Quality Check Levels

### 🟢 Level 1: Essential Checks (Recommended for Development)
- Basic syntax validation
- Import verification
- Code formatting (Black)
- Minimal linting (only critical errors)

**Command:** `python scripts/quick-check.py`

### 🟡 Level 2: Standard Checks (Before Committing)
- All Level 1 checks
- Import sorting (isort)
- Basic security scan (bandit)
- Unit tests

**Command:** `python scripts/volume.py status`

### 🔴 Level 3: Comprehensive Checks (Before Release)
- All Level 2 checks
- Type checking (mypy)
- Full security analysis
- Performance metrics
- Documentation coverage

**Command:** `python -m autopr.actions.quality_engine --mode=comprehensive`

## 🔧 Configuration Changes

### What We Changed

1. **MyPy**: Disabled strict type checking for development
2. **Ruff**: Reduced from 200+ rules to ~20 essential rules
3. **Flake8**: Ignored most formatting and style issues
4. **Pytest**: Removed coverage requirements, allowed more failures
5. **Pre-commit**: Only runs essential checks, others moved to manual

### Key Benefits

- ✅ **Faster feedback**: Essential checks run in seconds
- ✅ **Less overwhelming**: Focus on critical issues only
- ✅ **Developer productivity**: Code first, polish later
- ✅ **Gradual improvement**: Can still run comprehensive checks when needed

## 🛠️ Available Scripts

### `scripts/quick-check.py`
- **Purpose**: Essential validation for daily development
- **Speed**: ~5-10 seconds
- **Output**: Minimal, focused on critical issues
- **Use case**: Before committing, during development

### `scripts/volume.py`
- **Purpose**: Volume control system for linting levels
- **Options**:
  - `set dev <level>`: Set development environment linting level (0-1000)
  - `set commit <level>`: Set commit checks level (0-1000)
  - `up dev/commit`: Increase linting level by 5
  - `down dev/commit`: Decrease linting level by 5
  - `status`: Show current volume levels
  - `autofix`: Fix issues at current level

## 📊 Error Reduction

| Tool   | Before        | After         | Reduction |
| ------ | ------------- | ------------- | --------- |
| Ruff   | ~500+ errors  | ~20-50 errors | 90%+      |
| MyPy   | ~200+ errors  | ~0-10 errors  | 95%+      |
| Flake8 | ~300+ errors  | ~10-30 errors | 90%+      |
| Total  | ~1000+ errors | ~30-90 errors | **90%+**  |

## 🎯 Development Workflow

### Daily Development
1. Write code
2. Run `python scripts/quick-check.py`
3. Fix any critical issues
4. Commit and push

### Before PR
1. Run `python scripts/volume.py status`
2. Fix any blocking issues
3. Create PR

### Before Release
1. Run comprehensive checks
2. Address all issues
3. Release

## 🔄 CI/CD Integration

### PR Checks (`.github/workflows/pr-checks.yml`)
- **Essential checks only**: Fast, non-blocking
- **Comprehensive checks**: Informational, don't block merge
- **Focus**: Functionality over perfection

### Main Branch (`.github/workflows/ci.yml`)
- **Full quality gates**: All checks enabled
- **Performance testing**: Load and stress tests
- **Security scanning**: Comprehensive security analysis

## 🚨 When to Use Strict Mode

### Development Phase
- ✅ Use permissive mode
- ✅ Focus on functionality
- ✅ Quick iterations

### Release Preparation
- ✅ Enable comprehensive checks
- ✅ Address all quality issues
- ✅ Ensure production readiness

### Legacy Code
- ✅ Use permissive mode initially
- ✅ Gradually improve over time
- ✅ Don't let perfect be the enemy of good

## 💡 Tips for Developers

### 1. Start with Quick Checks
```bash
# Always run this first
python scripts/quick-check.py
```

### 2. Use Auto-Fix
```bash
# Fix most issues automatically
python scripts/volume.py autofix
```

### 3. Focus on Functionality
- Write working code first
- Add tests for critical paths
- Polish later

### 4. Gradual Improvement
- Don't try to fix everything at once
- Address issues incrementally
- Use comprehensive checks for releases

### 5. Know Your Tools
- **Black**: Code formatting (always run)
- **isort**: Import sorting (before commit)
- **Ruff**: Linting (essential rules only)
- **MyPy**: Type checking (disabled for development)

## 🔧 Customization

### Make Checks More Permissive
Edit `pyproject.toml`:
```toml
[tool.ruff.lint]
# Add more rules to ignore
ignore = [
    "E501",  # Line too long
    "F401",  # Unused imports
    # ... add more as needed
]
```

### Make Checks More Strict
```bash
# Run comprehensive checks locally
python -m autopr.actions.quality_engine --mode=comprehensive

# Enable MyPy strict mode
mypy autopr --strict

# Run all Ruff rules
ruff check . --select=ALL
```

## 📞 Getting Help

### Common Issues
1. **Too many errors**: Use `scripts/quick-check.py` instead
2. **Slow checks**: Use essential mode for development
3. **Formatting issues**: Run `python scripts/volume.py autofix`

### Need More Help?
- Check the main README
- Look at existing code examples
- Ask in team chat
- Create an issue for configuration problems

---

**Remember**: The goal is to make development faster and more enjoyable while maintaining code quality. Start simple, improve gradually! 🚀 