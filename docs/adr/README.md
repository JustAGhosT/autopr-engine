# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) for the codeflow-engine project.

## What is an ADR?

An Architecture Decision Record (ADR) captures an important architectural decision made along with its context and consequences. ADRs help teams:

- Understand why decisions were made
- Track the evolution of the architecture
- Onboard new team members
- Revisit decisions when context changes

## ADR Format

Each ADR follows this structure:

- **Title**: Short, descriptive name
- **Status**: Proposed, Accepted, Deprecated, Superseded
- **Context**: What is the issue that we're seeing that is motivating this decision?
- **Decision**: What is the change that we're proposing and/or doing?
- **Consequences**: What becomes easier or more difficult to do because of this change?

## ADR Index

### Core Architecture

- [ADR-0001: Hybrid C#/Python Architecture](0001-hybrid-csharp-python-architecture.md) - **Status: Superseded by ADR-0019**
  - Originally proposed hybrid architecture (not implemented)
  
- [ADR-0019: Python-Only Architecture](0019-python-only-architecture.md) - **Status: Accepted** ⭐
  - **Supersedes ADR-0001**: Documents the actual Python-only implementation
  - Includes migration summary explaining why hybrid approach wasn't implemented
  
- [ADR-0021: Repository Structure and Monorepo vs Multi-Repo](0021-repository-structure.md) - **Status: Proposed**
  - Evaluates splitting the monorepo into 3-4 focused repositories
  - Includes detailed implementation plan and timeline

### Communication & Integration

- [ADR-0002: gRPC Communication](0002-grpc-communication.md) - **Status: Deprecated**
  - Originally proposed for C#/Python communication (not implemented)
  - Kept for historical reference
  
- [ADR-0003: Plugin System Architecture](0003-plugin-system-architecture.md) - **Status: Accepted**
  - Extensible plugin system for actions, integrations, and providers
  
- [ADR-0008: Event-Driven Architecture](0008-event-driven-architecture.md) - **Status: Accepted**
  - Asynchronous event processing for workflows

### API & Configuration

- [ADR-0004: API Versioning Strategy](0004-api-versioning-strategy.md) - **Status: Accepted**
  - Semantic versioning for APIs
  
- [ADR-0005: Configuration Management](0005-configuration-management.md) - **Status: Accepted**
  - YAML-based configuration with Pydantic validation
  
- [ADR-0006: Plugin System Design](0006-plugin-system-design.md) - **Status: Accepted**
  - Detailed plugin system implementation

### Security & Authentication

- [ADR-0007: Authentication & Authorization](0007-authn-authz.md) - **Status: Accepted**
  - JWT-based authentication with role-based access control
  
- [ADR-0013: Security Strategy](0013-security-strategy.md) - **Status: Accepted**
  - Comprehensive security measures and best practices

### Error Handling & Reliability

- [ADR-0009: Error Handling Strategy](0009-error-handling-strategy.md) - **Status: Accepted**
  - Structured error handling and recovery
  
- [ADR-0014: Caching Strategy](0014-caching-strategy.md) - **Status: Accepted**
  - Redis-based caching for performance

### Observability & Operations

- [ADR-0010: Monitoring & Observability](0010-monitoring-observability.md) - **Status: Accepted**
  - OpenTelemetry, Prometheus, and Sentry integration
  
- [ADR-0017: On-Call & Incident Response](0017-on-call-incident-response.md) - **Status: Accepted**
  - Incident management procedures

### Data & Deployment

- [ADR-0011: Data Persistence Strategy](0011-data-persistence-strategy.md) - **Status: Accepted**
  - PostgreSQL with SQLAlchemy and Alembic
  
- [ADR-0012: Deployment Strategy](0012-deployment-strategy.md) - **Status: Accepted**
  - Docker, Kubernetes, and CI/CD pipelines

### Quality & Documentation

- [ADR-0015: Testing Strategy](0015-testing-strategy.md) - **Status: Accepted**
  - Unit, integration, and end-to-end testing approach
  
- [ADR-0016: Documentation Strategy](0016-documentation-strategy.md) - **Status: Accepted**
  - Sphinx-based documentation with automated generation

### Business & Product

- [ADR-0018: AutoPR SaaS Consideration](0018-autopr-saas-consideration.md) - **Status: Accepted**
  - SaaS offering analysis and decision
  
- [ADR-0020: Package Naming Convention](0020-package-naming.md) - **Status: Accepted** ⭐
  - Documents the autopr → codeflow_engine rename
  - Includes migration guide and backward compatibility strategy

## Creating a New ADR

When creating a new ADR:

1. Copy the template from `docs/adr/template.md` (if it exists) or use the standard format
2. Number it sequentially (check the highest number and add 1)
3. Use the format: `NNNN-short-title.md` (e.g., `0022-my-decision.md`)
4. Include date and status at the top
5. Update this index with a link and brief description

## ADR Status Definitions

- **Proposed**: Under discussion, not yet decided
- **Accepted**: Decision has been made and implemented (or implementation in progress)
- **Deprecated**: No longer relevant, but kept for historical context
- **Superseded**: Replaced by a newer ADR (link to the superseding ADR)

## Key Decisions Summary

### Technology Stack (As Implemented)

The project uses a **Python-only architecture** (ADR-0019):
- Python 3.12+ with type hints and Pydantic v2
- FastAPI for REST API, Flask-SocketIO for WebSockets
- PostgreSQL + SQLAlchemy + Alembic for persistence
- Redis for caching and queuing
- OpenTelemetry, Prometheus, Sentry for observability

### Package Structure (ADR-0020)

- **Package Name**: `codeflow_engine` (Python package)
- **PyPI Distribution**: `codeflow-engine`
- **CLI Tools**: `autopr`, `autopr-server`, `autopr-worker` (backward compatible)
- **Config Files**: `autopr.yaml`, `autopr.yml` (backward compatible)

### Future Considerations

- **Repository Split** (ADR-0021): Evaluating split into 3-4 focused repos for better scalability
- **Performance Optimization**: If needed, selective migration of hot paths to Rust/Go
- **Microservices**: Potential extraction of high-throughput services

## References

- [ADR GitHub Org](https://adr.github.io/) - ADR tools and best practices
- [Michael Nygard's ADR Blog Post](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) - Original ADR concept
- [ADR Tools](https://github.com/npryce/adr-tools) - Command-line tools for managing ADRs
