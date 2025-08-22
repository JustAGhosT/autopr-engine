"""
Error Handler Module

This module provides error handling and recovery mechanisms for the AI linting fixer.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from typing import Any


logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories."""

    SYNTAX = "syntax"
    SEMANTIC = "semantic"
    RUNTIME = "runtime"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    PERMISSION = "permission"
    RESOURCE = "resource"
    UNKNOWN = "unknown"


class ErrorRecoveryStrategy(Enum):
    """Error recovery strategies."""

    RETRY = "retry"
    SKIP = "skip"
    FALLBACK = "fallback"
    ABORT = "abort"


@dataclass
class ErrorContext:
    """Context information for an error."""

    file_path: str | None = None
    line_number: int | None = None
    function_name: str | None = None
    module_name: str | None = None
    additional_info: dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorInfo:
    """Information about an error."""

    error_type: str
    message: str
    severity: ErrorSeverity
    category: ErrorCategory = ErrorCategory.UNKNOWN
    context: ErrorContext = field(default_factory=ErrorContext)
    file_path: str | None = None
    line_number: int | None = None


class ErrorHandler:
    """Handles errors and provides recovery mechanisms."""

    def __init__(self):
        """Initialize the error handler."""
        self.on_recovery_callbacks: list[Callable[[ErrorInfo, ErrorRecoveryStrategy], None]] = []
        self.error_count = 0
        self.recovery_count = 0

    def handle_error(self, error_info: ErrorInfo) -> ErrorRecoveryStrategy:
        """Handle an error and determine recovery strategy."""
        self.error_count += 1

        logger.warning(f"Error {self.error_count}: {error_info.error_type} - {error_info.message}")

        # Determine recovery strategy based on severity
        if error_info.severity == ErrorSeverity.CRITICAL:
            strategy = ErrorRecoveryStrategy.ABORT
        elif error_info.severity == ErrorSeverity.HIGH:
            strategy = ErrorRecoveryStrategy.FALLBACK
        elif error_info.severity == ErrorSeverity.MEDIUM:
            strategy = ErrorRecoveryStrategy.RETRY
        else:
            strategy = ErrorRecoveryStrategy.SKIP

        # Notify callbacks
        for callback in self.on_recovery_callbacks:
            try:
                callback(error_info, strategy)
            except Exception as e:
                logger.error(f"Error in recovery callback: {e}")

        return strategy

    def add_recovery_callback(
        self, callback: Callable[[ErrorInfo, ErrorRecoveryStrategy], None]
    ) -> None:
        """Add a recovery callback."""
        self.on_recovery_callbacks.append(callback)

    def get_error_stats(self) -> dict[str, int]:
        """Get error handling statistics."""
        return {
            "total_errors": self.error_count,
            "recoveries": self.recovery_count,
            "success_rate": (
                (self.error_count - self.recovery_count) / self.error_count
                if self.error_count > 0
                else 1.0
            ),
        }


def create_error_context(
    file_path: str | None = None,
    line_number: int | None = None,
    function_name: str | None = None,
    module_name: str | None = None,
    **additional_info: Any,
) -> ErrorContext:
    """Create an error context."""
    return ErrorContext(
        file_path=file_path,
        line_number=line_number,
        function_name=function_name,
        module_name=module_name,
        additional_info=additional_info,
    )


def get_default_error_handler() -> ErrorHandler:
    """Get the default error handler instance."""
    return error_handler


# Global error handler instance
error_handler = ErrorHandler()
