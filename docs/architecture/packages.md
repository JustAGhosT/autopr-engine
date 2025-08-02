# AutoPR Package Architecture

## Overview

AutoPR is built as a modular system with a clear separation of concerns across multiple packages,
supporting both .NET and Python runtimes. This document outlines the package structure,
responsibilities, and relationships between different components.

## Core Packages (NuGet/.NET)

### AutoPR.Core

**NuGet**: `AutoPR.Core`**Purpose**: Core interfaces, models, and shared utilities used throughout
the platform.

**Key Components**:

- Base interfaces for plugins and extensions
- Core domain models and DTOs
- Common utilities and helpers
- Base exception types
- Configuration models

### AutoPR.Plugins

**NuGet**: `AutoPR.Plugins`**Purpose**: Base interfaces and utilities for developing AutoPR plugins.

**Key Components**:

- `IPlugin` interface
- Plugin lifecycle management
- Plugin configuration schemas
- Base classes for common plugin types
- Plugin metadata attributes

### AutoPR.Extensions

**NuGet**: `AutoPR.Extensions`**Purpose**: Common extensions and utilities used across the platform.

**Key Components**:

- Collection extensions
- String utilities
- Reflection helpers
- Async utilities
- Validation extensions

## Language-Specific Runtimes

### AutoPR.Python

**NuGet**: `AutoPR.Python`**Purpose**: Python runtime integration for AutoPR.

**Features**:

- Python 3.13+ script execution
- Virtual environment management
- Dependency resolution with pip/conda
- Python code analysis and introspection
- Integration with ML/AI frameworks (PyTorch, TensorFlow)
- Template processing and generation
- Asynchronous task execution
- GIL-aware thread pooling

### AutoPR.Node

**NuGet**: `AutoPR.Node`**Purpose**: Node.js runtime integration for AutoPR.

**Features**:

- Node.js 22+ script execution
- NPM/Yarn/PNPM package management
- Dependency resolution and auditing
- JavaScript/TypeScript code analysis
- Integration with frontend build tools

## Client Libraries

### @autopr/client (npm)

**Package**: `@autopr/client`**Language**: TypeScript/JavaScript**Purpose**: Official
TypeScript/JavaScript client for interacting with AutoPR services.

**Features**:

- Type-safe API client
- Promise-based interface
- Browser and Node.js support
- Authentication helpers
- WebSocket support for real-time updates

### AutoPR.Client (NuGet)

**NuGet**: `AutoPR.Client`**Language**: C#**Purpose**: Official .NET client for AutoPR services.

**Features**:

- Strongly-typed client
- Async/await support
- Dependency injection integration
- Comprehensive XML documentation
- Built-in retry policies

## Plugin Development

### Plugin Types

1. **Integration Plugins**: Connect to external services (GitHub, GitLab, etc.)
2. **Template Plugins**: Provide templates for PRs, issues, etc.
3. **Analysis Plugins**: Perform code analysis and provide insights
4. **Workflow Plugins**: Define custom workflows and automation

### Plugin Structure

```text
myplugin/
├── src/
│   ├── index.ts          # Plugin entry point
│   ├── config.schema.ts  # Configuration schema
│   └── ...               # Plugin implementation
├── package.json          # Plugin metadata and dependencies
└── README.md             # Documentation
```

### Development Guidelines

- Follow the Plugin Development Kit (PDK) conventions
- Implement required interfaces
- Provide comprehensive documentation
- Include unit and integration tests
- Support configuration via environment variables
- Implement proper error handling and logging

## Plugin Packages

### @autopr/plugin-github

**Package**: `@autopr/plugin-github`**Type**: Integration Plugin**Purpose**: GitHub integration for
AutoPR.

**Features**:

- Repository management
- Pull request automation
- Status checks and required contexts
- Webhook handling and validation
- GitHub Actions integration
- GitHub Apps support
- Fine-grained permissions

### @autopr/plugin-azure

**Package**: `@autopr/plugin-azure`**Type**: Integration Plugin**Purpose**: Azure DevOps integration
for AutoPR.

**Features**:

- Azure Repos integration
- Pull request automation
- Pipeline integration and gating
- Work item linking and tracking
- Azure DevOps REST API client
- Service principal authentication

### @autopr/plugin-gitlab

**Package**: `@autopr/plugin-gitlab`**Type**: Integration Plugin**Purpose**: GitLab integration for
AutoPR.

**Features**:

- GitLab repository integration
- Merge request automation
- CI/CD pipeline integration
- Issue and epic linking
- GitLab API client with pagination
- Group and subgroup support

### @autopr/plugin-autoweave

**Package**: `@autopr/plugin-autoweave`**Type**: Integration Plugin**Purpose**: AutoWeave
integration for AutoPR.

**Features**:

- Bidirectional synchronization
- Template and asset management
- Configuration synchronization
- Status reporting
- Webhook support

## Template System

### Core Template Packages

#### @autoweave/template-engine

**Package**: `@autoweave/template-engine`**Purpose**: Core template processing engine.

**Features**:

- Multi-template language support (Liquid, Handlebars, etc.)
- Template inheritance and composition
- Built-in template functions and filters
- Caching and incremental rendering
- Dependency tracking

#### @autoweave/template-sdk

**Package**: `@autoweave/template-sdk`**Purpose**: Development kit for creating custom templates.

**Features**:

- TypeScript/JavaScript API
- Template validation and linting
- Testing utilities
- Debugging tools
- Documentation generation

#### @autoweave/template-registry

**Package**: `@autoweave/template-registry`**Purpose**: Central template repository and management.

**Features**:

- Template discovery and resolution
- Versioning and semantic version support
- Access control and permissions
- Template metadata and documentation
- Dependency management

### Standard Template Packages

#### @autoweave/templates-standard

**Package**: `@autoweave/templates-standard`**Type**: Template Package**Purpose**: Standard Pull
Request templates for common scenarios.

**Included Templates**:

- Feature PR template
- Bugfix PR template
- Documentation PR template
- Chore/refactor PR template
- Release PR template
- Hotfix template
- Experimental feature template

#### @autoweave/templates-security

**Package**: `@autoweave/templates-security`**Type**: Template Package**Purpose**: Security-focused
PR templates and workflows.

**Included Templates**:

- Security vulnerability fix template
- Dependency update template
- Security policy update template
- Security review checklist
- CVE mitigation template
- Secret rotation template
- Compliance documentation template

#### @autoweave/templates-ai

**Package**: `@autoweave/templates-ai`**Type**: Template Package**Purpose**: AI/ML focused
templates.

**Included Templates**:

- Model training PR
- Dataset update
- Feature engineering
- Hyperparameter tuning
- Model evaluation report

## Package Relationships

```mermaid
graph TD
    %% Core Packages
    A[AutoPR.Core] --> B[AutoPR.Plugins]
    A --> C[AutoPR.Extensions]

    %% Language Runtimes
    B --> D[AutoPR.Python]
    B --> E[AutoPR.Node]

    %% Client Libraries
    A --> F[@autopr/client]
    A --> G[AutoPR.Client]

    %% Plugin Packages
    B --> H[@autopr/plugin-github]
    B --> I[@autopr/plugin-azure]
    B --> J[@autopr/plugin-gitlab]
    B --> K[@autopr/plugin-autoweave]

    %% Template System
    A --> L[@autoweave/template-engine]
    L --> M[@autoweave/template-sdk]
    L --> N[@autoweave/template-registry]

    %% Template Packages
    N --> O[@autoweave/templates-standard]
    N --> P[@autoweave/templates-security]
    N --> Q[@autoweave/templates-ai]

    %% Python Services
    D --> R[autopr-python]
    R --> S[autopr.ai]
    R --> T[autopr.templates]
    R --> U[autopr.analysis]

    %% Styling
    classDef core fill:#f9f,stroke:#333
    classDef plugin fill:#9cf,stroke:#333
    classDef template fill:#9f9,stroke:#333
    classDef python fill:#f99,stroke:#333

    class A,B,C core
    class H,I,J,K plugin
    class L,M,N,O,P,Q template
    class R,S,T,U python

    linkStyle 0,1,2,3 stroke:#333,stroke-width:2px
    linkStyle 4,5,6,7,8,9,10,11,12,13 stroke:#999,stroke-width:1px,stroke-dasharray: 5 5

## Versioning and Compatibility

### Package Versioning
All packages follow [Semantic Versioning](https://semver.org/) (SemVer):
- **MAJOR** version for incompatible API changes
- **MINOR** version for backward-compatible functionality
- **PATCH** version for backward-compatible bug fixes

### Template Versioning
Templates use a modified semantic versioning scheme:
- **MAJOR**: Breaking changes to template structure or required context
- **MINOR**: New features or non-breaking changes
- **PATCH**: Bug fixes and improvements
- **PRERELEASE**: Optional pre-release identifiers for development versions

### Compatibility Matrix
| Component             | Min .NET Version | Min Python Version | Node.js Version |
| --------------------- | ---------------- | ------------------ | --------------- |
| Core                  | .NET 9.0         | 3.13               | N/A             |
| Python Services       | N/A              | 3.13+              | N/A             |
| Node.js Plugins       | N/A              | N/A                | 18.x+           |
| Template Engine       | .NET 9.0         | 3.13+              | N/A             |
| AutoWeave Integration | .NET 9.0         | 3.13+              | N/A             |

## Contributing

To contribute to any of the packages:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Update documentation
5. Add/update tests
6. Submit a pull request

## License

All packages are licensed under the MIT License unless otherwise specified.
```
