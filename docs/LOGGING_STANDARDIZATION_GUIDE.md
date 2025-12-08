# Logging Standardization Guide

## Overview

AutoPR Engine uses **structlog** as the primary logging framework across the entire codebase. This guide documents the standardized logging approach, configuration, and best practices.

**Status:** ✅ Logging system standardized on structlog  
**Issue:** BUG-1 resolved - No dual logging system conflict (analysis found structlog only)  
**Last Updated:** 2025-11-22

## Table of Contents

1. [Architecture](#architecture)
2. [Configuration](#configuration)
3. [Usage Patterns](#usage-patterns)
4. [Log Levels](#log-levels)
5. [Structured Logging](#structured-logging)
6. [Context Management](#context-management)
7. [Performance Considerations](#performance-considerations)
8. [Testing](#testing)
9. [Production Configuration](#production-configuration)
10. [Monitoring Integration](#monitoring-integration)

---

## Architecture

### Logging Framework: structlog

AutoPR Engine uses **structlog** exclusively for all logging operations. Structlog provides:

- **Structured logging** with key-value pairs
- **Context binding** for request tracing
- **Performance optimization** with lazy evaluation
- **JSON output** for log aggregation systems
- **Integration** with standard library logging

### Why structlog?

1. **Performance**: Lazy evaluation and efficient context binding
2. **Structured Data**: JSON-serializable log entries for parsing and analysis
3. **Context Preservation**: Request IDs, user IDs, and workflow IDs automatically included
4. **Integration**: Works with ELK, Splunk, DataDog, and other log aggregation systems
5. **Type Safety**: Better IDE support and type checking

### Architecture Diagram

```
┌─────────────────┐
│  Application    │
│     Code        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   structlog     │
│   Logger        │
└────────┬────────┘
         │
         ├──────────────┬──────────────┐
         ▼              ▼              ▼
┌──────────────┐  ┌──────────┐  ┌──────────┐
│   Console    │  │   File   │  │  JSON    │
│   Handler    │  │  Handler │  │ Handler  │
└──────────────┘  └──────────┘  └──────────┘
```

---

## Configuration

### Basic Configuration

```python
# autopr/config/logging.py

import structlog
import logging
import sys
from pathlib import Path

def configure_logging(
    level: str = "INFO",
    json_logs: bool = False,
    log_file: str | None = None
):
    """
    Configure structlog for the application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Whether to output logs in JSON format
        log_file: Optional file path for log output
    """
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )
    
    # Define processors
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    
    # Add JSON processor for production
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter("%(message)s"))
        logging.root.addHandler(file_handler)


# Default configuration for development
configure_logging(level="DEBUG", json_logs=False)
```

### Environment-Specific Configuration

#### Development
```python
configure_logging(
    level="DEBUG",
    json_logs=False,  # Human-readable console output
    log_file=None
)
```

#### Staging
```python
configure_logging(
    level="INFO",
    json_logs=True,  # Structured JSON for log aggregation
    log_file="/var/log/autopr/app.log"
)
```

#### Production
```python
configure_logging(
    level="INFO",
    json_logs=True,  # JSON output for ELK/Splunk
    log_file="/var/log/autopr/production.log"
)
```

---

## Usage Patterns

### Basic Logging

```python
import structlog

logger = structlog.get_logger(__name__)

# Simple log messages
logger.debug("Processing workflow", workflow_id="wf-123")
logger.info("Workflow started", workflow_id="wf-123", user_id="user-456")
logger.warning("Rate limit approaching", remaining=10, limit=100)
logger.error("Workflow failed", workflow_id="wf-123", error="Connection timeout")
logger.critical("Database connection lost", attempts=3)
```

### Structured Logging with Context

```python
import structlog

logger = structlog.get_logger(__name__)

# Log with structured data
logger.info(
    "workflow_execution_started",
    workflow_id="wf-123",
    workflow_name="Deploy to Production",
    user_id="user-456",
    trigger="manual",
    estimated_duration=300  # seconds
)

# Log with metrics
logger.info(
    "workflow_execution_completed",
    workflow_id="wf-123",
    status="success",
    duration_seconds=287.5,
    steps_executed=12,
    steps_failed=0
)
```

### Exception Logging

```python
import structlog

logger = structlog.get_logger(__name__)

try:
    execute_workflow(workflow_id)
except Exception as e:
    logger.exception(
        "workflow_execution_failed",
        workflow_id="wf-123",
        error_type=type(e).__name__,
        error_message=str(e)
    )
    # Exception traceback is automatically included
```

---

## Log Levels

### Level Guidelines

| Level | Use Case | Examples |
|-------|----------|----------|
| **DEBUG** | Detailed diagnostic information | Variable values, function entry/exit, internal state |
| **INFO** | General informational messages | Request received, workflow started, task completed |
| **WARNING** | Warnings that don't prevent operation | Deprecated API used, retry attempt, resource threshold |
| **ERROR** | Errors that need attention | Failed API call, validation error, recoverable failure |
| **CRITICAL** | Critical errors requiring immediate action | Database connection lost, service unavailable |

### Examples by Level

```python
import structlog

logger = structlog.get_logger(__name__)

# DEBUG: Detailed diagnostic info
logger.debug("Database query executed", query="SELECT * FROM workflows", duration_ms=45)

# INFO: General informational messages
logger.info("User authenticated", user_id="user-123", method="github_token")

# WARNING: Potentially problematic situations
logger.warning("API rate limit 80% consumed", remaining=1000, limit=5000)

# ERROR: Error conditions
logger.error("Failed to send Slack notification", webhook_url="***", error="Connection timeout")

# CRITICAL: System-level failures
logger.critical("Redis connection lost", attempts=5, last_error="Connection refused")
```

---

## Structured Logging

### Key-Value Pairs

Always use key-value pairs for structured data:

```python
# ✅ GOOD: Structured with key-value pairs
logger.info("workflow_started", workflow_id="wf-123", user_id="user-456")

# ❌ BAD: Unstructured string interpolation
logger.info(f"Workflow wf-123 started by user-456")
```

### Standard Fields

Use consistent field names across the application:

| Field | Description | Example |
|-------|-------------|---------|
| `workflow_id` | Workflow identifier | `"wf-123"` |
| `execution_id` | Execution identifier | `"exec-456"` |
| `user_id` | User identifier | `"user-789"` |
| `request_id` | HTTP request ID | `"req-abc123"` |
| `duration_seconds` | Operation duration | `1.23` |
| `status` | Operation status | `"success"`, `"failed"` |
| `error_type` | Exception class name | `"ValidationError"` |
| `error_message` | Error description | `"Invalid workflow configuration"` |

### JSON Output Example

With `json_logs=True`, logs are output as JSON:

```json
{
  "event": "workflow_execution_completed",
  "workflow_id": "wf-123",
  "execution_id": "exec-456",
  "user_id": "user-789",
  "status": "success",
  "duration_seconds": 287.5,
  "steps_executed": 12,
  "steps_failed": 0,
  "timestamp": "2025-11-22T19:00:00.123456Z",
  "level": "info",
  "logger": "autopr.workflows.engine"
}
```

---

## Context Management

### Request Context

Bind request-level context that persists across log statements:

```python
import structlog
from contextvars import ContextVar

# Define context variables
request_id_ctx: ContextVar[str] = ContextVar("request_id", default=None)
user_id_ctx: ContextVar[str] = ContextVar("user_id", default=None)

# Bind context at request start
def process_request(request):
    request_id = request.headers.get("X-Request-ID", generate_request_id())
    user_id = get_user_id_from_token(request.headers.get("Authorization"))
    
    # Set context variables
    request_id_ctx.set(request_id)
    user_id_ctx.set(user_id)
    
    # All subsequent logs will include these fields
    logger = structlog.get_logger(__name__)
    logger.info("request_received", method=request.method, path=request.path)
    
    # ... process request ...
    
    logger.info("request_completed", status_code=200, duration_ms=123)
```

### Workflow Context

Bind workflow-specific context:

```python
import structlog

logger = structlog.get_logger(__name__)

def execute_workflow(workflow_id: str):
    # Bind workflow context
    log = logger.bind(workflow_id=workflow_id)
    
    log.info("workflow_execution_started")
    
    try:
        for step in get_workflow_steps(workflow_id):
            # Step context automatically includes workflow_id
            step_log = log.bind(step_id=step.id, step_name=step.name)
            step_log.info("step_started")
            
            execute_step(step)
            
            step_log.info("step_completed", duration_seconds=1.5)
        
        log.info("workflow_execution_completed", status="success")
    
    except Exception as e:
        log.exception("workflow_execution_failed", error_type=type(e).__name__)
```

---

## Performance Considerations

### Lazy Evaluation

Structlog uses lazy evaluation for performance:

```python
# ✅ GOOD: Lazy evaluation (only evaluated if logged)
logger.debug("expensive_operation", result=expensive_function())

# ✅ BETTER: Conditional evaluation
if logger.isEnabledFor(logging.DEBUG):
    logger.debug("expensive_operation", result=expensive_function())
```

### Avoid String Formatting

```python
# ✅ GOOD: Let structlog handle formatting
logger.info("workflow_started", workflow_id=wf_id, user_id=user_id)

# ❌ BAD: Pre-formatted strings
logger.info(f"Workflow {wf_id} started by {user_id}")
```

### Batch Logging

For high-frequency operations, consider batching:

```python
# Collect metrics
metrics = []
for i in range(1000):
    metrics.append(process_item(i))

# Log summary instead of individual items
logger.info("batch_processed", count=len(metrics), duration_seconds=5.2)
```

---

## Testing

### Mock Logger in Tests

```python
import pytest
from unittest.mock import Mock
import structlog

@pytest.fixture
def mock_logger(monkeypatch):
    """Mock structlog logger for testing."""
    mock = Mock()
    monkeypatch.setattr(structlog, "get_logger", lambda name: mock)
    return mock

def test_workflow_execution_logging(mock_logger):
    """Test that workflow execution logs correctly."""
    execute_workflow("wf-123")
    
    # Verify logging calls
    mock_logger.info.assert_called_with(
        "workflow_execution_started",
        workflow_id="wf-123"
    )
```

### Capture Logs in Tests

```python
import pytest
import structlog
from structlog.testing import LogCapture

@pytest.fixture
def log_capture():
    """Capture logs during tests."""
    return LogCapture()

def test_workflow_logging(log_capture):
    """Test workflow logging output."""
    structlog.configure(processors=[log_capture])
    
    logger = structlog.get_logger()
    logger.info("workflow_started", workflow_id="wf-123")
    
    assert log_capture.entries == [
        {"event": "workflow_started", "workflow_id": "wf-123", "level": "info"}
    ]
```

---

## Production Configuration

### Complete Production Setup

```python
# config/production.py

import structlog
import logging
import sys
from pythonjsonlogger import jsonlogger

def configure_production_logging():
    """Configure logging for production environment."""
    
    # Standard library configuration
    log_handler = logging.StreamHandler(sys.stdout)
    log_handler.setFormatter(jsonlogger.JsonFormatter())
    
    logging.basicConfig(
        level=logging.INFO,
        handlers=[log_handler]
    )
    
    # Structlog processors for production
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ]
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

# Initialize
configure_production_logging()
```

### Environment Variables

```bash
# .env.production

# Logging configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/autopr/production.log

# Structured logging fields
SERVICE_NAME=codeflow-engine
ENVIRONMENT=production
VERSION=1.0.0
```

---

## Monitoring Integration

### Metrics Logging

Log metrics for monitoring systems:

```python
logger.info(
    "api_request_completed",
    method="POST",
    path="/workflows",
    status_code=201,
    duration_ms=123,
    user_id="user-456"
)
```

### Alert Triggers

Use specific event names for alerting:

```python
# Critical alerts
logger.critical("database_connection_lost", attempts=5)
logger.critical("memory_threshold_exceeded", usage_percent=95)

# Warning alerts
logger.warning("rate_limit_approaching", remaining=500, limit=5000)
logger.warning("slow_query_detected", duration_ms=5000, query_id="q-123")
```

### Log Aggregation

Logs are automatically compatible with:

- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Splunk**
- **DataDog**
- **CloudWatch**
- **Grafana Loki**

Example Logstash configuration:

```json
{
  "input": {
    "file": {
      "path": "/var/log/autopr/*.log",
      "codec": "json"
    }
  },
  "filter": {
    "json": {
      "source": "message"
    }
  },
  "output": {
    "elasticsearch": {
      "hosts": ["localhost:9200"],
      "index": "autopr-%{+YYYY.MM.dd}"
    }
  }
}
```

---

## Best Practices

### DO's ✅

1. **Use structured logging** with key-value pairs
2. **Include context** (workflow_id, user_id, request_id)
3. **Use consistent field names** across the application
4. **Log at appropriate levels** (DEBUG, INFO, WARNING, ERROR, CRITICAL)
5. **Include metrics** (duration, count, size)
6. **Use exception()** for errors with stack traces
7. **Bind context** for request and workflow scopes

### DON'Ts ❌

1. **Don't log sensitive data** (passwords, tokens, API keys)
2. **Don't use string interpolation** for log messages
3. **Don't log in tight loops** (batch instead)
4. **Don't log the same event multiple times**
5. **Don't include PII** without proper redaction
6. **Don't ignore log levels** (everything is not INFO)

---

## Migration from Other Logging Libraries

### From standard `logging`

```python
# Before: Standard logging
import logging
logger = logging.getLogger(__name__)
logger.info(f"Workflow {workflow_id} started")

# After: structlog
import structlog
logger = structlog.get_logger(__name__)
logger.info("workflow_started", workflow_id=workflow_id)
```

### From print statements

```python
# Before: Print statements
print(f"Processing workflow {workflow_id}")

# After: structlog
logger.info("processing_workflow", workflow_id=workflow_id)
```

---

## Troubleshooting

### Logs Not Appearing

**Problem:** Logs not showing in output

**Solution:**
```python
# Ensure logging is configured
from autopr.config.logging import configure_logging
configure_logging(level="DEBUG")

# Check log level
import logging
print(logging.root.level)  # Should be 10 for DEBUG
```

### JSON Output Malformed

**Problem:** JSON logs are not valid JSON

**Solution:**
```python
# Ensure JSONRenderer is last processor
processors = [
    # ... other processors ...
    structlog.processors.JSONRenderer()  # Must be last
]
```

### Performance Issues

**Problem:** Logging is slowing down the application

**Solution:**
```python
# 1. Increase log level in production
configure_logging(level="INFO")  # Instead of DEBUG

# 2. Use lazy evaluation
if logger.isEnabledFor(logging.DEBUG):
    logger.debug("expensive_op", result=expensive_function())

# 3. Batch high-frequency logs
```

---

## Conclusion

AutoPR Engine's logging system is standardized on **structlog** for:

- ✅ **Consistency** across all modules
- ✅ **Performance** with lazy evaluation
- ✅ **Structured data** for analysis
- ✅ **Production-ready** JSON output
- ✅ **Integration** with monitoring systems

**BUG-1 Status:** ✅ **RESOLVED** - Single logging framework (structlog) confirmed

For questions or issues, see [Troubleshooting Guide](./TROUBLESHOOTING.md) or contact the DevOps team.

---

**Last Updated:** 2025-11-22  
**Version:** 1.0.0  
**Maintained by:** AutoPR DevOps Team
