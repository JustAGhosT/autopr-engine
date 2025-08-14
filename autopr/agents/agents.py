"""
Agent definitions for the AutoPR Agent Framework.

This module defines the specialized agents used in the AutoPR code analysis pipeline.
"""

from typing import Any

from pydantic import BaseModel, field_validator

# Provide a fallback for typing/mypy when crewai is not available
try:  # pragma: no cover - import-time compatibility shim
    from crewai import Agent  # type: ignore[import-not-found]
except Exception:  # pragma: no cover

    class Agent:  # type: ignore[no-redef]
        """Fallback Agent stub used when crewai is unavailable.

        Accepts arbitrary keyword arguments and assigns them as attributes so
        subclasses can safely call super().__init__(...) with rich kwargs.
        """

        def __init__(self, *args, **kwargs) -> None:  # noqa: ARG002 - stub accepts *args
            for key, value in kwargs.items():
                setattr(self, key, value)


from autopr.actions import platform_detection
from autopr.actions.llm import get_llm_provider_manager
from autopr.actions.quality_engine import QualityEngine
from autopr.actions.quality_engine.models import QualityInputs
from autopr.agents.models import CodeIssue, IssueSeverity
from autopr.utils.volume_utils import QualityMode, get_volume_level_name


class VolumeConfig(BaseModel):
    """Pydantic model for validating volume configuration (used in tests)."""

    volume: int = 500
    quality_mode: QualityMode | None = None
    config: dict[str, Any] | None = None

    @field_validator("volume")
    @classmethod
    def _clamp_volume(cls, v: int) -> int:
        if not isinstance(v, int):
            msg = "volume must be int"
            raise ValueError(msg)
        return max(0, min(1000, v))

    @field_validator("config")
    @classmethod
    def _validate_config(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        if v is None:
            return v
        # Enforce that enable_ai_agents, if provided, must be boolean
        if "enable_ai_agents" in v and not isinstance(v["enable_ai_agents"], bool):
            msg = "enable_ai_agents must be a boolean"
            raise ValueError(msg)
        return v

    def model_post_init(self, __context: Any) -> None:  # type: ignore[override]
        # Populate defaults from volume mapping if not provided
        from autopr.utils.volume_utils import volume_to_quality_mode

        if self.quality_mode is None or self.config is None:
            mode, default_config = volume_to_quality_mode(self.volume)
            if self.quality_mode is None:
                self.quality_mode = mode
            if self.config is None:
                self.config = default_config
            else:
                merged = default_config.copy()
                merged.update(self.config)
                self.config = merged


class BaseAgent(Agent):
    """Base agent with common configuration and volume control."""

    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str,
        llm_model: str = "gpt-4",
        volume: int = 500,  # Default to moderate level
        **kwargs: Any,
    ) -> None:
        """Initialize the base agent with common settings.

        Args:
            role: The role of the agent
            goal: The goal of the agent
            backstory: The backstory of the agent
            llm_model: The LLM model to use (default: 'gpt-4')
            volume: Volume level (0-1000) controlling quality strictness
            **kwargs: Additional arguments to pass to the base Agent
        """
        # Initialize the base Agent class first to ensure all attributes are set up
        # We'll update the backstory after initialization
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,  # Will be updated after initialization
            llm=get_llm_provider_manager().get_provider(llm_model),
            allow_delegation=True,
            **kwargs,
        )

        # Now set up our custom attributes after parent initialization
        self._volume = max(0, min(1000, volume))  # Clamp to 0-1000 range
        self._volume_config = VolumeConfig(volume=self._volume)

        # Update the backstory with volume context
        volume_level = get_volume_level_name(self._volume)
        self.backstory = f"""{backstory}

        You are currently operating at volume level {self._volume} ({volume_level}).
        This affects the strictness of your analysis and the depth of your checks.
        """

    @property
    def volume(self) -> int:
        """Get the current volume level (0-1000)."""
        return self._volume

    @property
    def volume_config(self) -> VolumeConfig:
        """Get the volume configuration."""
        return self._volume_config

    def get_volume_context(self) -> dict[str, Any]:
        """Get context about the current volume level for agent tasks."""
        return {
            "volume": self._volume,
            "volume_level": get_volume_level_name(self._volume),
            "quality_mode": (
                self._volume_config.quality_mode.value if self._volume_config.quality_mode else None
            ),
            "quality_config": self._volume_config.config or {},
        }


class CodeQualityAgent(BaseAgent):
    """Agent responsible for code quality analysis with volume-aware strictness."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the code quality agent with volume control.

        Args:
            **kwargs: Additional arguments including 'volume' (0-1000)
        """
        # Initialize the base agent first
        super().__init__(
            role="Senior Code Quality Engineer",
            goal="Analyze and improve code quality through comprehensive checks with configurable strictness",
            backstory="""You are an expert in static code analysis, code smells detection,
            and quality metrics. You excel at identifying potential issues and suggesting
            improvements. You have a keen eye for detail and a deep understanding of
            software engineering best practices.""",
            **kwargs,
        )

        # Initialize the quality engine with volume configuration
        self._quality_engine = QualityEngine()

        # Configure quality engine based on volume if needed
        if self.volume_config.config:
            # Apply any quality engine specific configurations from volume config
            quality_config = {
                k: v for k, v in self.volume_config.config.items() if k.startswith("quality_")
            }
            if quality_config:
                # Apply quality config to the quality engine if needed
                pass

    @property
    def quality_engine(self) -> QualityEngine:
        """Get the quality engine instance."""
        return self._quality_engine

    async def analyze_code_quality(self, repo_path: str) -> dict[str, Any]:
        """Analyze code quality for the given repository."""
        # Build minimal inputs and delegate to the quality engine
        inputs = QualityInputs(files=[repo_path], volume=self.volume)
        outputs = await self._quality_engine.run(inputs)
        # Convert to a plain dict for callers/tests
        try:
            return outputs.model_dump()  # type: ignore[attr-defined]
        except Exception:
            try:
                return outputs.dict()  # type: ignore[attr-defined]
            except Exception:
                return {
                    "success": getattr(outputs, "success", True),
                    "summary": getattr(outputs, "summary", None),
                }


class PlatformAnalysisAgent(BaseAgent):
    """Agent responsible for platform and technology stack analysis with volume-aware depth."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the platform analysis agent with volume control.

        Args:
            **kwargs: Additional arguments including 'volume' (0-1000)
        """
        # Initialize the base agent first
        super().__init__(
            role="Platform Architecture Specialist",
            goal="Identify and analyze the technology stack and platform architecture with configurable depth",
            backstory="""You have deep knowledge of various technology stacks, frameworks,
            and platform architectures. You can detect platform-specific patterns and
            provide optimization recommendations. You understand how different components
            interact and can identify potential integration issues.

            Your analysis depth and thoroughness are adjusted based on the current volume level.""",
            **kwargs,
        )

        # Defer detector creation so tests can patch the class before first access
        self._platform_detector: platform_detection.PlatformDetector | None = None

        # Configure platform detector based on volume if needed
        if (
            self.volume_config.config
            and "platform_scan_depth" in self.volume_config.config
            and self._platform_detector is not None
            and hasattr(self._platform_detector, "scan_depth")
        ):
            self._platform_detector.scan_depth = self.volume_config.config[
                "platform_scan_depth"
            ]

    @property
    def platform_detector(self) -> platform_detection.PlatformDetector:
        """Get the platform detector instance."""
        if self._platform_detector is None:
            self._platform_detector = platform_detection.PlatformDetector()
            # Configure platform detector based on volume if needed
            if self.volume_config.config and "platform_scan_depth" in self.volume_config.config:
                try:
                    self._platform_detector.scan_depth = self.volume_config.config[
                        "platform_scan_depth"
                    ]
                except Exception:
                    # Some PlatformDetector implementations may not support dynamic attributes
                    pass
        return self._platform_detector

    async def analyze_platform(self, repo_path: str) -> Any:
        """Analyze the platform and technology stack."""
        # Delegate directly and return the detector output for compatibility with tests
        import asyncio
        import inspect

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
                {k: v for k, v in self.volume_config.config.items() if k.startswith("linting_")}
            )

        # Import locally to avoid type-resolution issues during static analysis
        from autopr.actions.ai_linting_fixer import AILintingFixer as _AILintingFixer

        self._linting_fixer = _AILintingFixer(**linting_config)  # type: ignore[call-arg]

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
                from pathlib import Path as _Path
                with _Path(file_path).open(encoding="utf-8") as f:
                    file_content = f.read()
            except UnicodeDecodeError as e:
                return [
                    CodeIssue(
                        file_path=file_path,
                        line_number=0,
                        column=0,
                        message=f"Failed to decode file: {e!s}. File may be binary or use a different encoding.",
                        severity=IssueSeverity.HIGH,
                        rule_id="encoding-error",
                        category="error",
                        fix=None,
                    )
                ]

            # Fix issues using the linting fixer
            try:
                fixed_content, issues = await self._linting_fixer.fix_code(
                    file_path=file_path, file_content=file_content, verbose=self._verbose
                )
            except Exception as e:
                return [
                    CodeIssue(
                        file_path=file_path,
                        line_number=0,
                        column=0,
                        message=f"Linting failed: {e!s}",
                        severity=IssueSeverity.HIGH,
                        rule_id="linting-error",
                        category="error",
                        fix=None,
                    )
                ]

            # Write the fixed content back to the file if it changed
            if fixed_content != file_content:
                try:
                    from pathlib import Path as _Path
                    with _Path(file_path).open("w", encoding="utf-8") as f:
                        f.write(fixed_content)

                    # Use logging instead of print
                    if self._verbose:
                        import logging as _logging
                        _logging.getLogger(__name__).info(
                            "Fixed %d issues in %s", len(issues), file_path
                        )
                except Exception as e:
                    # If we can't write the file, log it and continue
                    issues.append(
                        CodeIssue(
                            file_path=file_path,
                            line_number=0,
                            column=0,
                            message=f"Failed to write fixes to file: {e!s}",
                            severity=IssueSeverity.HIGH,
                            rule_id="write-error",
                            category="error",
                            fix=None,
                        )
                    )

            return issues

        except FileNotFoundError:
            raise  # Re-raise file not found errors

        except PermissionError:
            raise  # Re-raise permission errors

        except Exception as e:
            # For any other unexpected errors, return an error issue
            if self._verbose:
                import logging as _logging
                _logging.getLogger(__name__).exception(
                    "Unexpected error fixing issues in %s: %s", file_path, e
                )
            return [
                CodeIssue(
                    file_path=file_path,
                    line_number=0,
                    column=0,
                    message=f"Unexpected error: {e!s}",
                    severity=IssueSeverity.HIGH,
                    rule_id="unexpected-error",
                    category="error",
                    fix=None,
                )
            ]
