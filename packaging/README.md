# AutoPR Engine - Package Manager Distributions

This directory contains package definitions for various package managers.

## Available Packages

| Package Manager | Platform | Status | Installation |
|-----------------|----------|--------|--------------|
| [Homebrew](homebrew/) | macOS, Linux | Template | `brew install JustAGhosT/tap/codeflow-engine` |
| [Chocolatey](chocolatey/) | Windows | Template | `choco install codeflow-engine` |
| PyPI | All | Published | `pip install codeflow-engine` |

## Homebrew (macOS/Linux)

### For Users

```bash
# Add the tap
brew tap JustAGhosT/tap

# Install
brew install codeflow-engine

# Or one-liner
brew install JustAGhosT/tap/codeflow-engine
```

### For Maintainers

1. Update the formula version in `homebrew/codeflow-engine.rb`
2. Calculate SHA256: `shasum -a 256 codeflow-engine-X.Y.Z.tar.gz`
3. Update the SHA256 in the formula
4. Push to the tap repository

## Chocolatey (Windows)

### For Users

```powershell
choco install codeflow-engine
```

### For Maintainers

1. Update version in `chocolatey/codeflow-engine.nuspec`
2. Build the package:
   ```powershell
   cd packaging/chocolatey
   choco pack
   ```
3. Test locally:
   ```powershell
   choco install codeflow-engine -s .
   ```
4. Push to Chocolatey:
   ```powershell
   choco push codeflow-engine.X.Y.Z.nupkg --source https://push.chocolatey.org/
   ```

## PyPI (All Platforms)

The primary distribution method. See root `pyproject.toml`.

```bash
# Build
poetry build

# Publish
poetry publish
```

## Adding New Package Managers

To add support for a new package manager:

1. Create a new directory: `packaging/<manager>/`
2. Add the package definition files
3. Document installation in this README
4. Add to the table above
5. Create CI workflow if automated publishing is needed

## Version Synchronization

All package versions should match the version in `pyproject.toml`.

Current version: **1.0.1**
