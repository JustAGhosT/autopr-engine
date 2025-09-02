"""AutoPR Agents for code analysis and quality management."""

import asyncio
import contextlib
import inspect
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, field_validator

from autopr.actions import platform_detection
from autopr.actions.ai_linting_fixer import AILintingFixer as _AILintingFixer
from autopr.actions.quality_engine import QualityEngine
from autopr.actions.quality_engine.models import QualityInputs, QualityMode
from autopr.agents.models import CodeIssue, IssueSeverity


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
            raise ValueError(msg)
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
                    msg = f"enable_ai_agents must be a boolean or valid boolean string, got '{enable_ai_agents}'"
                    raise ValueError(msg)
            elif not isinstance(enable_ai_agents, bool):
                # Try to convert other types to boolean
                try:
                    v["enable_ai_agents"] = bool(enable_ai_agents)
                except Exception:
                    msg = f"enable_ai_agents must be a boolean, got {type(enable_ai_agents).__name__}"
                    raise ValueError(msg)

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
            linting_config.update(
                {
                    k: v
                    for k, v in self.volume_config.config.items()
                    if k.startswith("linting_")
                }
            )

        self._linting_fixer = _AILintingFixer(**linting_config)  # type: ignore[call-arg,misc]

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
                        severity=IssueSeverity.CRITICAL,
                    )
                ]

            # Process the file with the linting fixer
            if self._linting_fixer is None:
                return [
                    CodeIssue(
                        file_path=file_path,
                        line_number=0,
                        message="Linting fixer not initialized",
                        severity=IssueSeverity.CRITICAL,
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
                    severity=IssueSeverity.CRITICAL,
                )
            ]

        except FileNotFoundError:
            return [
                CodeIssue(
                    file_path=file_path,
                    line_number=0,
                    message="File not found",
                    severity=IssueSeverity.CRITICAL,
                )
            ]
        except PermissionError:
            return [
                CodeIssue(
                    file_path=file_path,
                    line_number=0,
                    message="Permission denied",
                    severity=IssueSeverity.CRITICAL,
                )
            ]
        except Exception as e:
            logging.exception(
                f"Unexpected error fixing code issues in {file_path}: {e}"
            )
            return [
                CodeIssue(
                    file_path=file_path,
                    line_number=0,
                    message=f"Unexpected error: {e}",
                    severity=IssueSeverity.CRITICAL,
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
                        severity=IssueSeverity.CRITICAL,
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
                    severity=IssueSeverity.CRITICAL,
                )
            ]

        except Exception as e:
            logging.exception(
                f"Unexpected error analyzing code quality in {file_path}: {e}"
            )
            return [
                CodeIssue(
                    file_path=file_path,
                    line_number=0,
                    message=f"Unexpected error: {e}",
                    severity=IssueSeverity.CRITICAL,
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

            return await self._quality_engine.execute(inputs, {})

        except Exception as e:
            logging.exception(f"Error analyzing quality: {e}")
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
