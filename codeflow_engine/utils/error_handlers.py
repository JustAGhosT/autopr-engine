"""
Shared Error Handling Utilities

Common error handling patterns used across the AutoPR engine.
"""

import logging
from typing import Any

from codeflow_engine.exceptions import AutoPRException


logger = logging.getLogger(__name__)


def handle_operation_error(
    operation_name: str,
    exception: Exception,
    error_class: type[AutoPRException] = AutoPRException,
    *,
    log_level: str = "exception",
    reraise: bool = True,
    **kwargs: Any,
) -> None:
    """
    Standardized error handling helper for engine operations.
    
    Args:
        operation_name: Name of the operation that failed
        exception: The exception that was raised
        error_class: Exception class to raise (default: AutoPRException)
        log_level: Logging level to use ('exception', 'error', 'warning')
        reraise: Whether to reraise the exception after logging
        **kwargs: Additional keyword arguments passed to the error class
        
    Raises:
        error_class: The specified exception class with formatted message
    """
    error_msg = f"{operation_name} failed: {exception}"
    
    if log_level == "exception":
        logger.exception(error_msg)
    elif log_level == "error":
        logger.error(error_msg)
    elif log_level == "warning":
        logger.warning(error_msg)
    
    if reraise:
        raise error_class(error_msg, **kwargs) from exception


def handle_workflow_error(
    workflow_name: str,
    operation: str,
    exception: Exception,
    *,
    log_level: str = "exception",
) -> None:
    """
    Standardized error handling helper for workflow operations.
    
    Args:
        workflow_name: Name of the workflow
        operation: Operation that failed (e.g., 'execution', 'validation')
        exception: The exception that was raised
        log_level: Logging level to use ('exception', 'error', 'warning')
        
    Raises:
        WorkflowError: Workflow error with formatted message
    """
    from codeflow_engine.exceptions import WorkflowError
    
    error_msg = f"Workflow {operation} failed: {exception}"
    
    if log_level == "exception":
        logger.exception(error_msg)
    elif log_level == "error":
        logger.error(error_msg)
    elif log_level == "warning":
        logger.warning(error_msg)
    
    raise WorkflowError(error_msg, workflow_name) from exception
