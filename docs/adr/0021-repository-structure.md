# 21. Repository Structure and Monorepo vs Multi-Repo Strategy

## Status

Proposed

## Date

2025-12-08

## Context

The codeflow-engine project has grown significantly and now encompasses multiple distinct concerns:

1. **Core Engine**: The main automation and workflow engine
2. **Web UI/Dashboard**: React-based user interface
3. **VS Code Extension**: Editor integration
4. **Desktop Application**: Electron-based desktop app (autopr-desktop)
5. **Documentation Website**: Marketing and documentation site
6. **Template System**: Reusable workflow templates
7. **Infrastructure**: Kubernetes, Terraform, deployment configs

Currently, all these components live in a single monorepo, which has both advantages and growing pains.

### Current Repository Structure

```
codeflow-engine/
├── codeflow_engine/        # Python core engine
├── autopr-desktop/          # Electron desktop app
├── vscode-extension/        # VS Code extension
├── website/                 # Documentation/marketing site
├── templates/               # Workflow templates
├── infrastructure/          # K8s, Bicep, Terraform
├── docs/                    # Documentation
├── tools/                   # Development tools
└── tests/                   # Test suite
```

### Problems with Current Structure

1. **Build Complexity**: Single CI/CD pipeline for multiple technologies
2. **Dependency Conflicts**: Python, Node.js, .NET tools in one repo
3. **Release Cycles**: Different components need different release schedules
4. **Team Boundaries**: Different teams work on different components
5. **Clone Size**: Large repository slows initial clones and fetches
6. **Testing**: Full test suite runs even for unrelated changes
7. **Permissions**: Difficult to grant granular access to components

## Decision Options

### Option 1: Keep Monorepo with Better Organization

Maintain single repository but improve tooling and structure.

**Pros:**
- Easy code sharing and refactoring across components
- Single source of truth for all code
- Simplified dependency version coordination
- Easy to enforce consistent coding standards
- Better for atomic cross-component changes

**Cons:**
- CI/CD complexity continues to grow
- Large repository size
- Difficult selective access control
- All-or-nothing cloning

**Tooling:**
- Use Nx, Turborepo, or Bazel for monorepo management
- Implement affected testing (only test changed components)
- Use sparse checkout for developers

### Option 2: Split into 3-4 Core Repositories

Separate concerns into logical repositories while maintaining some cohesion.

**Proposed Split:**

1. **codeflow-engine** (Core Python Package)
   - Python engine code
   - API server
   - Worker processes
   - Core tests
   - Python dependencies only

2. **codeflow-ui** (Frontend Applications)
   - Web dashboard (React)
   - VS Code extension
   - Desktop app (Electron)
   - Shared UI components
   - Frontend tests

3. **codeflow-infrastructure** (Deployment & Operations)
   - Kubernetes manifests
   - Terraform/Bicep configs
   - Docker configurations
   - Monitoring setups
   - Infrastructure as Code

4. **codeflow-templates** (Template Library)
   - Workflow templates
   - Platform-specific configs
   - Template documentation
   - Template tests

**Pros:**
- Clear separation of concerns
- Independent release cycles
- Focused CI/CD pipelines
- Smaller, faster clones
- Better team boundaries
- Granular access control

**Cons:**
- Cross-repo coordination needed
- Duplicate some tooling/configs
- More complex version management
- Breaking changes harder to coordinate
- Need robust versioning strategy

### Option 3: Full Microrepo (Many Small Repos)

Split into many small, focused repositories.

**Proposed Structure:**
- codeflow-engine-core
- codeflow-engine-api
- codeflow-engine-worker
- codeflow-ui-web
- codeflow-ui-vscode
- codeflow-desktop
- codeflow-infra-k8s
- codeflow-infra-terraform
- codeflow-templates

**Pros:**
- Maximum independence
- Clearest boundaries
- Finest-grained access control
- Smallest repositories

**Cons:**
- Coordination nightmare
- Versioning complexity
- Duplicated tooling everywhere
- Difficult cross-component refactoring
- High overhead for atomic changes

## Recommendation

**Choose Option 2**: Split into 3-4 core repositories for optimal balance between independence and coordination.

### Rationale

1. **Clear Boundaries**: The proposed split aligns with natural team and technology boundaries
2. **Manageable Complexity**: 3-4 repos is manageable without excessive coordination overhead
3. **Independent Deployments**: Core engine, UI, and infrastructure can deploy independently
4. **Reasonable Clone Times**: Each repo will be significantly smaller
5. **Focused CI/CD**: Each repo can have optimized pipelines for its technology
6. **Gradual Migration**: Can split incrementally, starting with highest-value separations

## Implementation Plan

### Phase 1: Preparation (Weeks 1-2)

1. **Audit Dependencies**: Map all inter-component dependencies
2. **Design Interfaces**: Define stable APIs between components
3. **Version Strategy**: Establish versioning scheme (semantic versioning + matrix)
4. **CI/CD Planning**: Design independent CI/CD pipelines
5. **Migration Scripts**: Prepare git history preservation scripts

### Phase 2: Core Engine Split (Weeks 3-4)

1. Extract `codeflow_engine/` to new `codeflow-engine` repository
2. Keep git history intact (use `git filter-repo`)
3. Set up independent CI/CD
4. Publish to PyPI from new repo
5. Update documentation

### Phase 3: UI Split (Weeks 5-6)

1. Extract frontend code to `codeflow-ui` repository
2. Consolidate UI components and shared libraries
3. Set up Node.js/TypeScript CI/CD
4. Establish npm publishing workflow
5. Update integration points

### Phase 4: Infrastructure Split (Weeks 7-8)

1. Extract infrastructure code to `codeflow-infrastructure` repository
2. Set up GitOps workflows
3. Establish environment management
4. Document deployment processes
5. Update runbooks

### Phase 5: Templates Split (Weeks 9-10)

1. Extract templates to `codeflow-templates` repository
2. Set up template validation pipeline
3. Establish template versioning
4. Create template marketplace
5. Document contribution guidelines

### Phase 6: Stabilization (Weeks 11-12)

1. Cross-repo integration testing
2. Documentation updates
3. Developer onboarding guides
4. Automated cross-repo tools
5. Monitoring and alerting setup

## Inter-Repository Coordination

### Version Matrix

Maintain compatibility matrix across repositories:

```yaml
# codeflow-engine v1.2.0 compatibility
compatible_ui_versions: "^2.1.0"
compatible_templates: "^1.0.0"
minimum_infra_version: "1.3.0"
```

### Shared Tooling

Maintain shared configurations in a `codeflow-shared` repository:
- Linting configs (ESLint, Ruff, Prettier)
- GitHub Actions workflows (reusable)
- Development environment configs
- Code generation templates

### Communication

1. **Cross-Repo Issues**: Use GitHub Projects to track cross-repo work
2. **Breaking Changes**: RFC process for changes affecting multiple repos
3. **Release Coordination**: Coordinated release schedule published quarterly
4. **Dependencies**: Renovate bot for automated dependency updates

## Success Metrics

- Build time reduction: Target 50% faster builds per repo
- Clone time: Under 2 minutes for any single repo
- Test execution: Under 10 minutes for affected tests
- Release frequency: Each component can release independently
- Developer onboarding: New developers can work on single component without full codebase

## Consequences

### Positive

- **Faster Development**: Focused repos mean faster builds and tests
- **Clear Ownership**: Each repo has clear team ownership
- **Independent Releases**: Components can evolve at their own pace
- **Better Security**: Granular access control per component
- **Reduced Conflicts**: Fewer merge conflicts with smaller teams per repo
- **Optimized Tooling**: Each repo can use best tools for its tech stack

### Negative

- **Coordination Overhead**: Cross-repo changes require more planning
- **Duplicated Config**: Some configs will be duplicated across repos
- **Version Management**: Need to track compatible versions across repos
- **Onboarding Complexity**: New developers need to understand multi-repo structure
- **Migration Effort**: Significant work to split and test the separation

### Mitigations

- Use monorepo tools temporarily to ease transition
- Establish clear inter-repo contracts and APIs
- Automate cross-repo testing with integration test suite
- Create comprehensive migration and onboarding documentation
- Use shared configuration repository for common tooling

## Alternative Considered

### Hybrid: Monorepo with Workspace Isolation

Use tools like Nx or Turborepo to get multi-repo benefits while keeping monorepo:

```
codeflow-engine/
├── packages/
│   ├── core/           # Python package
│   ├── web/            # React app
│   ├── vscode/         # VS Code extension
│   └── desktop/        # Electron app
├── nx.json
└── workspace.json
```

**Decision**: Not chosen because it doesn't solve clone size, access control, or technology heterogeneity issues.

## Timeline

- **Q1 2026**: Complete evaluation and decision
- **Q2 2026**: Execute split (Phases 1-6)
- **Q3 2026**: Stabilization and optimization
- **Q4 2026**: Evaluate and iterate

## Related Decisions

- [ADR-0019: Python-Only Architecture](0019-python-only-architecture.md)
- [ADR-0020: Package Naming Convention](0020-package-naming.md)
- [ADR-0012: Deployment Strategy](0012-deployment-strategy.md)
- [ADR-0015: Testing Strategy](0015-testing-strategy.md)

## References

- Monorepo vs Multi-Repo: https://monorepo.tools/
- Google's Monorepo Experience: https://cacm.acm.org/magazines/2016/7/204032-why-google-stores-billions-of-lines-of-code-in-a-single-repository/
- Git Filter-Repo: https://github.com/newren/git-filter-repo
- Nx Monorepo Tools: https://nx.dev/
