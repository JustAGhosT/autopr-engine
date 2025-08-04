"""
Quality Engine Data Models
"""

from enum import Enum
from typing import Any

import pydantic


class QualityMode(Enum):
    """Operating mode for quality checks"""

    ULTRA_FAST = "ultra-fast"
    FAST = "fast"
    COMPREHENSIVE = "comprehensive"
    AI_ENHANCED = "ai_enhanced"
    SMART = "smart"


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
        description="Volume level (0-1000) that automatically configures quality settings"
    )
    
    def apply_volume_settings(self, volume: int | None = None) -> None:
        """Apply volume-based configuration to this input object.
        
        Args:
            volume: If provided, overrides self.volume for this call
        """
        if volume is None:
            volume = self.volume
            
        if volume is None or volume < 0 or volume > 1000:
            return
            
        from .volume_mapping import get_volume_config
        volume_config = get_volume_config(volume)
        
        # Update self with volume-based configuration
        for key, value in volume_config.items():
            if hasattr(self, key):
                setattr(self, key, value)


class ToolResult(pydantic.BaseModel):
    """Results from a single quality tool execution"""

    issues: list[dict[str, Any]]
    files_with_issues: list[str]
    summary: str
    execution_time: float


class QualityOutputs(pydantic.BaseModel):
    """Complete output from quality engine operations"""

    success: bool
    total_issues_found: int
    total_issues_fixed: int
    files_modified: list[str]
    issues_by_tool: dict[str, list[dict[str, Any]]] = {}
    files_by_tool: dict[str, list[str]] = {}
    summary: str
    tool_execution_times: dict[str, float] = {}
    ai_enhanced: bool = False
    ai_summary: str | None = None
