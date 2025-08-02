# Configuration and Template Extraction

This document describes the systematic extraction and organization of embedded JSON and YAML
configurations from the AutoPR engine codebase into a clean, maintainable directory structure.

## Overview

All embedded JSON and YAML configuration data has been extracted from Python files and organized
into two main directories:

- `configs/` - Reusable configuration files for platforms, packages, workflows, and triggers
- `templates/` - File generation templates for builds, deployments, testing, and monitoring

## Directory Structure

### Configs/ (Reusable Configuration Files)

````text
configs/
├── README.md                    # Configuration directory overview
├── platforms/                  # Platform-specific configurations
│   ├── replit.json             # Replit platform config
│   ├── lovable.json            # Lovable.dev platform config
│   ├── bolt.json               # Bolt.new platform config
│   ├── same.json               # Same.new platform config
│   └── emergent.json           # Emergent.sh platform config
├── packages/                   # Package dependency configurations
│   ├── security.json           # Security-related packages
│   ├── testing.json            # Testing framework packages
│   ├── performance.json        # Performance optimization packages
│   ├── development.json        # Development tool packages
│   └── monitoring.json         # Monitoring and logging packages
├── workflows/                  # Workflow YAML files (21 files)
│   ├── phase1_pr_review_workflow.yaml
│   ├── phase2-rapid-prototyping.yaml
│   ├── magic-fix.yaml
│   ├── automated_dependency_update.yaml
│   ├── branch_cleanup.yaml
│   ├── changelog_updater.yaml
│   ├── dead_code_report.yaml
│   ├── enhanced_pr_comment_handler.yaml
│   ├── onboard_contributor.yaml
│   ├── pr_comment_handler.yaml
│   ├── pr_size_labeler.yaml
│   ├── quality_gate.yaml
│   ├── release_drafter.yaml
│   ├── scaffold_component_workflow.yaml
│   ├── screenshot_gallery.yaml
│   ├── security_audit.yaml
│   ├── stale_issue_closer.yaml
│   ├── tech_debt_report.yaml
│   ├── update_documentation.yaml
│   └── ...
└── triggers/                   # Trigger configurations
    └── main-triggers.yaml      # Main workflow triggers

```text

### templates/ (File Generation Templates)

``` text
templates/
├── README.md                   # Template directory overview
├── typescript/                # TypeScript configuration templates
│   ├── react-tsconfig.json    # React TypeScript config
│   ├── vite-tsconfig.json     # Vite TypeScript config
│   └── basic-tsconfig.json    # Basic TypeScript config
├── build/                     # Build configuration templates
│   ├── vite.config.js         # Vite build configuration
│   ├── vitest.config.js       # Vitest testing configuration
│   ├── next.config.js         # Next.js configuration
│   └── pm2.config.js          # PM2 process manager config
├── docker/                    # Dockerfile templates
│   ├── react.dockerfile       # React application Dockerfile
│   ├── node.dockerfile        # Node.js application Dockerfile
│   └── generic.dockerfile     # Generic application Dockerfile
├── testing/                   # Testing setup templates
│   ├── test-setup.js          # Common test setup
│   ├── jest.config.js         # Jest configuration
│   ├── setupTests.ts          # React testing setup
│   ├── App.test.tsx           # Sample React test
│   └── playwright.config.ts   # Playwright E2E config
├── deployment/                # Deployment configuration templates
│   ├── azure-static-web-app.json  # Azure Static Web Apps config
│   └── github-actions-test.yml    # GitHub Actions test workflow
└── monitoring/                # Monitoring and backup scripts
    ├── health-check.sh        # Health check script
    ├── monitor.sh             # System monitoring script
    ├── backup.sh              # Backup script
    └── restore.sh             # Restore script
````

## Extraction Sources

### Python Files Processed

1. **file_generators.py** (873 lines) - Contains JSON templates for TypeScript configs, Dockerfiles,
   deployment configs, monitoring and backup scripts
2. **enhancement_strategies.py** (548 lines) - Contains build configs (Vite, Vitest), PM2 process
   manager config, and other template strings
3. **platform_configs.py** (572 lines) - Contains platform definitions, package dependency lists,
   deployment configurations, and production checklists

### YAML Files Organized

- **22 workflow YAML files** moved from `autopr/workflows/` to `configs/workflows/`
- **triggers.yaml** moved to `configs/triggers/main-triggers.yaml`

## Benefits Achieved

### Maintainability

- **Clear separation** between configuration data and business logic
- **Organized structure** with logical grouping of related files
- **Easy to find** and modify specific configurations
- **Version control friendly** with individual files for each configuration

### Reusability

- **Platform configurations** can be reused across different enhancement strategies
- **Package dependencies** organized by category for easy selection
- **Template files** can be used independently or combined
- **Workflow configurations** can be shared and customized

### Extensibility

- **Easy to add** new platforms by creating new JSON files in `configs/platforms/`
- **Simple to extend** package categories in `configs/packages/`
- **Straightforward** to add new templates in appropriate `templates/` subdirectories
- **Clear pattern** for adding new workflow configurations

### Developer Experience

- **IDE support** with proper JSON/YAML syntax highlighting and validation
- **Documentation** embedded in README files for each directory
- **Consistent structure** makes it easy to understand and navigate
- **Type safety** maintained through structured JSON schemas

## Next Steps

1. **Refactor Python modules** to load configurations from files instead of embedded literals
2. **Add configuration validation** to ensure loaded configs match expected schemas
3. **Create utility functions** for loading and caching configuration files
4. **Add unit tests** to verify correct loading and usage of externalized configs
5. **Update documentation** to reflect the new configuration management approach

## Usage Examples

### Loading Platform Configuration

```python
import json
from pathlib import Path

def load_platform_config(platform_name: str) -> dict:
    config_path = Path(f"configs/platforms/{platform_name}.json")
    with open(config_path, 'r') as f:
        return json.load(f)

# Usage
replit_config = load_platform_config("replit")
```

### Loading Package Dependencies

```python
def load_package_dependencies(category: str) -> dict:
    config_path = Path(f"configs/packages/{category}.json")
    with open(config_path, 'r') as f:
        return json.load(f)

# Usage
security_packages = load_package_dependencies("security")
```

### Loading Templates

```python
def load_template(category: str, template_name: str) -> str:
    template_path = Path(f"templates/{category}/{template_name}")
    with open(template_path, 'r') as f:
        return f.read()

# Usage
dockerfile_content = load_template("docker", "react.dockerfile")
tsconfig_content = load_template("typescript", "react-tsconfig.json")
```

This extraction significantly improves the maintainability, reusability, and clarity of
configuration management in the AutoPR engine while preserving all original functionality.
