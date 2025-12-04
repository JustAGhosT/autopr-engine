# Template Engine Architecture

## Overview

The template engine provides flexible template processing for AutoWeave, supporting both simple and
complex templating scenarios.

## Core Components

### 1. Template Package Structure

```text

template-package/
├── template.yaml         # Metadata and configuration
├── main.j2               # Main template
├── partials/            # Reusable template parts
│   ├── header.j2
│   └── footer.j2
├── scripts/             # Post-processing scripts
│   └── post_generate.sh
└── tests/               # Template tests
    └── test_template.py
```

### 2. Template Metadata (template.yaml)

```yaml
id: "docker-app"
name: "Docker Application"
version: "1.0.0"
description: "Template for containerized applications"
author: "AutoWeave Team"

# Dependencies
requires:
  - name: "docker"
    version: ">=20.10"
  - name: "dotnet"
    version: ">=6.0"

# Template parameters
parameters:
  - name: "serviceName"
    type: "string"
    required: true
    description: "Name of the service"

# Content files
content:
  - type: "template"
    path: "main.j2"
    target: "{{serviceName}}/Dockerfile"
  - type: "script"
    path: "scripts/post_generate.sh"
    runOn: "post-generate"
```

### 3. Template Syntax

```jinja

# main.j2
FROM {{parameters.runtime}}:{{parameters.runtimeVersion}}

WORKDIR /app
COPY . .

# Include partial
{% include 'partials/header.j2' %}

# Conditional logic
{% if parameters.enableMonitoring %}
# Monitoring setup
ENV ENABLE_MONITORING=true
{% endif %}

# Loops
{% for env in parameters.environmentVariables %}
ENV {{env.name}}={{env.value}}
{% endfor %}
```

## Implementation Details

### 1. Template Processing Pipeline

1. **Load & Validate**: Parse template.yaml and validate schema
2. **Resolve Dependencies**: Check required tools/versions
3. **Gather Inputs**: Collect user parameters
4. **Render Templates**: Process all template files
5. **Post-process**: Run any post-generation scripts
6. **Output**: Generate final artifacts

### 2. Security Considerations

- Sandbox template execution
- Validate all user inputs
- Limit filesystem access
- Template signing and verification

### 3. Performance Optimizations

- Template compilation caching
- Parallel processing of independent templates
- Lazy loading of template dependencies

## Integration Points

- **CLI**: `autoweave template generate`
- **REST API**: `/api/templates/generate`
- **Build Pipeline**: Native integration with CI/CD

## Future Extensions

- Template inheritance
- Remote template repositories
- Template testing framework
- Visual template editor
