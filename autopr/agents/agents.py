"""AutoPR Agents for code analysis and quality management."""

import asyncio
import contextlib
import inspect
import logging
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel, field_validator

from autopr.actions import platform_detection
from autopr.actions.ai_linting_fixer import AILintingFixer as _AILintingFixer
from autopr.actions.ai_linting_fixer.models import AILintingFixerInputs, AILintingFixerOutputs
from autopr.actions.quality_engine import QualityEngine
from autopr.actions.quality_engine.models import QualityInputs, QualityMode
from autopr.agents.models import CodeIssue, IssueSeverity


def get_highest_severity() -> IssueSeverity:
    """Get the highest available severity level, falling back through ordered severity levels."""
    # Safe ordered lookup to avoid direct attribute evaluation at import time
    severity_names = ["CRITICAL", "ERROR", "HIGH", "MEDIUM", "WARNING", "LOW", "INFO"]

    for name in severity_names:
        severity = getattr(IssueSeverity, name, None)
        if severity is not None:
            return severity

    # Fallback to INFO if nothing else is available
    return IssueSeverity.INFO


class VolumeConfig(BaseModel):
    """Configuration for volume-based quality control."""

    volume: int = 500
    quality_mode: QualityMode = QualityMode.SMART
    config: dict[str, Any] = {}

    @field_validator("volume")
    @classmethod
    def validate_volume(cls, v: int) -> int:
        """Validate volume is between 0 and 1000."""
        if v < 0:
            return 0
        if v > 1000:
            return 1000
        return v

    @field_validator("quality_mode")
    @classmethod
    def validate_quality_mode(cls, v: QualityMode) -> QualityMode:
        """Validate quality mode is valid."""
        if not isinstance(v, QualityMode):
            msg = "Quality mode must be a valid QualityMode enum"
            raise TypeError(msg)
        return v

    @field_validator("config")
    @classmethod
    def validate_config(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate config and add defaults."""
        if v is None:
            v = {}

        # Convert enable_ai_agents to boolean if present
        if "enable_ai_agents" in v:
            enable_ai_agents = v["enable_ai_agents"]
            if isinstance(enable_ai_agents, str):
                # Convert string to boolean
                enable_ai_agents = enable_ai_agents.strip().lower()
                if enable_ai_agents in ("true", "t", "yes", "y", "on", "1"):
                    v["enable_ai_agents"] = True
                elif enable_ai_agents in ("false", "f", "no", "n", "off", "0"):
                    v["enable_ai_agents"] = False
                else:
                    msg = (
                        f"enable_ai_agents must be a boolean or valid boolean string, "
                        f"got '{enable_ai_agents}'"
                    )
                    raise ValueError(msg)
            elif not isinstance(enable_ai_agents, bool):
                # Try to convert other types to boolean
                try:
                    v["enable_ai_agents"] = bool(enable_ai_agents)
                except Exception:
                    msg = (
                        f"enable_ai_agents must be a boolean, "
                        f"got {type(enable_ai_agents).__name__}"
                    )
                    raise ValueError(msg) from None

        # Add enable_ai_agents if not present
        if "enable_ai_agents" not in v:
            # We can't access self.volume here, so we'll set a default
            v["enable_ai_agents"] = True  # Default to True, will be updated in __init__

        return v

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization to set enable_ai_agents based on volume."""
        if "enable_ai_agents" not in self.config:
            self.config["enable_ai_agents"] = self.volume >= 600


class BaseAgent:
    """Base class for all AutoPR agents."""

    def __init__(self, role: str, goal: str, backstory: str, **kwargs: Any) -> None:
        """Initialize the base agent."""
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.volume_config = VolumeConfig(**kwargs)
        self._platform_detector: Any = None
        self._quality_engine: Any = None

    @property
    def platform_detector(self) -> Any:
        """Get the platform detector instance."""
        if self._platform_detector is None:
            with contextlib.suppress(Exception):
                self._platform_detector = platform_detection.PlatformDetector()
        return self._platform_detector

    async def analyze_platform(self, repo_path: str) -> Any:
        """Analyze the platform and technology stack."""
        # Delegate directly and return the detector output for compatibility with tests
        detector = self.platform_detector
        analyze = detector.analyze

        # If the analyze attribute is a coroutine function, await it
        if asyncio.iscoroutinefunction(analyze):
            return await analyze(repo_path)  # type: ignore[misc]

        # Call once and await the result if it is awaitable (e.g., AsyncMock return)
        result = analyze(repo_path)
        if inspect.isawaitable(result):  # type: ignore[arg-type]
            return await result  # type: ignore[misc]
        return result


class LintingFixerWrapper:
    """Wrapper for AILintingFixer to provide the expected interface for agents."""

    def __init__(self, linting_fixer: _AILintingFixer):
        self._fixer = linting_fixer

    async def fix_file(self, file_path: str, _file_content: str) -> Any:
        """Fix linting issues in a single file."""
        inputs = AILintingFixerInputs(
            target_path=file_path,
            max_fixes=10,
            create_backups=False,
            dry_run=False
        )
        result: AILintingFixerOutputs = cast(Any, self._fixer).run(inputs)

        # Convert the result to the expected format
        class FixResult:
            def __init__(
                self, success: bool, fixed_issues: list[CodeIssue],
                error_message: str | None = None
            ):
                self.success = success
                self.fixed_issues = fixed_issues
                self.error_message = error_message

        # Convert AILintingFixerOutputs to the expected format
        fixed_issues = []
        if result.success and result.issues_fixed > 0:
            # Create CodeIssue objects from the results
            for file_modified in result.files_modified:
                fixed_issues.append(CodeIssue(
                    file_path=file_modified,
                    line_number=0,
                    message="Fixed linting issues",
                    severity=IssueSeverity.INFO
                ))

        return FixResult(
            success=result.success,
            fixed_issues=fixed_issues,
            error_message=getattr(result, 'error_message', None)
        )

    async def analyze_file(self, file_path: str, _file_content: str) -> Any:
        """Analyze linting issues in a single file without fixing."""
        inputs = AILintingFixerInputs(
            target_path=file_path,
            max_fixes=0,  # Don't fix, just analyze
            create_backups=False,
            dry_run=True
        )
        result: AILintingFixerOutputs = cast(Any, self._fixer).run(inputs)

        # Convert the result to the expected format
        class AnalysisResult:
            def __init__(
                self, success: bool, issues: list[CodeIssue], error_message: str | None = None
            ):
                self.success = success
                self.issues = issues
                self.error_message = error_message

        # Convert detected issues to CodeIssue objects
        issues = []
        if result.total_issues_detected > 0:
            # For now, create a generic issue since we don't have detailed issue info
            issues.append(CodeIssue(
                file_path=file_path,
                line_number=0,
                message=f"Found {result.total_issues_detected} linting issues",
                severity=IssueSeverity.WARNING
            ))

        return AnalysisResult(
            success=result.success,
            issues=issues,
            error_message=getattr(result, 'error_message', None)
        )


class LintingAgent(BaseAgent):
    """Agent responsible for code linting and style enforcement with volume-aware strictness."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the linting agent with volume control.

        Args:
            **kwargs: Additional arguments including 'volume' (0-1000)
        """
        super().__init__(
            role="Senior Linting Engineer",
            goal="Detect and fix code style and quality issues with configurable strictness",
            backstory="""You are an expert in code style guides, best practices, and
            automated code quality tools. You help maintain consistent code quality
            across the codebase. You're meticulous about following style guides and
            can spot even the most subtle style violations.

            Your strictness and thoroughness are adjusted based on the current volume level.""",
            **kwargs,
        )

        # Configure linting fixer based on volume
        linting_config = {}
        if self.volume_config.config:
            # Filter to only include valid AILintingFixer parameters
            valid_params = {"llm_manager", "max_workers", "workflow_context"}
            linting_config.update(
                {
                    k: v
                    for k, v in self.volume_config.config.items()
                    if k.startswith("linting_") and k.replace("linting_", "") in valid_params
                }
            )

        # Initialize linting fixer, but handle potential failures gracefully
        self._linting_fixer: Any = None
        try:
            base_fixer = _AILintingFixer(**linting_config)
            self._linting_fixer = LintingFixerWrapper(base_fixer)
        except Exception as e:
            logging.warning("Failed to initialize linting fixer: %s", e)
            self._linting_fixer = None

        # Adjust verbosity based on volume
        self._verbose = False
        if self.volume_config.quality_mode:
            self._verbose = self.volume_config.quality_mode != QualityMode.ULTRA_FAST

    @property
    def linting_fixer(self) -> Any:
        """Get the linting fixer instance."""
        return self._linting_fixer

    @property
    def verbose(self) -> bool:
        """Get the verbosity setting."""
        return self._verbose

    @verbose.setter
    def verbose(self, value: bool) -> None:
        """Set the verbosity setting."""
        self._verbose = value

    async def fix_code_issues(self, file_path: str) -> list[CodeIssue]:
        """Fix code style and quality issues in the specified file.

        Args:
            file_path: Path to the file to fix

        Returns:
            List[CodeIssue]: List of fixed issues, or an error issue if processing failed

        Raises:
            FileNotFoundError: If the specified file does not exist
            PermissionError: If there are permission issues reading/writing the file
        """
        try:
            # Get the file content
            try:
                with Path(file_path).open(encoding="utf-8") as f:
                    file_content = f.read()
            except UnicodeDecodeError as e:
                return [
                    CodeIssue(
                        file_path=file_path,
                        line_number=0,
                        message=f"Unicode decode error: {e}",
                        severity=get_highest_severity(),
                    )
                ]

            # Process the file with the linting fixer
            if self._linting_fixer is None:
                return [
                    CodeIssue(
                        file_path=file_path,
                        line_number=0,
                        message="Linting fixer not initialized",
                        severity=get_highest_severity(),
                    )
                ]
            result = await self._linting_fixer.fix_file(file_path, file_content)

            if result.success:
                return result.fixed_issues
            return [
                CodeIssue(
                    file_path=file_path,
                    line_number=0,
                    message=f"Linting failed: {result.error_message}",
                    severity=get_highest_severity(),
                )
            ]

        except FileNotFoundError:
            return [
                CodeIssue(
                    file_path=file_path,
                    line_number=0,
                    message="File not found",
                    severity=get_highest_severity(),
                )
            ]
        except PermissionError:
            return [
                CodeIssue(
                    file_path=file_path,
                    line_number=0,
                    message="Permission denied",
                    severity=get_highest_severity(),
                )
            ]
        except Exception as e:
            logging.exception(
                "Unexpected error fixing code issues in %s", file_path
            )
            return [
                CodeIssue(
                    file_path=file_path,
                    line_number=0,
                    message=f"Unexpected error: {e}",
                    severity=get_highest_severity(),
                )
            ]

    async def analyze_code_quality(self, file_path: str) -> list[CodeIssue]:
        """Analyze code quality in the specified file.

        Args:
            file_path: Path to the file to analyze

        Returns:
            List[CodeIssue]: List of quality issues found
        """
        try:
            # Get the file content
            try:
                with Path(file_path).open(encoding="utf-8") as f:
                    file_content = f.read()
            except UnicodeDecodeError as e:
                return [
                    CodeIssue(
                        file_path=file_path,
                        line_number=0,
                        message=f"Unicode decode error: {e}",
                        severity=get_highest_severity(),
                    )
                ]

            # Process the file with the linting fixer for analysis only
            result = await self._linting_fixer.analyze_file(file_path, file_content)

            if result.success:
                return result.issues
            return [
                CodeIssue(
                    file_path=file_path,
                    line_number=0,
                    message=f"Analysis failed: {result.error_message}",
                    severity=get_highest_severity(),
                )
            ]

        except Exception as e:
            logging.exception(
                "Unexpected error analyzing code quality in %s", file_path
            )
            return [
                CodeIssue(
                    file_path=file_path,
                    line_number=0,
                    message=f"Unexpected error: {e}",
                    severity=get_highest_severity(),
                )
            ]


class QualityAgent(BaseAgent):
    """Agent responsible for comprehensive code quality analysis."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the quality agent."""
        super().__init__(
            role="Senior Code Quality Engineer",
            goal="Analyze and improve overall code quality and maintainability",
            backstory="""You are an expert in code quality metrics, maintainability analysis,
            and best practices for writing clean, maintainable code. You understand
            the importance of code quality for long-term project success and can
            identify areas for improvement across the codebase.

            Your analysis depth and thoroughness are adjusted based on the current volume level.""",
            **kwargs,
        )

        # Initialize quality engine
        quality_config = {}
        if self.volume_config.config:
            quality_config.update(
                {
                    k: v
                    for k, v in self.volume_config.config.items()
                    if k.startswith("quality_")
                }
            )

        self._quality_engine: QualityEngine = QualityEngine()

    @property
    def quality_engine(self) -> QualityEngine:
        """Get the quality engine instance."""
        return self._quality_engine

    async def analyze_quality(self, repo_path: str) -> Any:
        """Analyze code quality across the repository."""
        try:
            inputs = QualityInputs(
                mode=self.volume_config.quality_mode,
                files=[repo_path],  # Use files parameter instead of repository_path
                **self.volume_config.config,
            )

            return await self._quality_engine.execute(inputs, {}, self.volume_config.config)

        except Exception:
            logging.exception("Error analyzing quality")
            return None


class AutoPRCrew:
    """Main crew for AutoPR operations."""

    def __init__(self, volume: int = 500, **kwargs: Any) -> None:
        """Initialize the AutoPR crew."""
        self.volume = volume
        self.linting_agent = LintingAgent(volume=volume, **kwargs)
        self.quality_agent = QualityAgent(volume=volume, **kwargs)

    async def analyze_repository(self, repo_path: str) -> dict[str, Any]:
        """Analyze the repository for code quality issues."""
        results = {}

        # Platform analysis
        platform_result = await self.linting_agent.analyze_platform(repo_path)
        results["platform"] = platform_result

        # Quality analysis
        quality_result = await self.quality_agent.analyze_quality(repo_path)
        results["quality"] = quality_result

        return results

    async def fix_issues(self, file_path: str) -> list[CodeIssue]:
        """Fix issues in a specific file."""
        return await self.linting_agent.fix_code_issues(file_path)
