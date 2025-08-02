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

## 🔧 Validation & Utility Scripts

- **`validate_build_system.py`** - Validates build system configuration
- **`validate_configs.py`** - Validates project configuration files  
- **`validate_imports.py`** - Validates import statements across codebase
- **`validate_links.py`** - Validates external links in documentation
- **`validate_templates.py`** - Validates template files

## 🚨 Emergency/Nuclear Scripts

Legacy scripts for extreme linting control (use volume control instead):

- `nuclear-problems-fix.py` - Nuclear option to disable all IDE problems
- `super-nuclear-fix.py` - Temporarily disable problematic files
- `kill-all-validation.py` - Kill all validation systems
- `fix-extension-errors.py` - Fix extension cache errors
- `final-level-0-fix.py` - Apply Level 0 (silence) fixes

## 💾 Commit Scripts

- `commit.bat` - Windows commit script
- `comprehensive-commit.bat/ps1` - Enhanced commit with validation

## Usage

```bash
# Validation
python scripts/validate_build_system.py

# Volume control (recommended)
python scripts/volume.py dev 50
python scripts/volume-control/status.py

# Emergency silence (if needed)
python scripts/nuclear-problems-fix.py
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
