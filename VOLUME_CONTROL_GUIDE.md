# 🎛️ AutoPR Volume Control System Guide

## 🎯 Overview

The AutoPR Volume Control System provides **HiFi-style volume control** for your development environment, allowing you to adjust the strictness of linting and quality checks from 0-1000 in ticks of 5. This system was successfully integrated from PR #14 and provides granular control over your development experience.

## 🚀 Quick Start

### Check Current Status
```bash
python scripts/volume-control/main.py status
```

### Set Development Volume
```bash
# Set to specific level
python scripts/volume-control/main.py dev 300

# Adjust incrementally
python scripts/volume-control/main.py dev up 1
python scripts/volume-control/main.py dev down 1
```

### Set Commit Volume
```bash
# Set to specific level
python scripts/volume-control/main.py commit 500

# Adjust incrementally
python scripts/volume-control/main.py commit up 1
python scripts/volume-control/main.py commit down 1
```

### Auto-fix Issues
```bash
python scripts/volume-control/main.py autofix
```

## 📊 Volume Levels

| Volume | Level | Description | Use Case |
|--------|-------|-------------|----------|
| 0-100 | QUIET | Basic syntax only | Prototyping, experiments |
| 200-400 | LOW | Basic formatting | Development, learning |
| 500-600 | MEDIUM | Standard checks | Regular development |
| 700-800 | HIGH | Strict checks | Code review, quality focus |
| 900-1000 | MAXIMUM | Nuclear - everything blocks | Production, strict compliance |

## 🛠️ Integrated Components

### ✅ Successfully Integrated from PR #14

1. **Volume Control System**
   - `scripts/volume-control/main.py` - Main CLI interface
   - `scripts/volume-control/config_loader.py` - Configuration management
   - `scripts/volume-control/volume_knob.py` - Volume adjustment logic
   - `scripts/volume-control/status.py` - Status reporting

2. **Configuration Files**
   - `.volume-dev.json` - Development environment settings
   - `.volume-commit.json` - Commit-time settings
   - `scripts/volume-control/configs/` - Tool-specific configurations

3. **IDE Integration**
   - `.cursorrules` - Cursor IDE development guidelines
   - `.windsurfrules` - Windsurf IDE development guidelines
   - `.vscode/settings.json` - VS Code integration

4. **Documentation**
   - `VOLUME_200_SETTINGS.md` - Volume level 200 documentation
   - `check_active_tools.py` - Tool verification utility

5. **Linting Configurations**
   - `.flake8` - Python linting configuration
   - `.yamlignore` - YAML file exclusions

## 🎮 Usage Examples

### Development Workflow

1. **Start with QUIET for prototyping:**
   ```bash
   python scripts/volume-control/main.py dev 75
   ```

2. **Increase as you refine:**
   ```bash
   python scripts/volume-control/main.py dev 300
   ```

3. **Use HIGH for final review:**
   ```bash
   python scripts/volume-control/main.py dev 700
   ```

4. **Auto-fix issues:**
   ```bash
   python scripts/volume-control/main.py autofix
   ```

### Commit Workflow

1. **Set commit volume higher than dev:**
   ```bash
   python scripts/volume-control/main.py commit 500
   ```

2. **Verify before committing:**
   ```bash
   python scripts/volume-control/main.py status
   ```

3. **Auto-fix commit issues:**
   ```bash
   python scripts/volume-control/main.py autofix
   ```

## 🔧 Configuration

### Tool Configurations

The system supports configurations for:
- **Python**: Linting, formatting, type checking
- **Git**: Integration and hooks
- **GitHub Actions**: Workflow validation
- **JSON**: Schema validation
- **TypeScript**: Type checking and formatting
- **YAML**: Validation and formatting
- **PowerShell**: Script analysis
- **Problems**: IDE problem reporting

### Customizing Configurations

Edit files in `scripts/volume-control/configs/` to customize tool behavior:

```bash
# View available configurations
ls scripts/volume-control/configs/

# Edit a specific tool config
code scripts/volume-control/configs/python.json
```

## 🎯 Integration with Quality Engine

The volume control system integrates seamlessly with the AutoPR Quality Engine:

```bash
# Run Quality Engine with volume-aware settings
python -m autopr.actions.quality_engine --mode=smart

# The Quality Engine automatically respects volume settings
```

## 🔍 Monitoring and Debugging

### Check Active Tools
```bash
python check_active_tools.py
```

### Debug Volume Settings
```bash
python scripts/volume-control/main.py debug
```

### View Configuration Details
```bash
python scripts/volume-control/main.py status --verbose
```

## 🚨 Troubleshooting

### Common Issues

1. **Volume not applying:**
   - Reload your IDE window
   - Restart the Python language server
   - Check for configuration conflicts

2. **Pre-commit hooks not working:**
   - Verify pre-commit is installed: `pip install pre-commit`
   - Install hooks: `pre-commit install`

3. **Tool availability:**
   - Use `check_active_tools.py` to verify tool installation
   - Install missing tools as needed

### Reset to Defaults
```bash
# Reset development volume
python scripts/volume-control/main.py dev 75

# Reset commit volume
python scripts/volume-control/main.py commit 200
```

## 🎉 Benefits

### ✅ What We Achieved

1. **Granular Control**: Fine-tuned development experience
2. **Separate Dev/Commit Volumes**: Different strictness for different contexts
3. **Auto-fix Integration**: Automatic issue resolution
4. **IDE Integration**: Seamless editor experience
5. **Comprehensive Documentation**: Clear usage guidelines

### 🚀 Key Features

- **HiFi-style Volume Control**: 0-1000 scale with 5-tick increments
- **Dual Volume System**: Separate dev and commit environments
- **Auto-fix Capability**: Automatic issue resolution
- **Tool Integration**: Works with all major development tools
- **IDE Support**: Cursor, Windsurf, VS Code integration
- **Pre-commit Integration**: Automated quality gates

## 📈 Next Steps

1. **Customize Configurations**: Adjust tool settings to your preferences
2. **Set Up Workflows**: Configure volume levels for different scenarios
3. **Team Integration**: Share volume settings with your team
4. **CI/CD Integration**: Use volume control in automated pipelines

## 🎯 Success Metrics

- ✅ **Volume Control System**: Fully integrated and functional
- ✅ **Auto-fix Feature**: Working with Quality Engine integration
- ✅ **IDE Integration**: Cursor and Windsurf rules integrated
- ✅ **Documentation**: Comprehensive guides and examples
- ✅ **Configuration Management**: Flexible tool configurations
- ✅ **Pre-commit Integration**: Automated quality gates

The volume control system is now **fully operational** and ready for production use! 🎉
