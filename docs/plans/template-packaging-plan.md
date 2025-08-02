# Template Packaging & Modularization Plan

## Overview

This document outlines the strategy for migrating from inline/hardcoded templates to a structured,
maintainable template system with proper packaging and versioning.

## Current State Analysis

### Template Categories

1. **Docker Templates**
   - Generic and framework-specific Dockerfiles
   - Template metadata in YAML format

1. **Security Configs**
   - CORS, Helmet, and .htaccess configurations
   - Security headers and middleware settings

1. **Documentation**
   - Report templates
   - Guide templates
   - API documentation

1. **Platform Configs**
   - Framework-specific configurations
   - Build and deployment settings

1. **Code Templates**
   - TypeScript/React components
   - API routes
   - Test files

## Target Architecture

### Package Structure

```text

packages/
└── templates-core/               # Core templates package
    ├── src/
    │   ├── docker/              # Docker templates
    │   ├── security/            # Security configs
    │   ├── languages/           # Language-specific templates
    │   ├── platforms/           # Platform configs
    │   ├── docs/                # Documentation templates
    │   └── discovery/           # Discovery templates
    ├── tests/                   # Template tests
    └── pyproject.toml           # Package configuration
```

### Template Format

Each template will follow this structure:

```yaml
# metadata.yaml
template:
  name: "docker-node"
  description: "Production-ready Node.js Docker configuration"
  version: "1.0.0"
  tags: ["docker", "node", "production"]
  parameters:
    - name: "node_version"
      type: "string"
      default: "18"
      description: "Node.js version"
  files:
    - source: "Dockerfile.tpl"
      target: "Dockerfile"
      mode: "0644"
```

## Implementation Plan

### Phase 1: Foundation (2 days)

1. **Package Setup**
   - Create `packages/templates-core`
   - Set up Python package structure
   - Add build and test configuration

1. **Template Loader**
   - Implement template discovery
   - Add template validation
   - Create basic rendering engine

### Phase 2: Core Templates (3 days)

1. **Docker Templates**
   - Migrate existing Docker templates
   - Add template metadata
   - Create validation tests

1. **Security Templates**
   - Migrate security configs
   - Add parameterization
   - Document usage

### Phase 3: Documentation & Testing (2 days)

1. **Documentation**
   - Create template authoring guide
   - Document template variables
   - Add usage examples

1. **Testing**
   - Add template validation tests
   - Create rendering tests
   - Set up CI/CD

### Phase 4: Remaining Templates (3 days)

1. **Platform Configs**
   - Migrate platform-specific templates
   - Add parameterization
   - Update documentation

1. **Code Templates**
   - Migrate TypeScript/React templates
   - Add template variables
   - Create examples

## Template Authoring Guide

### Template Structure

```text

templates/
  <category>/
    <template-name>/
      metadata.yaml    # Template metadata
      files/           # Template files
      tests/           # Test cases
      README.md        # Documentation
```

### Metadata Specification

```yaml
# metadata.yaml
template:
  name: "string" # Unique template identifier
  description: "string" # Human-readable description
  version: "semver" # Template version
  tags: ["tag1", "tag2"] # Searchable tags
  parameters: # Template parameters
    - name: "param1"
      type: "string|number|boolean"
      default: "value"
      description: "string"
  files: # Template files
    - source: "relative/path.tpl"
      target: "output/path"
      mode: "0644" # File permissions
```

## Migration Strategy

1. **Incremental Migration**
   - Migrate one template category at a time
   - Update references incrementally
   - Maintain compatibility layer during transition

1. **Deprecation**
   - Mark old template locations as deprecated
   - Add warnings for deprecated usage
   - Remove in next major version

## Scripts & Related Files Migration

### Scripts to Migrate/Update

1. **Template Validation Scripts**
   - `scripts/validate_platforms.py` - Update to work with new template structure
   - `scripts/validate_template_schemas.py` - New script for schema validation
   - `scripts/test_template_rendering.py` - Test rendering with various inputs
   - Add new validation for template metadata
   - Integrate with CI/CD pipeline

1. **Generator Modules** (`autopr/actions/prototype_enhancement/generators/`)
   - `docker_generator.py` - Update to use new template loader
   - `security_generator.py` - Migrate to new template format
   - `docs_generator.py` - Update for new template structure
   - `template_utils.py` - Refactor for package-based templates

1. **Build & Test Scripts**
   - `scripts/code_quality.py` - Add template validation
   - `scripts/check-changes.sh` - Include template changes in checks
   - `scripts/type-check-info.sh` - Add template type checking
   - `.github/workflows/validate-templates.yml` - CI workflow for templates
   - `.github/workflows/publish-templates.yml` - Template publishing workflow

1. **Template Management Scripts**
   - `scripts/update_template_registry.py` - Maintain central template registry
   - `scripts/check_template_compatibility.py` - Validate cross-template compatibility
   - `scripts/convert_legacy_templates.py` - Migrate old template formats
   - `scripts/verify_migration.py` - Verify migration completeness

1. **Documentation Scripts**
   - `scripts/generate_template_reference.py` - Generate template reference docs
   - `scripts/update_readmes.py` - Keep READMEs in sync with templates
   - `scripts/generate-docs.py` - Comprehensive documentation generator

### Migration Strategy 2

1. **Phase 1: Script Audit & Preparation**
   - Inventory all scripts that interact with templates
   - Document required changes for each script
   - Create test cases for script functionality
   - Set up test environment with sample templates

1. **Phase 2: Core Script Updates**
   - Update template loading in generator modules
   - Modify validation scripts for new structure
   - Update build/test scripts to handle new locations
   - Implement new template management scripts

1. **Phase 3: Testing & Validation**
   - Test template rendering across all formats
   - Validate template metadata schemas
   - Verify cross-template compatibility
   - Test migration paths for existing templates

1. **Phase 4: Documentation & CI/CD**
   - Generate updated documentation
   - Update README files
   - Set up CI/CD workflows
   - Create rollback procedures

1. **Phase 5: Migration & Deployment**
   - Run migration scripts
   - Verify all templates work as expected
   - Deploy updated templates
   - Monitor for issues

### Script-Specific Migration Details

#### Template Management Scripts

- **`update_template_registry.py`**:
  - Scans template directories
  - Updates central registry with metadata
  - Validates template uniqueness
  - Generates template index

- **`check_template_compatibility.py`**:
  - Validates dependencies between templates
  - Checks version compatibility
  - Verifies required parameters

#### Documentation Scripts

- **`generate_template_reference.py`**:
  - Extracts docstrings and metadata
  - Generates markdown reference
  - Updates documentation site

- **`update_readmes.py`**:
  - Syncs template documentation
  - Updates usage examples
  - Validates links

#### CI/CD Workflows

- **`validate-templates.yml`**:
  - Runs on PRs
  - Validates template syntax
  - Tests rendering
  - Checks documentation

- **`publish-templates.yml`**:
  - Version bumps
  - Builds packages
  - Publishes to registry
  - Updates changelog

## Future Enhancements

1. **Template Registry**
   - Central template repository
   - Versioned templates
   - Dependency management

1. **CLI Tools**
   - Template scaffolding
   - Interactive prompts
   - Validation utilities

1. **Editor Integration**
   - VS Code extension
   - Syntax highlighting
   - IntelliSense for template variables
