"""
Linting Agent for AutoPR.
This module provides the LintingAgent class which is responsible for identifying
and fixing code style and quality issues in a codebase.
"""

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from autopr.actions.ai_linting_fixer import \
    ai_linting_fixer as _create_ai_linting_fixer
from autopr.actions.ai_linting_fixer.models import LintingIssue
from autopr.agents.base import BaseAgent

# Set up logger
logger = logging.getLogger(__name__)


@dataclass
class LintingInputs:
    """Inputs for the LintingAgent.

    Attributes:
        file_path: Path to the file to lint
        code: The code content to lint (if not provided, will be read from file_path)
        language: The programming language of the code
        rules: List of linting rules to apply (if None, all rules will be used)
        fix: Whether to automatically fix issues when possible
        context: Additional context for the linter
    """

    file_path: str
    code: str | None = None
    language: str | None = None
    rules: list[str] | None = None
    fix: bool = True
    context: dict[str, Any] | None = None


@dataclass
class LintingOutputs:
    """Outputs from the LintingAgent.

    Attributes:
        file_path: Path to the linted file
        original_code: The original code content
        fixed_code: The fixed code (if fixes were applied)
        issues: List of code issues found
        fixed_issues: List of issues that were fixed
        remaining_issues: List of issues that could not be fixed
        fix_summary: Summary of fixes applied
        metrics: Dictionary of linting metrics
    """

    file_path: str
    original_code: str
    fixed_code: str | None = None
    issues: list[LintingIssue] | None = None
    fixed_issues: list[LintingIssue] | None = None
    remaining_issues: list[LintingIssue] | None = None
    fix_summary: dict[str, Any] | None = None
    metrics: dict[str, Any] | None = None


class LintingAgent(BaseAgent[LintingInputs, LintingOutputs]):
    """Agent for identifying and fixing code style and quality issues.

    This agent uses a combination of rule-based and AI-powered analysis to
    detect and fix code style and quality issues in various programming languages.
    """

    def __init__(
        self,
        volume: int = 500,  # Default to moderate level (500/1000)
        *,
        verbose: bool = False,
        allow_delegation: bool = False,
        max_iter: int = 3,
        max_rpm: int | None = None,
        llm_manager: Any | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the LintingAgent.

        Args:
            volume: Volume level (0-1000) for linting strictness
            verbose: Whether to enable verbose logging
            allow_delegation: Whether to allow task delegation
            max_iter: Maximum number of iterations for the agent
            max_rpm: Maximum requests per minute for the agent
            llm_manager: Optional LLMProviderManager instance. If not provided,
                       a default one will be created.
            **kwargs: Additional keyword arguments passed to the base class
        """
        super().__init__(
            name="Code Linter",
            role="Identify and fix code style and quality issues.",
            backstory=(
                "You are an expert code linter with deep knowledge of coding standards "
                "and best practices across multiple programming languages. Your goal is "
                "to help developers write clean, maintainable, and bug-free code by "
                "identifying and fixing style and quality issues."
            ),
            volume=volume,
            verbose=verbose,
            allow_delegation=allow_delegation,
            max_iter=max_iter,
            max_rpm=max_rpm,
            **kwargs,
        )

        # Initialize the AI linting fixer (constructor manages its own LLM manager)
        if _create_ai_linting_fixer is None:
            msg = "AILintingFixer factory is not available. Ensure optional AI components are installed."
            raise ImportError(msg)
        self.linting_fixer = _create_ai_linting_fixer()

        # Register fixer agents
        self._register_fixer_agents()

    def _register_fixer_agents(self) -> None:
        """Register all available fixer agents."""
        # The AgentManager already initializes all agents, so we don't need to register them individually
        # Just ensure the agent manager is properly imported and used

    async def _execute(self, inputs: LintingInputs) -> LintingOutputs:
        """Lint and optionally fix code issues.

        Args:
            inputs: The input data for the agent

        Returns:
            LintingOutputs containing the linting results and fixes

        Raises:
            FileNotFoundError: If the input file doesn't exist
            PermissionError: If there are permission issues reading the file
            UnicodeDecodeError: If there's an encoding error reading the file
            OSError: For other file-related errors
        """
        try:
            # Read the file if code is not provided
            if inputs.code is None:
                try:
                    path = Path(inputs.file_path)
                    loop = asyncio.get_running_loop()
                    code = await loop.run_in_executor(None, path.read_text, "utf-8")
                except FileNotFoundError as e:
                    error_msg = f"File not found: {inputs.file_path}"
                    if self.verbose:
                        logger.exception("%s", error_msg)
                    raise FileNotFoundError(error_msg) from e
                except PermissionError as e:
                    error_msg = (
                        f"Permission denied when reading file: {inputs.file_path}"
                    )
                    if self.verbose:
                        logger.exception("%s", error_msg)
                    raise PermissionError(error_msg) from e
                except UnicodeDecodeError as e:
                    error_msg = (
                        f"Could not decode file {inputs.file_path} as UTF-8: {e!s}"
                    )
                    if self.verbose:
                        logger.exception("%s", error_msg)
                    # Preserve the original exception details while adding context
                    raise UnicodeDecodeError(
                        e.encoding,
                        e.object,
                        e.start,
                        e.end,
                        f"{e.reason} in file {inputs.file_path}",
                    ) from e
                except OSError as e:
                    error_msg = f"Error reading file {inputs.file_path}: {e!s}"
                    if self.verbose:
                        logger.exception("%s", error_msg)
                    raise OSError(error_msg) from e
            else:
                code = inputs.code

            # Determine language from file extension if not provided
            language = inputs.language or self._detect_language(inputs.file_path)

            # Set up the context
            context = inputs.context or {}
            context["language"] = language

            # Apply volume-based configuration
            _ = self.volume_config.config or {}

            # Placeholder: integration with AILintingFixer to be wired for single-file flow
            logger.debug(
                "LintingAgent single-file execution path; external fixer integration is pending"
            )

            return LintingOutputs(
                file_path=inputs.file_path,
                original_code=code,
                fixed_code=None,
                issues=[],
                fixed_issues=[],
                remaining_issues=[],
                fix_summary={},
                metrics={},
            )

        except Exception as e:
            # Log the error and return a response with the error
            if self.verbose:
                logger.exception("Error in LintingAgent: %s", e)

            # Create a default issue for the error
            error_issue = LintingIssue(
                file_path=inputs.file_path,
                line_number=1,
                column_number=1,
                error_code="linting-error",
                message=f"Error during linting: {e!s}",
                line_content="",
            )

            return LintingOutputs(
                file_path=inputs.file_path,
                original_code=inputs.code or "",
                issues=[error_issue],
                fixed_issues=[],
                remaining_issues=[error_issue],
                fix_summary={"error": f"{e!s}"},
                metrics={"error": f"{e!s}"},
            )

    def _detect_language(self, file_path: str) -> str:
        """Detect the programming language from the file extension.

        Args:
            file_path: Path to the file

        Returns:
            The detected programming language
        """
        # Get the file extension
        ext = Path(file_path).suffix.lower()

        # Map extensions to languages
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".go": "go",
            ".rb": "ruby",
            ".php": "php",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "cpp",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".rs": "rust",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".pl": "perl",
            ".sh": "bash",
            ".r": "r",
            ".m": "matlab",
            ".sql": "sql",
            ".html": "html",
            ".css": "css",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".xml": "xml",
            ".md": "markdown",
        }

        return language_map.get(ext, "text")

    def get_available_rules(self) -> list[dict[str, Any]]:
        """Get a list of all available linting rules.

        Returns:
            A list of dictionaries containing rule information
        """
        return []
