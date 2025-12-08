# 19. Python-Only Architecture Decision

## Status

Accepted (Supersedes ADR-0001)

## Context

While ADR-0001 proposed a hybrid C#/Python architecture, the project has been successfully implemented using Python exclusively. This decision reflects the actual implementation and provides clarity on the technology stack in use.

## Decision

We will use a **Python-only architecture** for the entire codeflow-engine project with the following stack:

- **Python 3.12+** for all application code
- **FastAPI** for REST API and server components
- **Flask-SocketIO** for real-time WebSocket communication
- **PostgreSQL** with SQLAlchemy and Alembic for data persistence
- **Redis** for caching and queue management
- **Poetry** for dependency management
- **Docker** for containerization and deployment

### Key Technologies

#### Core Framework
- Python 3.12+ with type hints for type safety
- Pydantic v2 for data validation and settings management
- Structlog for structured JSON logging

#### AI/ML Stack
- OpenAI GPT models (GPT-4, GPT-3.5)
- Anthropic Claude models
- Mistral AI and Groq for alternative providers
- AutoGen for multi-agent orchestration

#### Integrations
- PyGithub for GitHub API
- GitPython for Git operations
- aiohttp for async HTTP requests
- websockets for real-time communication

#### Database & Persistence
- PostgreSQL (via psycopg2-binary)
- SQLAlchemy for ORM
- Alembic for migrations
- Redis for caching

#### Observability
- OpenTelemetry SDK for distributed tracing
- Prometheus metrics (via prometheus-client)
- Sentry for error tracking
- DataDog for monitoring

## Rationale

### Why Python-Only vs Hybrid C#/Python

1. **Simpler Architecture**: Single language reduces complexity, improves maintainability
2. **Faster Development**: No cross-language communication overhead
3. **Rich Ecosystem**: Python's AI/ML ecosystem is comprehensive
4. **Performance**: Modern async Python (asyncio, aiohttp) provides sufficient performance
5. **Team Efficiency**: Single technology stack reduces onboarding complexity
6. **Deployment**: Simpler container images and fewer runtime dependencies

### Performance Considerations

While C# offers better raw performance, Python's async capabilities combined with:
- Efficient use of async/await patterns
- Connection pooling for database and HTTP
- Redis for hot-path caching
- Worker processes for CPU-intensive tasks

...provide adequate performance for our use case.

## Consequences

### Positive

- **Simplified Architecture**: Single codebase, single deployment pipeline
- **Faster Iteration**: No gRPC communication layer needed
- **Better Type Safety**: Python 3.12+ with Pydantic v2 provides strong typing
- **Rich AI Ecosystem**: Direct access to all Python AI/ML libraries
- **Easier Testing**: Single language testing framework
- **Lower Maintenance**: Fewer moving parts, simpler debugging

### Negative

- **CPU Performance**: Lower raw CPU performance compared to C#
- **Memory Usage**: Python's memory footprint is higher
- **GIL Limitations**: Global Interpreter Lock affects multi-threaded CPU work
- **Startup Time**: Slower cold starts compared to compiled languages

### Mitigations

- Use async I/O extensively to avoid GIL bottlenecks
- Leverage Redis for caching to reduce CPU load
- Scale horizontally with multiple worker processes
- Use PyPy or Cython for performance-critical sections if needed

## Migration Summary from Proposed Architecture

### What Changed from ADR-0001

| Proposed (ADR-0001) | Actual Implementation | Rationale |
|---------------------|----------------------|-----------|
| C# + Python hybrid | Python-only | Simpler, faster development |
| gRPC communication | Direct Python calls | No cross-language overhead |
| .NET 6+ for core | FastAPI + Flask | Python web frameworks sufficient |
| Separate C# service | Monolithic Python app | Easier deployment and debugging |

### Migration Path (If Needed)

If performance becomes a critical issue, migration options include:

1. **Gradual Optimization**:
   - Profile to identify bottlenecks
   - Optimize hot paths with Cython or PyPy
   - Add Redis caching strategically

2. **Selective Language Migration**:
   - Migrate only performance-critical components to Rust or Go
   - Use FFI (Foreign Function Interface) for integration
   - Keep main application in Python

3. **Full Microservices**:
   - Extract high-throughput services to separate microservices
   - Use gRPC or REST for communication
   - Deploy performance-critical services in compiled languages

## Related Decisions

- [ADR-0002: gRPC Communication](0002-grpc-communication.md) - Not implemented, kept for reference
- [ADR-0005: Configuration Management](0005-configuration-management.md) - Implemented with Pydantic
- [ADR-0011: Data Persistence Strategy](0011-data-persistence-strategy.md) - Implemented with PostgreSQL
- [ADR-0020: Package Naming Convention](0020-package-naming.md) - codeflow_engine package name

## References

- Python 3.12 Release Notes: https://docs.python.org/3/whatsnew/3.12.html
- FastAPI Documentation: https://fastapi.tiangolo.com/
- Pydantic v2 Documentation: https://docs.pydantic.dev/
