"""
Enhanced Error Handler for AI Linting Fixer

This module provides comprehensive error handling, categorization, and display
capabilities that integrate with the existing display system.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import operator
from pathlib import Path
import traceback
from typing import Any
from uuid import uuid4

from .display import DisplayConfig, DisplayFormatter, ErrorDisplay


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors that can occur."""

    # File system errors
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_DENIED = "permission_denied"
    DISK_SPACE = "disk_space"

    # Network/API errors
    API_TIMEOUT = "api_timeout"
    API_RATE_LIMIT = "api_rate_limit"
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_ERROR = "authentication_error"

    # Code analysis errors
    SYNTAX_ERROR = "syntax_error"
    PARSING_ERROR = "parsing_error"
    LINTING_ERROR = "linting_error"

    # AI/LLM errors
    AI_MODEL_ERROR = "ai_model_error"
    AI_RESPONSE_ERROR = "ai_response_error"
    AI_CONFIDENCE_LOW = "ai_confidence_low"

    # System errors
    MEMORY_ERROR = "memory_error"
    TIMEOUT_ERROR = "timeout_error"
    CONFIGURATION_ERROR = "configuration_error"

    # Workflow errors
    WORKFLOW_ERROR = "workflow_error"
    ORCHESTRATION_ERROR = "orchestration_error"

    # Unknown/Generic
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class ErrorContext:
    """Context information for an error."""

    file_path: str | None = None
    line_number: int | None = None
    function_name: str | None = None
    workflow_step: str | None = None
    user_action: str | None = None
    system_state: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: str | None = None


@dataclass
class ErrorInfo:
    """Comprehensive error information."""

    error_id: str = field(default_factory=lambda: str(uuid4()))
    error_type: str = ""
    error_message: str = ""
    error_details: str = ""
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    category: ErrorCategory = ErrorCategory.UNKNOWN_ERROR
    context: ErrorContext = field(default_factory=ErrorContext)

    # Recovery information
    is_recoverable: bool = True
    retry_count: int = 0
    max_retries: int = 3
    suggested_action: str | None = None

    # Technical details
    exception: Exception | None = None
    traceback: str | None = None
    stack_trace: list[str] = field(default_factory=list)


class ErrorRecoveryStrategy(Enum):
    """Strategies for error recovery."""

    RETRY = "retry"
    SKIP = "skip"
    FALLBACK = "fallback"
    ABORT = "abort"
    MANUAL_INTERVENTION = "manual_intervention"


class ErrorHandler:
    """Enhanced error handler with categorization and recovery strategies."""

    def __init__(self, display_config: DisplayConfig | None = None):
        """Initialize the error handler."""
        self.display_config = display_config or DisplayConfig()
        self.formatter = DisplayFormatter(self.display_config)
        self.error_display = ErrorDisplay(self.formatter)

        # Error tracking
        self.errors_logged: list[ErrorInfo] = []
        self.error_counts: dict[ErrorCategory, int] = {}
        self.recovery_attempts: dict[str, int] = {}

        # Map error categories to recovery strategies
        self.recovery_strategies = {
            ErrorCategory.FILE_NOT_FOUND: ErrorRecoveryStrategy.FALLBACK,
            ErrorCategory.PERMISSION_DENIED: ErrorRecoveryStrategy.MANUAL_INTERVENTION,
            ErrorCategory.API_TIMEOUT: ErrorRecoveryStrategy.RETRY,
            ErrorCategory.API_RATE_LIMIT: ErrorRecoveryStrategy.RETRY,
            ErrorCategory.NETWORK_ERROR: ErrorRecoveryStrategy.RETRY,
            ErrorCategory.AUTHENTICATION_ERROR: ErrorRecoveryStrategy.MANUAL_INTERVENTION,
            ErrorCategory.SYNTAX_ERROR: ErrorRecoveryStrategy.SKIP,
            ErrorCategory.PARSING_ERROR: ErrorRecoveryStrategy.SKIP,
            ErrorCategory.AI_MODEL_ERROR: ErrorRecoveryStrategy.FALLBACK,
            ErrorCategory.AI_RESPONSE_ERROR: ErrorRecoveryStrategy.RETRY,
            ErrorCategory.MEMORY_ERROR: ErrorRecoveryStrategy.ABORT,
            ErrorCategory.TIMEOUT_ERROR: ErrorRecoveryStrategy.RETRY,
            ErrorCategory.CONFIGURATION_ERROR: ErrorRecoveryStrategy.MANUAL_INTERVENTION,
            ErrorCategory.WORKFLOW_ERROR: ErrorRecoveryStrategy.ABORT,
            ErrorCategory.ORCHESTRATION_ERROR: ErrorRecoveryStrategy.FALLBACK,
            ErrorCategory.UNKNOWN_ERROR: ErrorRecoveryStrategy.RETRY,
        }

        # Map error categories to severity levels
        self.severity_mapping = {
            ErrorCategory.FILE_NOT_FOUND: ErrorSeverity.MEDIUM,
            ErrorCategory.PERMISSION_DENIED: ErrorSeverity.HIGH,
            ErrorCategory.DISK_SPACE: ErrorSeverity.CRITICAL,
            ErrorCategory.API_TIMEOUT: ErrorSeverity.MEDIUM,
            ErrorCategory.API_RATE_LIMIT: ErrorSeverity.MEDIUM,
            ErrorCategory.NETWORK_ERROR: ErrorSeverity.MEDIUM,
            ErrorCategory.AUTHENTICATION_ERROR: ErrorSeverity.HIGH,
            ErrorCategory.SYNTAX_ERROR: ErrorSeverity.LOW,
            ErrorCategory.PARSING_ERROR: ErrorSeverity.MEDIUM,
            ErrorCategory.LINTING_ERROR: ErrorSeverity.LOW,
            ErrorCategory.AI_MODEL_ERROR: ErrorSeverity.HIGH,
            ErrorCategory.AI_RESPONSE_ERROR: ErrorSeverity.MEDIUM,
            ErrorCategory.AI_CONFIDENCE_LOW: ErrorSeverity.LOW,
            ErrorCategory.MEMORY_ERROR: ErrorSeverity.CRITICAL,
            ErrorCategory.TIMEOUT_ERROR: ErrorSeverity.MEDIUM,
            ErrorCategory.CONFIGURATION_ERROR: ErrorSeverity.HIGH,
            ErrorCategory.WORKFLOW_ERROR: ErrorSeverity.CRITICAL,
            ErrorCategory.ORCHESTRATION_ERROR: ErrorSeverity.HIGH,
            ErrorCategory.UNKNOWN_ERROR: ErrorSeverity.MEDIUM,
        }

        # Error callbacks
        self.on_error_callbacks: list[Callable[[ErrorInfo], None]] = []
        self.on_recovery_callbacks: list[Callable[[ErrorInfo, ErrorRecoveryStrategy], None]] = []

    def register_error_callback(self, callback: Callable[[ErrorInfo], None]) -> None:
        """Register a callback to be called when errors occur."""
        self.on_error_callbacks.append(callback)

    def register_recovery_callback(
        self, callback: Callable[[ErrorInfo, ErrorRecoveryStrategy], None]
    ) -> None:
        """Register a callback to be called when recovery is attempted."""
        self.on_recovery_callbacks.append(callback)

    def categorize_error(
        self, exception: Exception, context: ErrorContext | None = None
    ) -> ErrorCategory:
        """Categorize an exception based on its type and context."""
        error_type = type(exception).__name__
        error_message = str(exception).lower()

        # File system errors
        if "file not found" in error_message or "no such file" in error_message:
            return ErrorCategory.FILE_NOT_FOUND
        if "permission denied" in error_message or "access denied" in error_message:
            return ErrorCategory.PERMISSION_DENIED
        if "disk space" in error_message or "no space left" in error_message:
            return ErrorCategory.DISK_SPACE

        # Network/API errors
        if "timeout" in error_message or "timed out" in error_message:
            return ErrorCategory.API_TIMEOUT
        if "rate limit" in error_message or "too many requests" in error_message:
            return ErrorCategory.API_RATE_LIMIT
        if "network" in error_message or "connection" in error_message:
            return ErrorCategory.NETWORK_ERROR
        if "authentication" in error_message or "unauthorized" in error_message:
            return ErrorCategory.AUTHENTICATION_ERROR

        # Code analysis errors
        if "syntax" in error_message or "syntaxerror" in error_type.lower():
            return ErrorCategory.SYNTAX_ERROR
        if "parse" in error_message or "parsing" in error_message:
            return ErrorCategory.PARSING_ERROR
        if "lint" in error_message or "flake8" in error_message:
            return ErrorCategory.LINTING_ERROR

        # AI/LLM errors
        if "ai" in error_message or "model" in error_message:
            return ErrorCategory.AI_MODEL_ERROR
        if "response" in error_message and ("ai" in error_message or "llm" in error_message):
            return ErrorCategory.AI_RESPONSE_ERROR
        if "confidence" in error_message and "low" in error_message:
            return ErrorCategory.AI_CONFIDENCE_LOW

        # System errors
        if "memory" in error_message or "memoryerror" in error_type.lower():
            return ErrorCategory.MEMORY_ERROR
        if "timeout" in error_message:
            return ErrorCategory.TIMEOUT_ERROR
        if "config" in error_message or "configuration" in error_message:
            return ErrorCategory.CONFIGURATION_ERROR

        # Workflow errors
        if "workflow" in error_message:
            return ErrorCategory.WORKFLOW_ERROR
        if "orchestration" in error_message:
            return ErrorCategory.ORCHESTRATION_ERROR

        return ErrorCategory.UNKNOWN_ERROR

    def determine_severity(
        self, category: ErrorCategory, context: ErrorContext | None = None
    ) -> ErrorSeverity:
        """Determine the severity of an error based on its category and context."""
        return self.severity_mapping.get(category, ErrorSeverity.MEDIUM)

    def get_suggested_action(
        self, category: ErrorCategory, context: ErrorContext | None = None
    ) -> str:
        """Get a suggested action for resolving the error."""
        suggestions = {
            ErrorCategory.FILE_NOT_FOUND: "Check if the file exists and the path is correct",
            ErrorCategory.PERMISSION_DENIED: "Check file permissions and ensure you have write access",
            ErrorCategory.API_TIMEOUT: "Retry the operation or increase timeout settings",
            ErrorCategory.API_RATE_LIMIT: "Wait before retrying or reduce request frequency",
            ErrorCategory.NETWORK_ERROR: "Check network connectivity and retry",
            ErrorCategory.SYNTAX_ERROR: "Review the code for syntax issues",
            ErrorCategory.AI_CONFIDENCE_LOW: "Review the AI suggestion manually",
            ErrorCategory.MEMORY_ERROR: "Reduce batch size or free up system memory",
            ErrorCategory.CONFIGURATION_ERROR: "Check configuration files and environment variables",
        }

        return suggestions.get(category, "Review the error details and take appropriate action")

    def create_error_info(
        self,
        exception: Exception,
        context: ErrorContext | None = None,
        additional_info: dict[str, Any] | None = None,
    ) -> ErrorInfo:
        """Create comprehensive error information."""
        if context is None:
            context = ErrorContext()

        category = self.categorize_error(exception, context)
        severity = self.determine_severity(category, context)
        suggested_action = self.get_suggested_action(category, context)

        error_info = ErrorInfo(
            error_type=type(exception).__name__,
            error_message=str(exception),
            error_details=traceback.format_exc(),
            severity=severity,
            category=category,
            context=context,
            suggested_action=suggested_action,
            exception=exception,
            traceback=traceback.format_exc(),
            stack_trace=traceback.format_exc().split("\n"),
        )

        # Add additional information
        if additional_info:
            for key, value in additional_info.items():
                setattr(error_info, key, value)

        return error_info

    def log_error(
        self,
        exception: Exception,
        context: ErrorContext | None = None,
        additional_info: dict[str, Any] | None = None,
        display: bool = True,
    ) -> ErrorInfo:
        """Log an error with comprehensive information."""
        error_info = self.create_error_info(exception, context, additional_info)

        # Track error
        self.errors_logged.append(error_info)
        self.error_counts[error_info.category] = self.error_counts.get(error_info.category, 0) + 1

        # Display error if requested
        if display:
            self.display_error(error_info)

        # Call registered callbacks
        for callback in self.on_error_callbacks:
            try:
                callback(error_info)
            except Exception as e:
                # Don't let callback errors break the error handling
                logging.exception(f"Error in error callback: {e}")

        return error_info

    def display_error(self, error_info: ErrorInfo) -> None:
        """Display an error using the existing display system."""
        # Format error message
        severity_emoji = {
            ErrorSeverity.LOW: "ℹ️",
            ErrorSeverity.MEDIUM: "⚠️",
            ErrorSeverity.HIGH: "❌",
            ErrorSeverity.CRITICAL: "🚨",
        }

        emoji = severity_emoji.get(error_info.severity, "❌")
        message = f"{emoji} {error_info.category.value.replace('_', ' ').title()}: {error_info.error_message}"

        # Display based on severity
        if error_info.severity in {ErrorSeverity.HIGH, ErrorSeverity.CRITICAL}:
            self.error_display.show_error(message, error_info.error_details)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            self.error_display.show_warning(message)
        else:
            self.error_display.show_info(message)

        # Show suggested action if available
        if error_info.suggested_action and self.display_config.is_verbose():
            self.error_display.show_info(f"💡 Suggested action: {error_info.suggested_action}")

    def get_recovery_strategy(self, error_info: ErrorInfo) -> ErrorRecoveryStrategy:
        """Get the recovery strategy for an error."""
        return self.recovery_strategies.get(error_info.category, ErrorRecoveryStrategy.SKIP)

    def attempt_recovery(self, error_info: ErrorInfo) -> bool:
        """Attempt to recover from an error."""
        strategy = self.get_recovery_strategy(error_info)

        # Call recovery callbacks
        for callback in self.on_recovery_callbacks:
            try:
                callback(error_info, strategy)
            except Exception as e:
                logging.exception(f"Error in recovery callback: {e}")

        # Update retry count
        error_info.retry_count += 1
        self.recovery_attempts[error_info.error_id] = error_info.retry_count

        # Check if we should retry
        if (
            strategy == ErrorRecoveryStrategy.RETRY
            and error_info.retry_count < error_info.max_retries
        ):
            self.error_display.show_info(
                f"🔄 Retrying... (attempt {error_info.retry_count}/{error_info.max_retries})"
            )
            return True

        return False

    def get_error_summary(self) -> dict[str, Any]:
        """Get a summary of all logged errors."""
        return {
            "total_errors": len(self.errors_logged),
            "error_counts_by_category": self.error_counts,
            "error_counts_by_severity": {
                severity.value: len([e for e in self.errors_logged if e.severity == severity])
                for severity in ErrorSeverity
            },
            "recovery_attempts": self.recovery_attempts,
            "most_common_error": (
                max(self.error_counts.items(), key=operator.itemgetter(1))
                if self.error_counts
                else None
            ),
        }

    def clear_errors(self) -> None:
        """Clear all logged errors."""
        self.errors_logged.clear()
        self.error_counts.clear()
        self.recovery_attempts.clear()

    def export_errors(self, file_path: str | Path) -> None:
        """Export errors to a file."""
        file_path = Path(file_path)

        summary = self.get_error_summary()
        summary["exported_at"] = datetime.now().isoformat()
        summary["errors"] = [
            {
                "error_id": error.error_id,
                "error_type": error.error_type,
                "error_message": error.error_message,
                "severity": error.severity.value,
                "category": error.category.value,
                "context": {
                    "file_path": error.context.file_path,
                    "line_number": error.context.line_number,
                    "function_name": error.context.function_name,
                    "workflow_step": error.context.workflow_step,
                    "timestamp": error.context.timestamp.isoformat(),
                },
                "retry_count": error.retry_count,
                "suggested_action": error.suggested_action,
            }
            for error in self.errors_logged
        ]

        import json

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)


# Convenience functions for easy integration
def create_error_context(
    file_path: str | None = None,
    line_number: int | None = None,
    function_name: str | None = None,
    workflow_step: str | None = None,
    session_id: str | None = None,
    **kwargs,
) -> ErrorContext:
    """Create an error context with the given parameters."""
    return ErrorContext(
        file_path=file_path,
        line_number=line_number,
        function_name=function_name,
        workflow_step=workflow_step,
        session_id=session_id,
        system_state=kwargs,
    )


def get_default_error_handler(display_config: DisplayConfig | None = None) -> ErrorHandler:
    """Get a default error handler instance."""
    return ErrorHandler(display_config)
