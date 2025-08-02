"""
Base tool class for quality analysis tools with timeout handling, error handling, and display output.
"""

from abc import ABC, abstractmethod
import asyncio
import time
from typing import Any, Generic, TypedDict, TypeVar

import structlog

# Change the bound to Any to allow TypedDict
TConfig = TypeVar("TConfig", bound=Any)
TIssue = TypeVar("TIssue")

logger = structlog.get_logger(__name__)


class ToolExecutionResult(TypedDict):
    """Result of tool execution with metadata."""

    success: bool
    issues: list[Any]
    execution_time: float
    error_message: str | None
    warnings: list[str]
    output_summary: str


class Tool(ABC, Generic[TConfig, TIssue]):
    """Abstract base class for quality tools with enhanced error handling and timeouts."""

    def __init__(self) -> None:
        self.default_timeout = 60.0  # Default 60 second timeout
        self.max_files_per_run = 100  # Limit files to prevent hanging
        self.verbose_output = False

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the tool."""

    @property
    @abstractmethod
    def description(self) -> str:
        """A brief description of what the tool does."""

    @property
    def category(self) -> str:
        """The category of the tool (e.g., 'linting', 'security', etc.)."""
        return "general"

    @property
    def timeout(self) -> float:
        """Get the timeout for this tool in seconds."""
        return self.default_timeout

    @property
    def max_files(self) -> int:
        """Get the maximum number of files this tool can process at once."""
        return self.max_files_per_run

    def get_display_name(self) -> str:
        """Get a user-friendly display name for the tool."""
        return self.name.replace("_", " ").title()

    async def run_with_timeout(self, files: list[str], config: TConfig) -> ToolExecutionResult:
        """
        Run the tool with timeout handling and error management.

        Args:
            files: The list of files to process
            config: The configuration for the tool

        Returns:
            ToolExecutionResult with execution metadata
        """
        start_time = time.time()
        warnings = []
        error_message = None
        issues = []

        try:
            # Limit files if needed
            if len(files) > self.max_files:
                warnings.append(f"Limited to first {self.max_files} files (out of {len(files)})")
                files = files[: self.max_files]

            # Run the tool with timeout
            if self.verbose_output:
                logger.info(
                    f"Starting {self.get_display_name()} analysis",
                    file_count=len(files),
                    timeout=self.timeout,
                )

            issues = await asyncio.wait_for(
                self._run_implementation(files, config), timeout=self.timeout
            )

            success = True

        except TimeoutError:
            error_message = (
                f"{self.get_display_name()} execution timed out after {self.timeout} seconds"
            )
            success = False
            logger.warning(f"Tool {self.name} timed out", timeout=self.timeout)

        except Exception as e:
            error_message = f"{self.get_display_name()} execution failed: {e!s}"
            success = False
            logger.error(f"Tool {self.name} failed", error=str(e))

        execution_time = time.time() - start_time

        # Generate output summary
        output_summary = self._generate_output_summary(issues, error_message, warnings)

        return ToolExecutionResult(
            success=success,
            issues=issues,
            execution_time=execution_time,
            error_message=error_message,
            warnings=warnings,
            output_summary=output_summary,
        )

    async def _run_implementation(self, files: list[str], config: TConfig) -> list[TIssue]:
        """
        Internal implementation method that tools should override.
        This is called by run_with_timeout with proper error handling.
        """
        return await self.run(files, config)

    @abstractmethod
    async def run(self, files: list[str], config: TConfig) -> list[TIssue]:
        """
        Run the tool on a list of files.
        Tools should implement this method with their specific logic.

        Args:
            files: The list of files to process.
            config: The configuration for the tool.

        Returns:
            A list of issues found by the tool.
        """

    def _generate_output_summary(
        self, issues: list[Any], error_message: str | None, warnings: list[str]
    ) -> str:
        """Generate a human-readable summary of the tool execution."""
        summary_parts = []

        # Add warnings if any
        if warnings:
            summary_parts.append(f"Warnings: {', '.join(warnings)}")

        # Add error if any
        if error_message:
            summary_parts.append(f"Error: {error_message}")
            return " | ".join(summary_parts)

        # Add success summary
        issue_count = len(issues)
        if issue_count == 0:
            summary_parts.append("No issues found")
        elif issue_count == 1:
            summary_parts.append("1 issue found")
        else:
            summary_parts.append(f"{issue_count} issues found")

        return " | ".join(summary_parts)

    def get_config_schema(self) -> dict[str, Any]:
        """Get the configuration schema for this tool."""
        return {
            "timeout": {
                "type": "float",
                "default": self.timeout,
                "description": f"Timeout in seconds for {self.get_display_name()} execution",
            },
            "max_files": {
                "type": "int",
                "default": self.max_files,
                "description": f"Maximum number of files to process with {self.get_display_name()}",
            },
            "verbose": {
                "type": "bool",
                "default": self.verbose_output,
                "description": f"Enable verbose output for {self.get_display_name()}",
            },
        }

    def validate_config(self, config: TConfig) -> list[str]:
        """Validate the configuration and return any validation errors."""
        errors = []

        if not isinstance(config, dict):
            return ["Configuration must be a dictionary"]

        # Check timeout
        if "timeout" in config:
            timeout = config["timeout"]
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                errors.append("Timeout must be a positive number")

        # Check max_files
        if "max_files" in config:
            max_files = config["max_files"]
            if not isinstance(max_files, int) or max_files <= 0:
                errors.append("max_files must be a positive integer")

        return errors

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics and recommendations for this tool."""
        return {
            "recommended_timeout": self.timeout,
            "recommended_max_files": self.max_files,
            "category": self.category,
            "description": self.description,
        }

    def __str__(self) -> str:
        """String representation of the tool."""
        return f"{self.get_display_name()} ({self.category})"

    def __repr__(self) -> str:
        """Detailed string representation of the tool."""
        return f"{self.__class__.__name__}(name='{self.name}', category='{self.category}')"
