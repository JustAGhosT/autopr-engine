"""
AutoPR Engine Exceptions

Custom exception classes for the AutoPR Engine with secure error handling
and information leakage prevention.

Security: All exceptions include sanitization methods to prevent exposing
sensitive information (API keys, database credentials, internal paths) to end users.
"""

import re
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


class AutoPRException(Exception):
    """
    Base exception class for all AutoPR Engine errors.
    
    Includes automatic sanitization to prevent information leakage.
    """

    def __init__(self, message: str, error_code: str | None = None, user_message: str | None = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self._user_message = user_message

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message
    
    def get_user_message(self) -> str:
        """
        Get sanitized error message safe for end users.
        
        Returns:
            Sanitized error message without sensitive information
            
        Security: Prevents leakage of:
            - Database connection strings
            - API keys and tokens
            - File paths
            - Stack traces
            - Email addresses
            - IP addresses
        """
        if self._user_message:
            return self._user_message
        
        # Use sanitization function
        return sanitize_error_message(self.message)
    
    def get_internal_message(self) -> str:
        """Get full internal message for logging (may contain sensitive data)."""
        return self.message


def sanitize_error_message(message: str) -> str:
    """
    Sanitize error message for end users.
    
    Removes sensitive information like:
    - Database connection strings
    - API keys and tokens
    - File paths
    - Email addresses
    - IP addresses
    - SQL queries
    
    Args:
        message: Error message to sanitize
        
    Returns:
        Sanitized error message safe for end users
        
    Example:
        >>> sanitize_error_message("Connection failed: postgresql://user:pass@localhost/db")
        "Connection failed: postgresql://[REDACTED]"
    """
    sanitized = message
    
    # Patterns to redact
    sensitive_patterns = [
        # Database connection strings
        (r'postgresql://[^\s]+', 'postgresql://[REDACTED]'),
        (r'mysql://[^\s]+', 'mysql://[REDACTED]'),
        (r'mongodb://[^\s]+', 'mongodb://[REDACTED]'),
        (r'sqlite:///[^\s]+', 'sqlite:///[REDACTED]'),
        
        # API keys and tokens
        # JWT tokens (base64url encoded strings with dots)
        (r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*', '[REDACTED]'),
        # JWT tokens without full structure (just the header/payload/signature parts)
        (r'eyJ[a-zA-Z0-9_-]+', '[REDACTED]'),
        (r'(api[_-]?key|token|secret|password)["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_\-\.]+', r'\1=[REDACTED]'),
        (r'ghp_[a-zA-Z0-9]+', 'ghp_[REDACTED]'),
        (r'sk-[a-zA-Z0-9]+', 'sk-[REDACTED]'),
        (r'Bearer\s+[a-zA-Z0-9\-\._~\+\/]+=*', 'Bearer [REDACTED]'),
        
        # File paths (Unix and Windows)
        (r'/[a-zA-Z0-9/_\-\.]+\.py', '[FILE_PATH]'),
        (r'[a-zA-Z]:\\[a-zA-Z0-9\\_\-\.]+', '[FILE_PATH]'),
        
        # Email addresses
        (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL_REDACTED]'),
        
        # IP addresses
        (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP_REDACTED]'),
        
        # SQL queries (often contain sensitive data)
        (r'SELECT .+ FROM', 'SELECT [QUERY_REDACTED] FROM'),
        (r'INSERT INTO .+ VALUES', 'INSERT INTO [QUERY_REDACTED] VALUES'),
        (r'UPDATE .+ SET', 'UPDATE [QUERY_REDACTED] SET'),
    ]
    
    for pattern, replacement in sensitive_patterns:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
    
    # If message contains technical details, use generic message
    if any(keyword in sanitized.lower() for keyword in [
        'traceback', 'line ', '.py:', 'module', 'attribute',
        'object at 0x', 'memory at', 'frame at'
    ]):
        sanitized = "An error occurred. Please check the logs or contact support."
    
    return sanitized


class ConfigurationError(AutoPRException):
    """Raised when there's an issue with configuration."""

    def __init__(self, message: str, config_key: str | None = None):
        user_msg = "Configuration error. Please check your settings."
        if config_key:
            # Sanitize config_key to avoid leaking sensitive key names
            safe_key = config_key.replace('password', '[REDACTED]').replace('secret', '[REDACTED]').replace('key', '[REDACTED]')
            user_msg = f"Configuration error for setting: {safe_key}"
        super().__init__(message, "CONFIG_ERROR", user_msg)
        self.config_key = config_key


class IntegrationError(AutoPRException):
    """Raised when there's an issue with external integrations."""

    def __init__(self, message: str, integration_name: str | None = None):
        user_msg = "Integration error occurred."
        if integration_name:
            message = f"Integration '{integration_name}': {message}"
            user_msg = f"Integration error with {integration_name}. Please check configuration."
        super().__init__(message, "INTEGRATION_ERROR", user_msg)
        self.integration_name = integration_name


class WorkflowError(AutoPRException):
    """Raised when there's an issue with workflow execution."""

    def __init__(self, message: str, workflow_name: str | None = None):
        user_msg = "Workflow execution failed."
        if workflow_name:
            message = f"Workflow '{workflow_name}': {message}"
            user_msg = f"Workflow '{workflow_name}' failed. Please check configuration."
        super().__init__(message, "WORKFLOW_ERROR", user_msg)
        self.workflow_name = workflow_name


class ActionError(AutoPRException):
    """Raised when there's an issue with action execution."""

    def __init__(self, message: str, action_name: str | None = None):
        user_msg = "Action execution failed."
        if action_name:
            message = f"Action '{action_name}': {message}"
            user_msg = f"Action '{action_name}' failed."
        super().__init__(message, "ACTION_ERROR", user_msg)
        self.action_name = action_name


class LLMProviderError(AutoPRException):
    """Raised when there's an issue with LLM providers."""

    def __init__(self, message: str, provider_name: str | None = None):
        user_msg = "AI service error occurred."
        if provider_name:
            message = f"LLM Provider '{provider_name}': {message}"
            user_msg = f"AI service '{provider_name}' is temporarily unavailable."
        super().__init__(message, "LLM_ERROR", user_msg)
        self.provider_name = provider_name


class ValidationError(AutoPRException):
    """Raised when data validation fails."""

    def __init__(self, message: str, field_name: str | None = None):
        user_msg = "Invalid input provided."
        if field_name:
            message = f"Validation error for '{field_name}': {message}"
            user_msg = f"Invalid input for field '{field_name}'."
        super().__init__(message, "VALIDATION_ERROR", user_msg)
        self.field_name = field_name


class RateLimitError(AutoPRException):
    """Raised when rate limits are exceeded."""

    def __init__(self, message: str, retry_after: int | None = None):
        user_msg = "Rate limit exceeded. Please try again later."
        if retry_after:
            user_msg = f"Rate limit exceeded. Please try again in {retry_after} seconds."
        super().__init__(message, "RATE_LIMIT_ERROR", user_msg)
        self.retry_after = retry_after


class AuthenticationError(AutoPRException):
    """Raised when authentication fails."""

    def __init__(self, message: str):
        user_msg = "Authentication failed. Please check your credentials."
        super().__init__(message, "AUTH_ERROR", user_msg)


class AutoPRPermissionError(AutoPRException):
    """Raised when permission is denied."""

    def __init__(self, message: str, resource: str | None = None):
        user_msg = "Permission denied."
        if resource:
            user_msg = f"Permission denied for resource: {resource}"
        super().__init__(message, "PERMISSION_ERROR", user_msg)
        self.resource = resource


def log_exception_securely(
    error: Exception,
    context: Optional[dict[str, Any]] = None,
    level: str = 'error'
) -> None:
    """
    Log exception with full details for internal debugging.
    
    Logs complete information including stack trace that should
    NOT be exposed to end users.
    
    Args:
        error: Exception to log
        context: Additional context information
        level: Log level ('debug', 'info', 'warning', 'error', 'critical')
        
    Security: Only logs to internal logging system, never to user-facing responses.
    
    TODO: PRODUCTION - Integrate with error tracking (Sentry, DataDog)
    """
    import traceback
    
    context = context or {}
    
    # Build log message with context
    log_message = f"Exception occurred: {error.__class__.__name__}: {str(error)}"
    
    # Add context information
    if context:
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        log_message += f" | Context: {context_str}"
    
    # Add stack trace
    stack_trace = traceback.format_exc()
    
    # Get logger method based on level
    log_method = getattr(logger, level, logger.error)
    
    # Log with stack trace
    log_method(log_message, extra={'stack_trace': stack_trace})
    
    # TODO: PRODUCTION - Send to error tracking service
    # import sentry_sdk
    # sentry_sdk.capture_exception(error, contexts={'custom': context})


def handle_exception_safely(
    error: Exception,
    context: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """
    Handle exception with secure logging and sanitized error response.
    
    This is the primary exception handler for API responses. It:
    1. Logs full exception details internally (with sensitive data)
    2. Returns sanitized error for API responses (safe for end users)
    
    Args:
        error: Exception to handle
        context: Additional context for logging (internal only)
        
    Returns:
        Dictionary with sanitized error information for API response
        
    Security: Prevents information leakage while maintaining useful error messages.
    
    Example:
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     return handle_exception_safely(e, context={'user_id': 123})
    """
    # Log full exception details internally (may contain sensitive data)
    log_exception_securely(error, context=context, level='error')
    
    # Return sanitized response (safe for end users)
    if isinstance(error, AutoPRException):
        response = {
            'success': False,
            'error': error.get_user_message(),
            'error_code': error.error_code,
        }
        
        # Add safe context fields (whitelist approach)
        safe_fields = {
            'workflow_name': getattr(error, 'workflow_name', None),
            'action_name': getattr(error, 'action_name', None),
            'integration_name': getattr(error, 'integration_name', None),
            'retry_after': getattr(error, 'retry_after', None),
        }
        
        # Only include non-None values
        safe_context = {k: v for k, v in safe_fields.items() if v is not None}
        if safe_context:
            response['context'] = safe_context
    else:
        # Generic error for non-AutoPR exceptions
        response = {
            'success': False,
            'error': sanitize_error_message(str(error)),
            'error_code': 'INTERNAL_ERROR',
        }
    
    return response
