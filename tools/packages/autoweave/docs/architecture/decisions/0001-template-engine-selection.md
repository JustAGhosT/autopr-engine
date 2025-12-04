# ADR 0001: Template Engine Selection

## Status

✅ Accepted

## Context

We need to select a template language and structure for AutoWeave's template system that balances
power, familiarity, and maintainability. The template engine will be used across multiple components
including the CI/CD pipeline, CLI, and web UI.

## Decision

We will implement a multi-file template system using:

1. **Template Language**: Jinja2-style syntax (via Scriban)
2. **Metadata Format**: YAML
3. **Structure**: Multi-file template packages

## Rationale

1. **Jinja2/Scriban** offers the best balance of power and familiarity:
   - Supports complex logic, loops, and conditionals
   - Familiar to DevOps and platform engineers
   - Good performance characteristics
   - Strong .NET support through Scriban

1. **YAML** was chosen over JSON for metadata because:
   - More readable and writable by humans
   - Better support for comments
   - Widely used in DevOps tools (Kubernetes, Ansible, etc.)
   - Good tooling support in .NET

1. **Multi-file structure** was selected because:
   - Better organization of complex templates
   - Easier maintenance and version control
   - Supports separation of concerns
   - Enables partial templates and reuse

## Consequences

### Positive

- **Familiarity**: Uses technologies well-known in the target audience
- **Power**: Handles complex templating scenarios
- **Maintainability**: Clear separation of concerns
- **Extensibility**: Easy to add new features and integrations
- **Tooling**: Good IDE support and syntax highlighting

### Negative

- **Learning Curve**: More complex than simpler alternatives like Handlebars
- **Performance**: Slightly more overhead than lighter alternatives
- **Security**: Requires careful sandboxing of template execution
- **Dependencies**: Adds external dependencies (Scriban, YamlDotNet)

## Alternatives Considered

### 1. Handlebars/Mustache

**Pros**:

- Simpler to learn
- Logic-less (prevents complex logic in templates)
- Better performance for simple cases

**Cons**:

- Too limited for complex scenarios
- Would require workarounds for common patterns
- Less familiar to target audience

### 2. Go Templates

**Pros**:

- Popular in cloud-native ecosystem
- Strong typing
- Good performance

**Cons**:

- Less common in .NET ecosystem
- More verbose syntax
- Smaller community than Jinja2

### 3. Custom DSL

**Pros**:

- Perfect fit for exact requirements
- No external dependencies

**Cons**:

- High maintenance cost
- Steeper learning curve
- Limited tooling
- No community support

## Implementation Notes

- Use Scriban as the template engine
- Implement strict sandboxing for security
- Add validation for template metadata
- Include comprehensive error messages
- Provide clear documentation and examples

## Related Work

- [Scriban Documentation](<https://github.com/scriban/scriban)>
- [YAML Specification](<https://yaml.org/spec/)>
- [Template System Requirements](./../template_engine.md)

## Decision Makers

- Architecture Team
- Lead Developer
- Security Team

## Date

2025-07-28
