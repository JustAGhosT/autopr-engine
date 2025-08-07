"""
Quality Engine Data Models
"""

import logging
from typing import Any, Optional

import pydantic

from autopr.actions.base import ActionInputs
from autopr.utils.volume_utils import QualityMode, get_volume_config

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
        description="Volume level (0-1000) that automatically configures quality settings"
    )
    
    def apply_volume_settings(self, volume: int | None = None) -> None:
        """Apply volume-based configuration to this instance.
        
        Args:
            volume: Volume level (0-1000). If None, uses self.volume.
            
        This will update the instance attributes based on the volume level:
        - mode: QualityMode based on volume
        - max_fixes: Number of fixes to apply (0-100)
        - max_issues: Maximum issues to report (10-1000)
        - enable_ai_agents: Whether to use AI agents (True for volume >= 200)
        """
        if volume is None:
            volume = self.volume
            
        if volume is None or volume < 0 or volume > 1000:
            logger.warning("Invalid volume level: %s. Must be between 0-1000.", volume)
            return
            
        try:
            # Get volume-based configuration
            volume_config = get_volume_config(volume)
            logger.debug("Applying volume settings for volume %d: %s", volume, volume_config)
            
            # Update instance attributes with volume-based configuration
            for key, value in volume_config.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                    logger.debug("Set %s = %s", key, value)
                else:
                    logger.warning("Volume config key '%s' does not exist in %s", 
                                key, self.__class__.__name__)
                    
        except Exception as e:
            logger.exception("Failed to apply volume settings: %s", str(e))
            # Fall back to default values based on volume ranges
            if volume < 200:
                self.mode = QualityMode.ULTRA_FAST
                self.max_fixes = 0
                self.max_issues = 10
                self.enable_ai_agents = False
            elif volume < 400:
                self.mode = QualityMode.FAST
                self.max_fixes = 10
                self.max_issues = 50
                self.enable_ai_agents = False
            elif volume < 600:
                self.mode = QualityMode.SMART
                self.max_fixes = 25
                self.max_issues = 100
                self.enable_ai_agents = True
            elif volume < 800:
                self.mode = QualityMode.COMPREHENSIVE
                self.max_fixes = 50
                self.max_issues = 250
                self.enable_ai_agents = True
            else:
                self.mode = QualityMode.AI_ENHANCED
                self.max_fixes = 100
                self.max_issues = 500
                self.enable_ai_agents = True
                
            logger.warning("Falling back to default volume settings for volume %d: %s", 
                         volume, self.mode.value)


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
