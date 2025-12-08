# 1. Hybrid C#/Python Architecture

## Status

**Superseded by [ADR-0019: Python-Only Architecture](0019-python-only-architecture.md)**

This ADR was originally proposed but never implemented. The project was successfully built using Python-only architecture. See ADR-0019 for the actual implementation and rationale.

## Context

AutoPR requires both high-performance code execution and advanced AI/ML capabilities. We need to
balance performance, development velocity, and maintainability while leveraging the strengths of
different technologies.

## Decision

We will implement a hybrid architecture using:

- **C# (.NET 6+)** for core infrastructure, performance-critical paths, and system integration
- **Python 3.10+** for AI/ML components and data processing
- **gRPC** for efficient communication between C# and Python components
- **React/TypeScript** for the web UI

## Consequences

### Positive

- **Performance**: C# provides better raw performance for CPU-bound operations
- **AI Capabilities**: Full access to Python's rich AI/ML ecosystem
- **Type Safety**: Strong typing in both C# and Python (with type hints)
- **Scalability**: Components can be scaled independently
- **Developer Experience**: Clear separation of concerns

### Negative

- **Complexity**: Additional complexity in managing two codebases
- **Interop Overhead**: gRPC communication adds some latency
- **Build/Deploy**: More complex build and deployment pipelines
- **Learning Curve**: Developers need to be proficient in both languages

### Neutral

- **Team Structure**: May require cross-functional teams or clear component ownership
- **Tooling**: Need to support both .NET and Python development environments

## Migration Strategy

1. **Phase 1**: Stabilize current Python implementation
2. **Phase 2**: Port performance-critical components to C#
3. **Phase 3**: Implement gRPC communication layer
4. **Phase 4**: Gradual migration of components following clear interfaces

## Related Decisions

- [ADR-0002: gRPC for Cross-Language Communication](0002-grpc-communication.md)
- [ADR-0003: Plugin System Architecture](0003-plugin-system.md)
