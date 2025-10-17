"""
Shared error handling utilities for AutoPR Engine.

This module provides standardized error handling helpers used across the codebase.
"""

import logging
from typing import TypeVar

from autopr.exceptions import AutoPRException


logger = logging.getLogger(__name__)

ExceptionT = TypeVar("ExceptionT", bound=Exception)


def handle_operation_error(
    operation_name: str,
    exception: Exception,
    error_class: type[AutoPRException] = AutoPRException,
    *,
    context_name: str | None = None,
    log_level: str = "exception",
    reraise: bool = True,
) -> None:
    """
    Standardized error handling helper for engine operations.
    
    Args:
        operation_name: Name of the operation that failed
        exception: The exception that was raised
        error_class: Exception class to raise (default: AutoPRException)
        context_name: Optional context identifier (e.g., workflow_name, action_name)
        log_level: Logging level to use ('exception', 'error', 'warning')
        reraise: Whether to reraise the exception after logging
        
    Raises:
        error_class: The specified exception class with formatted message
    """
    if context_name:
        error_msg = f"{context_name}: {operation_name} failed: {exception}"
    else:
        error_msg = f"{operation_name} failed: {exception}"
    
    if log_level == "exception":
        logger.exception(error_msg)
    elif log_level == "error":
        logger.error(error_msg)
    elif log_level == "warning":
        logger.warning(error_msg)
    
    if reraise:
        raise error_class(error_msg) from exception
