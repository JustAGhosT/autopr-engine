# 20. Package Naming Convention: codeflow_engine

## Status

Accepted

## Date

2025-12-08

## Context

The project was initially named "autopr" with the Python package "autopr". As the project evolved into a more comprehensive automation platform, a rename was needed to better reflect its scope and avoid namespace conflicts with other automation tools.

The package needed to:
- Reflect the broader scope beyond just pull requests
- Use Python naming conventions (snake_case)
- Be distinct from the CLI/user-facing name
- Avoid conflicts in the Python package ecosystem

## Decision

Rename the Python package from `autopr` to `codeflow_engine` while maintaining user-facing names for backward compatibility.

### Package Structure

- **Python Package**: `codeflow_engine` (snake_case for Python convention)
- **PyPI Distribution**: `codeflow-engine` (kebab-case for package managers)
- **CLI Tools**: `autopr`, `autopr-server`, `autopr-worker`, `autopr-migration` (maintained for backward compatibility)
- **Configuration Files**: `autopr.yaml`, `autopr.yml` (maintained for backward compatibility)
- **Plugin Namespaces**: `autopr.actions`, `autopr.integrations`, `autopr.llm_providers` (maintained for backward compatibility)

### Import Changes

```python
# Before
from autopr.engine import AutoPREngine
from autopr.config import AutoPRConfig
from autopr.actions.platform_detector import PlatformDetector

# After
from codeflow_engine.engine import AutoPREngine
from codeflow_engine.config import AutoPRConfig
from codeflow_engine.actions.platform_detector import PlatformDetector
```

## Rationale

### Why "codeflow_engine"

1. **Scope Reflection**: "codeflow" better represents the full automation pipeline beyond just PRs
2. **Engine Suffix**: Indicates it's an underlying engine/platform, not just an application
3. **Python Convention**: snake_case aligns with PEP 8 naming conventions
4. **Namespace Clarity**: Distinguishes the core engine from integrations and plugins
5. **Avoids Conflicts**: Unique name in PyPI and Python package ecosystem

### Backward Compatibility Strategy

1. **User-Facing Names**: CLI commands remain `autopr` for existing scripts and workflows
2. **Configuration Files**: Still look for `autopr.yaml` to avoid breaking user configs
3. **Plugin System**: Plugin namespaces use `autopr.*` for community plugin compatibility
4. **Documentation**: Clear migration guide for any custom code
5. **Gradual Transition**: Phased approach allows users to migrate at their own pace

## Implementation Details

### Updated Files

1. **Package Directory**: `autopr/` → `codeflow_engine/`
2. **pyproject.toml**: Updated package declaration, coverage paths, isort config
3. **setup.py**: Updated entry points and package references
4. **All Python Files**: Updated 697+ import statements
5. **Tests**: Updated all test imports and mocking references
6. **Documentation**: Updated code examples and guides

### Plugin System Compatibility

The plugin system maintains backward compatibility by keeping the `autopr.*` namespace:

```python
[tool.poetry.plugins."autopr.actions"]
"platform_detector" = "codeflow_engine.actions.platform_detector:PlatformDetector"

[tool.poetry.plugins."autopr.integrations"]
"github" = "codeflow_engine.integrations.github:GitHubIntegration"

[tool.poetry.plugins."autopr.llm_providers"]
"openai" = "codeflow_engine.ai.providers.openai:OpenAIProvider"
```

This allows third-party plugins to continue using the familiar `autopr.*` namespace while the core package uses `codeflow_engine`.

## Consequences

### Positive

- **Clear Identity**: Better reflects the project's full capabilities
- **Python Standards**: Aligns with Python naming conventions (PEP 8)
- **Namespace Safety**: Reduces risk of conflicts with other packages
- **Extensibility**: "engine" suffix indicates a platform for building on
- **Backward Compatibility**: User-facing tools maintain familiar names

### Negative

- **Migration Effort**: Existing code using the package needs imports updated
- **Documentation Updates**: All docs needed updating to reflect new name
- **Search/Discovery**: Some search results may reference old name
- **Learning Curve**: Users need to understand dual naming (CLI vs package)

### Neutral

- **Community Plugins**: Plugin developers need to understand namespace mapping
- **Import Length**: `codeflow_engine` is longer than `autopr` (14 vs 6 characters)

## Migration Guide

### For End Users (CLI)

No changes needed! CLI commands remain the same:
```bash
autopr --help
autopr-server start
autopr-worker run
```

### For Developers (Using as Library)

Update imports in your code:

```python
# Old imports
from autopr.engine import AutoPREngine
from autopr.config import AutoPRConfig

# New imports
from codeflow_engine.engine import AutoPREngine
from codeflow_engine.config import AutoPRConfig
```

Use find-replace in your codebase:
```bash
find . -name "*.py" -exec sed -i 's/from autopr\./from codeflow_engine./g' {} \;
```

### For Plugin Authors

Package imports use the new name, but plugin namespaces remain:

```python
# Your plugin code uses new package name
from codeflow_engine.actions.base import Action

# But your plugin.yaml still uses old namespace
[tool.poetry.plugins."autopr.actions"]
"my_custom_action" = "my_package.actions:MyAction"
```

## Timeline

- **2025-12-08**: Package rename completed
- **2025-12-08**: Documentation updated
- **2025-12-08**: All tests passing with new imports
- **Q1 2026**: Deprecation notices for any remaining `autopr` references
- **Q2 2026**: Full transition to `codeflow_engine` branding

## Related Decisions

- [ADR-0019: Python-Only Architecture](0019-python-only-architecture.md) - Core technology decision
- [ADR-0005: Configuration Management](0005-configuration-management.md) - Configuration file names
- [ADR-0006: Plugin System Design](0006-plugin-system-design.md) - Plugin namespace conventions

## References

- PEP 8 - Style Guide for Python Code: https://peps.python.org/pep-0008/
- Python Packaging User Guide: https://packaging.python.org/
- Semantic Versioning: https://semver.org/
