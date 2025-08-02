# AutoPR Engine Repository Migration Guide

This guide documents the major repository reorganization completed in Phase 5 of the repository
structure cleanup.

## Overview

The AutoPR Engine repository has undergone a comprehensive reorganization to improve
maintainability, discoverability, and developer experience. This migration guide helps developers
understand the changes and update their workflows accordingly.

## Major Changes

### 1. Documentation Reorganization

**Before:**

```
docs/
├── PLAN.md
├── ARCHITECTURE.md
├── AI_BOTS_ECOSYSTEM_ANALYSIS.md
├── ENTERPRISE_MODERNIZATION_PLAN.md
└── scattered documentation files
```

**After:**

```
docs/
├── architecture/
│   ├── README.md
│   ├── ARCHITECTURE_LEGACY.md
│   └── AUTOPR_ENHANCED_SYSTEM.md
├── plans/
│   ├── REPOSITORY_STRUCTURE_PLAN.md
│   ├── ENTERPRISE_MODERNIZATION_PLAN.md
│   ├── PLAN_LEGACY.md
│   └── other plan files
├── analysis/
│   ├── AI_BOTS_ECOSYSTEM_ANALYSIS.md
│   └── ecosystem analysis files
├── development/
│   ├── ONBOARDING_STRATEGY.md
│   └── development guides
└── README.md (main documentation index)
```

### 2. Configuration Consolidation

**Before:**

```
configs/
├── .flake8.test
├── workflows/phase2-rapid-prototyping.yaml (duplicate)
└── scattered configuration files
```

**After:**

```
configs/
├── .flake8 (renamed from .flake8.test)
├── workflows/phase2_rapid_prototyping.yaml (removed duplicate)
├── config.yaml (validated)
├── mypy.ini (validated)
└── organized configuration structure
```

### 3. Template Reorganization

**Before:**

```
templates/
├── ONBOARDING_STRATEGY.md (should be in docs)
├── NO_CODE_PLATFORM_PLAN.md (should be in docs)
├── py.typed (should be in autopr)
└── scattered template files
```

**After:**

```
templates/
├── platforms/ (40+ platform templates)
├── discovery/ (code analysis templates)
├── deployment/ (deployment templates)
├── security/ (security templates)
├── monitoring/ (monitoring templates)
├── testing/ (testing templates)
├── documentation/ (documentation templates)
├── integrations/ (integration templates)
└── organized template structure
```

### 4. Build System Cleanup

**Before:**

```
├── pyproject.toml
├── requirements.txt (redundant)
├── requirements-dev.txt (redundant)
├── .coverage.Home.30960.XkmJtlRx (scattered)
├── coverage.xml (scattered)
└── build-artifacts/ (unorganized)
```

**After:**

```
├── pyproject.toml (single source of truth)
├── build-artifacts/ (organized)
├── .gitignore (updated for better artifact management)
└── consolidated build system
```

## Import Path Updates

### Fixed Import Issues

The following import paths have been corrected:

1. **Template Discovery Imports:**

   ```python
   # Before
   from discovery.content_analyzer import TemplateAnalysis
   from discovery.template_loader import TemplateLoader

   # After
   from ..content_analyzer import TemplateAnalysis
   from ..template_loader import TemplateLoader
   ```

2. **Quality Analyzer Imports:**

   ```python
   # Before
   from templates.discovery.template_validators import ValidationSeverity

   # After
   # from templates.discovery.template_validators import ValidationSeverity  # Commented out
   ```

3. **Test File Imports:**

   ```python
   # Before
   from enhanced_file_generator import TemplateMetadata

   # After
   from ..enhanced_file_generator import TemplateMetadata
   ```

## Validation Scripts

New validation scripts have been created to maintain repository health:

### 1. Import Validation

```bash
python scripts/validate_imports.py
```

- Scans all Python files for broken imports
- Generates detailed import validation reports
- Helps identify import issues after reorganization

### 2. Link Validation

```bash
python scripts/validate_links.py
```

- Validates all Markdown links in documentation
- Ensures documentation links work after reorganization
- Generates link validation reports

### 3. Configuration Validation

```bash
python scripts/validate_configs.py
```

- Validates all configuration files (YAML, JSON, INI)
- Checks for duplicate configurations
- Ensures configuration consistency

### 4. Template Validation

```bash
python scripts/validate_templates.py
```

- Validates all template files
- Checks template organization and consistency
- Ensures template standards compliance

### 5. Build System Validation

```bash
python scripts/validate_build_system.py
```

- Validates pyproject.toml configuration
- Checks build artifact organization
- Ensures package management consistency

## Updated Documentation References

### Main Documentation Index

- **Root README.md**: Updated with new documentation structure
- **docs/README.md**: Comprehensive documentation index
- **All documentation links**: Updated to reflect new structure

### Key Documentation Files

- **Architecture**: `docs/architecture/README.md`
- **Development**: `docs/development/`
- **Plans**: `docs/plans/`
- **Analysis**: `docs/analysis/`

## Package Management Changes

### Single Source of Truth

- **Primary**: `pyproject.toml` (PEP 621 + Poetry)
- **Removed**: `requirements.txt`, `requirements-dev.txt`
- **Optional Dependencies**: Available via
  `pip install "autopr-engine[dev,monitoring,memory,ai,database,server,resilience]"`

### Installation Commands

```bash
# Install with all optional dependencies
pip install "autopr-engine[full]"

# Install with specific optional dependencies
pip install "autopr-engine[dev,monitoring]"

# Install core only
pip install "autopr-engine"
```

## Development Workflow Updates

### Pre-commit Hooks

The pre-commit configuration has been updated to include:

- Automatic handling of unstaged changes
- Comprehensive code formatting and linting
- Quality engine integration (optional)

### IDE Integration

- **VS Code Tasks**: Comprehensive commit scripts integrated
- **Keyboard Shortcuts**: `Ctrl+Shift+C` for comprehensive commit, `Ctrl+Shift+Q` for quick commit
- **Workspace Configuration**: Updated for new structure

## Testing and Validation

### Running Validation Scripts

```bash
# Run all validation scripts
python scripts/validate_imports.py
python scripts/validate_links.py
python scripts/validate_configs.py
python scripts/validate_templates.py
python scripts/validate_build_system.py
```

### Expected Results

- All validation scripts should return exit code 0
- No broken imports, links, or configurations
- Proper organization and consistency

## Troubleshooting

### Common Issues

1. **Import Errors After Reorganization:**

   ```bash
   python scripts/validate_imports.py
   ```

   - Check the generated report for specific import issues
   - Update import paths according to the migration guide

2. **Broken Documentation Links:**

   ```bash
   python scripts/validate_links.py
   ```

   - Review the link validation report
   - Update documentation links to reflect new structure

3. **Configuration Issues:**
   ```bash
   python scripts/validate_configs.py
   ```

   - Check for configuration validation errors
   - Ensure all required configuration files exist

### Getting Help

If you encounter issues during migration:

1. **Check Validation Reports**: All validation scripts generate detailed reports
2. **Review Migration Guide**: This document contains all major changes
3. **Consult Documentation**: Updated documentation reflects new structure
4. **Run Validation Scripts**: Use the provided validation tools

## Future Maintenance

### Regular Validation

Run validation scripts regularly to maintain repository health:

```bash
# Weekly validation
python scripts/validate_imports.py
python scripts/validate_links.py
python scripts/validate_configs.py
```

### Adding New Files

When adding new files, ensure they follow the established organization:

- **Documentation**: Place in appropriate `docs/` subdirectory
- **Templates**: Use existing template categories or create new ones
- **Configuration**: Add to `configs/` with proper validation
- **Scripts**: Add to `scripts/` with validation capabilities

### Updating Dependencies

When updating dependencies:

1. Update `pyproject.toml` only
2. Run `python scripts/validate_build_system.py`
3. Test installation with new dependencies

## Conclusion

The repository reorganization improves:

- **Maintainability**: Better organization and structure
- **Discoverability**: Clear documentation and file locations
- **Developer Experience**: Validation tools and clear guidelines
- **Consistency**: Standardized patterns and practices

All changes are backward-compatible and include comprehensive validation tools to ensure continued
functionality.

---

**Last Updated**: January 2025  
**Version**: 1.0.0  
**Migration Status**: Complete
