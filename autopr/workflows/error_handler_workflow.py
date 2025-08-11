"""
Error Handler Workflow

A specialized workflow for handling errors in AI linting fixer and other AutoPR components.
This workflow integrates with the existing workflow system and provides comprehensive
error tracking, categorization, and recovery capabilities.
"""

from datetime import datetime
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from autopr.actions.ai_linting_fixer.display import DisplayConfig, OutputMode
from autopr.actions.ai_linting_fixer.error_handler import (
    ErrorHandler,
    ErrorInfo,
    ErrorRecoveryStrategy,
    create_error_context,
)

from .base import Workflow

logger = logging.getLogger(__name__)


class ErrorHandlerWorkflowInputs(BaseModel):
    """Inputs for the error handler workflow."""

    # Error information
    exception: Exception | None = None
    error_message: str | None = None
    error_type: str | None = None

    # Context information
    file_path: str | None = None
    line_number: int | None = None
    function_name: str | None = None
    workflow_step: str | None = None
    session_id: str | None = None

    # Additional context
    additional_info: dict[str, Any] = Field(default_factory=dict)

    # Workflow configuration
    enable_recovery: bool = True
    enable_display: bool = True
    enable_export: bool = False
    export_path: str | None = None

    # Recovery settings
    max_retries: int = 3
    retry_delay: float = 1.0


class ErrorHandlerWorkflowOutputs(BaseModel):
    """Outputs from the error handler workflow."""

    # Error processing results
    error_handled: bool
    error_info: ErrorInfo | None = None
    recovery_attempted: bool = False
    recovery_successful: bool = False

    # Error summary
    total_errors_processed: int = 0
    errors_by_category: dict[str, int] = Field(default_factory=dict)
    errors_by_severity: dict[str, int] = Field(default_factory=dict)

    # Export information
    error_report_exported: bool = False
    export_path: str | None = None

    # Workflow status
    success: bool
    summary: str
    error_message: str | None = None


class ErrorHandlerWorkflow(Workflow):
    """
    Specialized workflow for handling errors in AutoPR components.

    This workflow provides:
    - Error categorization and severity assessment
    - Intelligent recovery strategies
    - Error history tracking and export
    - Integration with existing workflow system
    - Callback support for external notifications
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the error handler workflow."""
        super().__init__(
            name="error_handler",
            description="Comprehensive error handling workflow for AutoPR components",
            version="1.0.0",
        )

        self.config = config or {}
        self.error_handler: ErrorHandler | None = None
        self.display_config: DisplayConfig | None = None

        # Supported events
        self.supported_events = [
            "error_occurred",
            "recovery_needed",
            "error_summary_requested",
            "error_export_requested",
        ]

    async def initialize(self) -> None:
        """Initialize the error handler workflow."""
        try:
            # Create display configuration
            self.display_config = DisplayConfig(
                mode=OutputMode.VERBOSE if self.config.get("verbose", False) else OutputMode.NORMAL,
                use_colors=self.config.get("use_colors", True),
                use_emojis=self.config.get("use_emojis", True),
            )

            # Initialize error handler
            self.error_handler = ErrorHandler(self.display_config)

            # Register callbacks if enabled
            if self.config.get("enable_callbacks", True):
                self._register_callbacks()

            logger.info("Error handler workflow initialized successfully")

        except Exception as e:
            logger.exception(f"Failed to initialize error handler workflow: {e}")
            raise

    def _register_callbacks(self) -> None:
        """Register error and recovery callbacks."""
        if not self.error_handler:
            return

        def on_error_callback(error_info: ErrorInfo) -> None:
            """Callback for when errors occur."""
            logger.info(f"Error callback triggered: {error_info.error_type}")

            # Emit workflow event
            self.emit_event(
                "error_occurred",
                {
                    "error_id": error_info.error_id,
                    "error_type": error_info.error_type,
                    "category": error_info.category.value,
                    "severity": error_info.severity.value,
                },
            )

        def on_recovery_callback(error_info: ErrorInfo, strategy: ErrorRecoveryStrategy) -> None:
            """Callback for recovery attempts."""
            logger.info(f"Recovery callback: {strategy.value} for {error_info.error_type}")

            # Emit workflow event
            self.emit_event(
                "recovery_attempted",
                {
                    "error_id": error_info.error_id,
                    "strategy": strategy.value,
                    "retry_count": error_info.retry_count,
                },
            )

        self.error_handler.register_error_callback(on_error_callback)
        self.error_handler.register_recovery_callback(on_recovery_callback)

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the error handler workflow.

        Args:
            context: Execution context containing error information

        Returns:
            Workflow execution result
        """
        try:
            # Parse inputs
            inputs = ErrorHandlerWorkflowInputs(**context.get("inputs", {}))

            # Initialize if not already done
            if not self.error_handler:
                await self.initialize()

            # Process the error
            result = await self._process_error(inputs)

            # Export error report if requested
            if inputs.enable_export:
                result = await self._export_error_report(inputs, result)

            return result.dict()

        except Exception as e:
            logger.exception(f"Error handler workflow execution failed: {e}")
            return {"success": False, "error_message": str(e), "error_handled": False}

    async def _process_error(
        self, inputs: ErrorHandlerWorkflowInputs
    ) -> ErrorHandlerWorkflowOutputs:
        """Process an error with the error handler."""
        if not self.error_handler:
            msg = "Error handler not initialized"
            raise RuntimeError(msg)

        # Create error context
        context = create_error_context(
            file_path=inputs.file_path,
            line_number=inputs.line_number,
            function_name=inputs.function_name,
            workflow_step=inputs.workflow_step,
            session_id=inputs.session_id,
            **inputs.additional_info,
        )

        # Handle different input types
        if inputs.exception:
            # Process exception
            error_info = self.error_handler.log_error(
                inputs.exception, context, inputs.additional_info, display=inputs.enable_display
            )
        elif inputs.error_message:
            # Create synthetic exception for error message
            class SyntheticError(Exception):
                pass

            synthetic_exception = SyntheticError(inputs.error_message)
            error_info = self.error_handler.log_error(
                synthetic_exception, context, inputs.additional_info, display=inputs.enable_display
            )
        else:
            # No error to process
            return ErrorHandlerWorkflowOutputs(
                error_handled=False, success=True, summary="No error to process"
            )

        # Attempt recovery if enabled
        recovery_attempted = False
        recovery_successful = False

        if inputs.enable_recovery:
            recovery_attempted = True
            recovery_successful = self.error_handler.attempt_recovery(error_info)

        # Get error summary
        summary = self.error_handler.get_error_summary()

        return ErrorHandlerWorkflowOutputs(
            error_handled=True,
            error_info=error_info,
            recovery_attempted=recovery_attempted,
            recovery_successful=recovery_successful,
            total_errors_processed=summary["total_errors"],
            errors_by_category=summary["error_counts_by_category"],
            errors_by_severity=summary["error_counts_by_severity"],
            success=True,
            summary=f"Processed {summary['total_errors']} errors",
        )

    async def _export_error_report(
        self, inputs: ErrorHandlerWorkflowInputs, result: ErrorHandlerWorkflowOutputs
    ) -> ErrorHandlerWorkflowOutputs:
        """Export error report if requested."""
        if not self.error_handler:
            return result

        try:
            # Determine export path
            if inputs.export_path:
                export_path = inputs.export_path
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_path = f"./logs/error_report_{timestamp}.json"

            # Ensure directory exists
            Path(export_path).parent.mkdir(parents=True, exist_ok=True)

            # Export errors
            self.error_handler.export_errors(export_path)

            result.error_report_exported = True
            result.export_path = export_path

            logger.info(f"Error report exported to: {export_path}")

        except Exception as e:
            logger.exception(f"Failed to export error report: {e}")
            result.error_message = f"Export failed: {e}"

        return result

    async def get_error_summary(self) -> dict[str, Any]:
        """Get a summary of all processed errors."""
        if not self.error_handler:
            return {"total_errors": 0, "error_counts_by_category": {}}

        return self.error_handler.get_error_summary()

    async def clear_errors(self) -> None:
        """Clear all logged errors."""
        if self.error_handler:
            self.error_handler.clear_errors()

    async def export_errors(self, file_path: str) -> None:
        """Export errors to a file."""
        if self.error_handler:
            self.error_handler.export_errors(file_path)

    def emit_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Emit a workflow event."""
        # This would integrate with the existing workflow event system
        logger.debug(f"Error handler workflow event: {event_type} - {data}")


# Convenience functions for easy integration
async def create_error_handler_workflow(
    config: dict[str, Any] | None = None,
) -> ErrorHandlerWorkflow:
    """Create and initialize an error handler workflow."""
    workflow = ErrorHandlerWorkflow(config)
    await workflow.initialize()
    return workflow


async def handle_error_with_workflow(
    exception: Exception,
    context: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
) -> ErrorHandlerWorkflowOutputs:
    """Convenience function to handle an error using the workflow."""
    workflow = await create_error_handler_workflow(config)

    inputs = ErrorHandlerWorkflowInputs(exception=exception, **(context or {}))

    result = await workflow.execute({"inputs": inputs.dict()})
    return ErrorHandlerWorkflowOutputs(**result)
