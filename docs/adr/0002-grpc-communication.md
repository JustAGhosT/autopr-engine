# 2. gRPC for Cross-Language Communication

## Status

**Deprecated** (Related to ADR-0001 which was superseded)

This ADR was proposed for cross-language communication in a hybrid C#/Python architecture, but was never implemented. The project uses Python-only architecture (see [ADR-0019](0019-python-only-architecture.md)), eliminating the need for cross-language communication.

Kept for historical reference.

## Context

We need efficient, type-safe communication between C# and Python components in our hybrid
architecture. The solution should provide:

- Low latency
- Strong typing
- Cross-language compatibility
- Good performance for both small and large payloads

## Decision

We will use **gRPC** as the primary communication protocol between C# and Python components.

### Implementation Details:

- **Protocol Buffers (protobuf)** for interface definition
- **gRPC** for high-performance RPC
- **HTTP/2** for transport
- **Code generation** for type-safe client/server stubs

## Consequences

### Positive

- **Performance**: HTTP/2 multiplexing and binary protocol
- **Type Safety**: Compile-time type checking
- **Language Neutral**: Works well with both C# and Python
- **Streaming Support**: Bidirectional streaming capabilities
- **Code Generation**: Reduces boilerplate code

### Negative

- **Learning Curve**: Developers need to understand protobuf and gRPC concepts
- **Tooling**: Additional tooling required for code generation
- **Debugging**: More complex than REST for simple use cases

### Neutral

- **Deployment**: Requires gRPC runtime in production
- **Documentation**: Need to maintain .proto files and generated code

## Related Decisions

- [ADR-0001: Hybrid C#/Python Architecture](0001-hybrid-csharp-python-architecture.md)
- [ADR-0004: API Versioning Strategy](0004-api-versioning.md)
