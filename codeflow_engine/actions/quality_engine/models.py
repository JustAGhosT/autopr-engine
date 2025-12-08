"""
Quality Engine Data Models
"""

import logging
from typing import Any

import pydantic

# (Removed unused ActionInputs import)
from codeflow_engine.utils.volume_utils import QualityMode, get_volume_config


logger = logging.getLogger(__name__)


class QualityInputs(pydantic.BaseModel):
    """Input parameters for quality engine operations

    The volume parameter (0-1000) can be used to automatically configure quality settings:
    - 0-199: Ultra-fast mode with minimal checks
    - 200-399: Fast mode with essential tools
    - 400-599: Smart mode with balanced checks
    - 600-799: Comprehensive mode with all tools
    - 800-1000: AI-enhanced mode with maximum analysis
    """

    mode: QualityMode = QualityMode.SMART
    files: list[str] | None = None
    max_fixes: int = 50
    max_issues: int = 100  # Maximum issues to report before stopping
    enable_ai_agents: bool = True
    config_path: str = "pyproject.toml"
    verbose: bool = False
    ai_provider: str | None = None
    ai_model: str | None = None
    volume: int | None = pydantic.Field(
        None,
        ge=0,
        le=1000,
        description="Volume level (0-1000) that automatically configures quality settings",
    )

    # Auto-fix parameters
    auto_fix: bool = False
    fix_types: list[str] | None = None
    dry_run: bool = False

    def apply_volume_settings(self, volume: int | None = None) -> None:
        """Apply volume-based settings to configure quality analysis."""
        if volume is None:
            volume = self.volume or 500

        # Clamp volume to valid range
        volume = max(0, min(1000, volume))

        # Get volume configuration
        volume_config = get_volume_config(volume)

        # Apply volume-based settings
        self.mode = volume_config["mode"]
        self.max_fixes = volume_config.get("max_fixes", 50)
        self.enable_ai_agents = volume_config.get("enable_ai_agents", True)

        logger.info(
            "Applied volume settings - volume=%d, mode=%s, max_fixes=%d, enable_ai_agents=%s",
            volume,
            self.mode,
            self.max_fixes,
            self.enable_ai_agents,
        )


class ToolResult(pydantic.BaseModel):
    """Results from a single quality tool execution"""

    issues: list[dict[str, Any]]
    files_with_issues: list[str]
    summary: str
    execution_time: float


class QualityOutputs(pydantic.BaseModel):
    """Output from quality engine operations"""

    success: bool
    total_issues_found: int
    total_issues_fixed: int
    files_modified: list[str]
    issues_by_tool: dict[str, list[Any]]
    files_by_tool: dict[str, list[str]]
    tool_execution_times: dict[str, float]
    summary: str
    ai_enhanced: bool
    ai_summary: str | None = None

    # Auto-fix results
    auto_fix_applied: bool = False
    fix_summary: str | None = None
    fix_errors: list[str] | None = None
