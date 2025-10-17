"""
AutoPR Engine Exceptions

Custom exception classes for the AutoPR Engine.
"""


class AutoPRException(Exception):
    """Base exception class for all AutoPR Engine errors."""

    def __init__(self, message: str, error_code: str | None = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ConfigurationError(AutoPRException):
    """Raised when there's an issue with configuration."""

    def __init__(self, message: str):
        super().__init__(message, "CONFIG_ERROR")


class IntegrationError(AutoPRException):
    """Raised when there's an issue with external integrations."""

    def __init__(self, message: str, integration_name: str | None = None):
        if integration_name:
            message = f"Integration '{integration_name}': {message}"
        super().__init__(message, "INTEGRATION_ERROR")
        self.integration_name = integration_name


class WorkflowError(AutoPRException):
    """Raised when there's an issue with workflow execution."""

    def __init__(self, message: str, workflow_name: str | None = None):
        if workflow_name:
            message = f"Workflow '{workflow_name}': {message}"
        super().__init__(message, "WORKFLOW_ERROR")
        self.workflow_name = workflow_name


class ActionError(AutoPRException):
    """Raised when there's an issue with action execution."""

    def __init__(self, message: str, action_name: str | None = None):
        if action_name:
            message = f"Action '{action_name}': {message}"
        super().__init__(message, "ACTION_ERROR")
        self.action_name = action_name


class LLMProviderError(AutoPRException):
    """Raised when there's an issue with LLM providers."""

    def __init__(self, message: str, provider_name: str | None = None):
        if provider_name:
            message = f"LLM Provider '{provider_name}': {message}"
        super().__init__(message, "LLM_ERROR")
        self.provider_name = provider_name


class ValidationError(AutoPRException):
    """Raised when data validation fails."""

    def __init__(self, message: str, field_name: str | None = None):
        if field_name:
            message = f"Validation error for '{field_name}': {message}"
        super().__init__(message, "VALIDATION_ERROR")
        self.field_name = field_name


class RateLimitError(AutoPRException):
    """Raised when rate limits are exceeded."""

    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message, "RATE_LIMIT_ERROR")
        self.retry_after = retry_after


class AuthenticationError(AutoPRException):
    """Raised when authentication fails."""

    def __init__(self, message: str):
        super().__init__(message, "AUTH_ERROR")


class AutoPRPermissionError(AutoPRException):
    """Raised when permission is denied."""

    def __init__(self, message: str):
        super().__init__(message, "PERMISSION_ERROR")
