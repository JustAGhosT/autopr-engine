# Enhanced Error Handler Guide

## Overview

The Enhanced Error Handler system provides comprehensive error tracking, categorization, and display
capabilities for the AI Linting Fixer. It integrates seamlessly with the existing display system and
provides intelligent error recovery strategies.

## Key Features

- **Error Categorization**: Automatically categorizes errors into meaningful types
- **Severity Assessment**: Determines error severity based on type and context
- **Recovery Strategies**: Provides intelligent recovery suggestions
- **Error History**: Tracks all errors for analysis and debugging
- **Export Capabilities**: Export error reports for further analysis
- **Integration**: Works with existing display system

## Quick Start

### Basic Usage

```python
from autopr.actions.ai_linting_fixer import (
    ErrorHandler,
    create_error_context,
    DisplayConfig,
    OutputMode
)

# Set up error handler
display_config = DisplayConfig(mode=OutputMode.VERBOSE)
error_handler = ErrorHandler(display_config)

# Log an error with context
try:
    # Your code here
    raise FileNotFoundError("config.json not found")
except Exception as e:
    context = create_error_context(
        file_path="config.json",
        function_name="load_config",
        workflow_step="initialization"
    )
    error_info = error_handler.log_error(e, context)
```

### Integration with AI Linting Fixer

```python
from autopr.actions.ai_linting_fixer import AILintingFixer, ErrorHandler
from autopr.actions.llm.manager import LLMProviderManager

# Initialize components
llm_manager = LLMProviderManager()
error_handler = ErrorHandler()
fixer = AILintingFixer(llm_manager=llm_manager)

# Use with error handling
try:
    result = fixer.fix_issues_with_ai(issues, max_fixes=10)
except Exception as e:
    context = create_error_context(
        workflow_step="ai_fixing",
        provider="openai"
    )
    error_info = error_handler.log_error(e, context)

    # Attempt recovery
    if error_handler.attempt_recovery(error_info):
        print("Recovery attempt initiated...")
```

## Error Categories

The system automatically categorizes errors into the following types:

### File System Errors

- `FILE_NOT_FOUND`: File or directory not found
- `PERMISSION_DENIED`: Access permission issues
- `DISK_SPACE`: Insufficient disk space

### Network/API Errors

- `API_TIMEOUT`: API request timeouts
- `API_RATE_LIMIT`: Rate limiting issues
- `NETWORK_ERROR`: Network connectivity problems
- `AUTHENTICATION_ERROR`: Authentication failures

### Code Analysis Errors

- `SYNTAX_ERROR`: Code syntax issues
- `PARSING_ERROR`: Code parsing problems
- `LINTING_ERROR`: Linting tool errors

### AI/LLM Errors

- `AI_MODEL_ERROR`: AI model issues
- `AI_RESPONSE_ERROR`: AI response problems
- `AI_CONFIDENCE_LOW`: Low AI confidence

### System Errors

- `MEMORY_ERROR`: Memory issues
- `TIMEOUT_ERROR`: General timeout errors
- `CONFIGURATION_ERROR`: Configuration problems

### Workflow Errors

- `WORKFLOW_ERROR`: Workflow execution issues
- `ORCHESTRATION_ERROR`: Orchestration problems

## Error Severity Levels

- **LOW**: Minor issues that don't affect functionality
- **MEDIUM**: Issues that may affect performance or user experience
- **HIGH**: Issues that affect functionality but are recoverable
- **CRITICAL**: Issues that prevent operation or cause data loss

## Recovery Strategies

The system provides intelligent recovery strategies:

- **RETRY**: Automatically retry the operation
- **SKIP**: Skip the problematic item and continue
- **FALLBACK**: Use alternative method or configuration
- **ABORT**: Stop execution immediately
- **MANUAL_INTERVENTION**: Require human intervention

## Advanced Features

### Custom Error Callbacks

```python
def on_error_callback(error_info):
    """Custom callback for error events."""
    print(f"Error occurred: {error_info.error_type}")
    # Send notification, log to external system, etc.

def on_recovery_callback(error_info, strategy):
    """Custom callback for recovery attempts."""
    print(f"Attempting recovery: {strategy.value}")

error_handler.register_error_callback(on_error_callback)
error_handler.register_recovery_callback(on_recovery_callback)
```

### Error Context

Provide rich context for better error analysis:

```python
context = create_error_context(
    file_path="src/main.py",
    line_number=42,
    function_name="process_data",
    workflow_step="data_processing",
    session_id="session_123",
    user_action="batch_processing",
    memory_usage=1024,
    cpu_usage=75
)
```

### Error Summary and Export

```python
# Get error summary
summary = error_handler.get_error_summary()
print(f"Total errors: {summary['total_errors']}")
print(f"Error breakdown: {summary['error_counts_by_category']}")

# Export to file
error_handler.export_errors("error_report.json")
```

### Error History

```python
# Get all logged errors
history = error_handler.error_display.get_error_history()

# Clear history
error_handler.clear_errors()
```

## Display Integration

The error handler integrates with the existing display system:

```python
# Enhanced error display
error_handler.error_display.show_error_summary(
    error_counts={"file_not_found": 2, "permission_denied": 1},
    total_errors=3
)

error_handler.error_display.show_suggested_actions([
    "Check file permissions",
    "Verify file paths",
    "Ensure sufficient disk space"
])
```

## Configuration Options

### Display Configuration

```python
display_config = DisplayConfig(
    mode=OutputMode.VERBOSE,  # QUIET, NORMAL, VERBOSE, DEBUG
    use_colors=True,
    use_emojis=True,
    line_width=80
)
```

### Error Handler Configuration

```python
error_handler = ErrorHandler(display_config)

# Customize recovery strategies
error_handler.recovery_strategies[ErrorCategory.API_TIMEOUT] = ErrorRecoveryStrategy.RETRY
error_handler.recovery_strategies[ErrorCategory.FILE_NOT_FOUND] = ErrorRecoveryStrategy.SKIP
```

## Best Practices

### 1. Provide Rich Context

Always provide meaningful context when logging errors:

```python
context = create_error_context(
    file_path=file_path,
    function_name=function_name,
    workflow_step=current_step,
    session_id=session_id
)
```

### 2. Use Appropriate Error Categories

The system automatically categorizes errors, but you can provide hints:

```python
# The system will detect this as a file not found error
raise FileNotFoundError("config.json not found")
```

### 3. Handle Recovery Gracefully

```python
if error_handler.attempt_recovery(error_info):
    # Implement retry logic
    time.sleep(1)  # Wait before retry
    # Retry the operation
else:
    # Handle non-recoverable errors
    print("Cannot recover from this error")
```

### 4. Export Error Reports

Regularly export error reports for analysis:

```python
# Export after processing
error_handler.export_errors(f"errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
```

### 5. Monitor Error Patterns

Use error summaries to identify patterns:

```python
summary = error_handler.get_error_summary()
if summary['error_counts_by_category'].get('api_timeout', 0) > 5:
    print("Too many API timeouts - check network connectivity")
```

## Examples

### Complete Integration Example

See `examples/error_handler_usage.py` for a complete example showing:

- Error handler setup and configuration
- Integration with AI linting fixer
- Error categorization demonstration
- Recovery strategy testing
- Error reporting and export

### Test File Example

See `test_lint_issues.py` for a demonstration of the error handler system with various error types.

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the project root directory
2. **Display Issues**: Check display configuration and terminal capabilities
3. **Recovery Failures**: Verify recovery strategies are appropriate for error types

### Debug Mode

Enable debug mode for detailed error information:

```python
display_config = DisplayConfig(mode=OutputMode.DEBUG)
error_handler = ErrorHandler(display_config)
```

### Error Report Analysis

Exported error reports contain:

- Error details and context
- Categorization and severity
- Recovery attempts
- Suggested actions
- Timestamps and session information

## API Reference

### ErrorHandler Class

- `log_error(exception, context, additional_info, display)`: Log an error
- `attempt_recovery(error_info)`: Attempt error recovery
- `get_error_summary()`: Get error statistics
- `export_errors(file_path)`: Export error report
- `clear_errors()`: Clear error history

### ErrorInfo Class

- `error_id`: Unique error identifier
- `error_type`: Type of exception
- `error_message`: Error message
- `severity`: Error severity level
- `category`: Error category
- `context`: Error context information
- `suggested_action`: Suggested resolution

### ErrorContext Class

- `file_path`: Related file path
- `line_number`: Related line number
- `function_name`: Function where error occurred
- `workflow_step`: Current workflow step
- `session_id`: Session identifier
- `system_state`: Additional system state

## Contributing

When adding new error categories or recovery strategies:

1. Add new category to `ErrorCategory` enum
2. Update `categorize_error()` method
3. Add severity mapping in `determine_severity()`
4. Add suggested action in `get_suggested_action()`
5. Update recovery strategies if needed
6. Add tests for new functionality
