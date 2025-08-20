# Volume Control System for AutoPR Engine

A HiFi-style volume control system with **JSON-based configuration** for precise linting control.

## 🎛️ Overview

This system provides **two volume knobs**:

- **Dev Volume**: Controls IDE linting (VS Code/Cursor)
- **Commit Volume**: Controls pre-commit checks

Each volume level has **specific checks and configurations** stored in JSON files for each tool.

## 🎯 Volume Levels

### Level 0: OFF

- **Description**: No linting - pure coding experience
- **Dev Checks**: None
- **Commit Checks**: None
- **Use Case**: When you want zero interference

### Level 100: QUIET

- **Description**: Basic syntax only - minimal interference
- **Dev Checks**: `syntax_errors`
- **Commit Checks**: `syntax_check`
- **Use Case**: When you want only critical errors

### Level 1000: MAXIMUM

- **Description**: Nuclear mode - everything enabled
- **Dev Checks**: `syntax_errors`, `type_checking`
- **Commit Checks**: All checks enabled
- **Use Case**: When you want maximum code quality

## 🔧 Usage

### From Main Directory

```bash
# Set dev volume to OFF
python scripts/volume.py dev 0

# Set dev volume to QUIET
python scripts/volume.py dev 100

# Set dev volume to MAXIMUM
python scripts/volume.py dev 1000

# Set commit volume
python scripts/volume.py commit 0
python scripts/volume.py commit 100
python scripts/volume.py commit 1000

# Check status
python scripts/volume.py status

# Autofix current level
python scripts/volume.py autofix
```

### From Volume Control Directory

```bash
cd scripts/volume-control

# Same commands as above
python main.py dev 0
python main.py dev 100
python main.py dev 1000
```

## 🎛️ Volume Control Commands

### Set Volume

```bash
python scripts/volume.py dev <0|100|1000>
python scripts/volume.py commit <0|100|1000>
```

### Volume Up/Down

```bash
python scripts/volume.py dev up [steps]
python scripts/volume.py dev down [steps]
python scripts/volume.py commit up [steps]
python scripts/volume.py commit down [steps]
```

### Status and Help

```bash
python scripts/volume.py status
python scripts/volume.py help
python scripts/volume.py autofix
```

## 🏗️ Architecture

### JSON-Based Configuration System

Each tool has its own JSON configuration file with settings for each level:

```
scripts/volume-control/configs/
├── vscode.json          # VS Code settings per level
├── ruff.json           # Ruff configuration per level
├── pyright.json        # Pyright configuration per level
└── pre_commit.json     # Pre-commit hooks per level
```

### File Structure

```
scripts/volume-control/
├── __init__.py
├── main.py              # Main CLI interface
├── volume_knob.py       # Volume knob classes
├── json_migrations.py   # JSON-based migration system
├── migrations.py        # Legacy migration system
├── dev_configs.py       # Legacy dev configs
├── commit_configs.py    # Legacy commit configs
├── configs/             # JSON configuration files
│   ├── vscode.json
│   ├── ruff.json
│   ├── pyright.json
│   └── pre_commit.json
└── README.md
```

## 🎯 JSON Configuration System

The system uses **JSON configuration files** for each tool:

### VS Code Configuration (`configs/vscode.json`)

```json
{
  "0": {
    "name": "OFF",
    "description": "No linting - pure coding experience",
    "settings": {
      "python.linting.enabled": false,
      "ruff.enable": false
    }
  },
  "100": {
    "name": "QUIET",
    "description": "Basic syntax only",
    "settings": {
      "python.linting.enabled": true,
      "python.linting.maxNumberOfProblems": 5
    }
  }
}
```

### Ruff Configuration (`configs/ruff.json`)

```json
{
  "0": {
    "name": "OFF",
    "enabled": false,
    "config": null
  },
  "100": {
    "name": "QUIET",
    "enabled": true,
    "config": {
      "select": ["E", "F"],
      "ignore": ["E501", "W291"],
      "line_length": 120
    }
  }
}
```

## 🔄 Adding New Levels

To add a new level (e.g., Level 500):

1. **Add to VS Code config** (`configs/vscode.json`):

```json
"500": {
  "name": "MEDIUM",
  "description": "Balanced linting",
  "settings": {
    "python.linting.maxNumberOfProblems": 50,
    "python.analysis.typeCheckingMode": "basic"
  }
}
```

2. **Add to Ruff config** (`configs/ruff.json`):

```json
"500": {
  "name": "MEDIUM",
  "enabled": true,
  "config": {
    "select": ["E", "F", "W", "I"],
    "line_length": 88
  }
}
```

3. **Add to other tool configs** as needed

The system will automatically find the closest level for any volume setting.

## 🎛️ The "Yeah Right" Problem Solved

This system solves the "yeah right" problem by:

- **Level 0**: Guarantees zero linting errors
- **JSON Configuration**: Easy to read and modify
- **Tool-Specific Configs**: Each tool has its own settings
- **Gradual Control**: Tune up one level at a time
- **Specific Checks**: Each level has exactly the checks you want
- **Environment Refresh**: Automatically refreshes IDE settings when changing levels

## 🚀 Quick Start

1. **Start with Level 0** (no linting):

   ```bash
   python scripts/volume.py dev 0
   python scripts/volume.py commit 0
   ```

2. **Environment refresh** happens automatically when changing levels

3. **Gradually increase** as needed:

   ```bash
   python scripts/volume.py dev 100  # Basic syntax
   python scripts/volume.py autofix  # Fix issues
   ```

4. **Check status** anytime:
   ```bash
   python scripts/volume.py status
   ```

## 🎯 Benefits of JSON Configuration

- **Readable**: Easy to understand what each level does
- **Maintainable**: Each tool has its own config file
- **Extensible**: Easy to add new tools or levels
- **Version Control**: JSON files can be tracked in git
- **Modular**: Each tool is independent

## 🔄 Environment Refresh

When you change volume levels, the system automatically:

1. **Applies new settings** to VS Code configuration
2. **Creates/removes config files** (`.ruff.toml`, `pyrightconfig.json`)
3. **Triggers environment refresh** to pick up changes
4. **Provides helpful instructions** for manual refresh if needed

**Automatic refresh includes:**

- Touch file creation to trigger IDE file watchers
- VS Code window reload attempt (if `code` command is available)
- Clear instructions for manual refresh if automatic fails

**Manual refresh options:**

- Reload VS Code window: `Ctrl+Shift+P` → "Developer: Reload Window"
- Restart Python language server: `Ctrl+Shift+P` → "Python: Restart Language Server"
- Restart your IDE completely

## 🎯 Next Steps

- [ ] Add intermediate levels (50, 200, 300, etc.)
- [ ] Add more tools (black, isort, bandit, etc.)
- [ ] Implement autofix for each level
- [ ] Add pre-commit configuration updates
- [ ] Add VS Code extension management
- [ ] Add workspace-specific settings
