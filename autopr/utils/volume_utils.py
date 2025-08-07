"""
Volume-related utility functions for AutoPR.

This module provides volume-based configuration and utilities that can be imported
without creating circular dependencies between modules.
"""
from enum import Enum
from typing import Any, Dict, Tuple


class QualityMode(Enum):
    """Operating mode for quality checks"""

    ULTRA_FAST = "ultra-fast"
    FAST = "fast"
    COMPREHENSIVE = "comprehensive"
    AI_ENHANCED = "ai_enhanced"
    SMART = "smart"

# Volume threshold constants for consistent behavior
AI_AGENTS_THRESHOLD = 200  # Volume level at which to enable AI agents
MIN_FIXES = 1  # Minimum number of fixes to apply
MAX_FIXES = 100  # Maximum number of fixes to apply
MIN_ISSUES = 10  # Minimum number of issues to report


def get_volume_level_name(volume: int) -> str:
    """
    Get a human-readable name for a volume level.
    
    Args:
        volume: Volume level from 0 to 1000
        
    Returns:
        Human-readable name of the volume level (e.g., 'Silent', 'Quiet')
        
    Raises:
        ValueError: If volume is outside 0-1000 range or not an integer
    """
    if not 0 <= volume <= 1000:
        raise ValueError(f"Volume must be between 0 and 1000, got {volume}")
        
    if volume == 0:
        return "Silent"
    elif volume < 200:
        return "Quiet"
    elif volume < 400:
        return "Moderate"
    elif volume < 600:
        return "Balanced"
    elif volume < 800:
        return "Thorough"
    else:
        return "Maximum"


def get_volume_config(volume: int) -> Dict[str, Any]:
    """
    Get the complete configuration for a given volume level.
    
    Args:
        volume: Volume level from 0 to 1000
        
    Returns:
        Dictionary with 'mode' and configuration settings that can be used to update QualityInputs
        
    Raises:
        ValueError: If volume is outside 0-1000 range or not an integer
    """
    quality_mode, config = volume_to_quality_mode(volume)
    return {
        "mode": quality_mode,
        **config
    }


def volume_to_quality_mode(volume: int) -> Tuple[QualityMode, Dict[str, Any]]:
    """
    Map a volume level (0-1000) to a QualityMode and configuration.
    
    Args:
        volume: Volume level from 0 to 1000
        
    Returns:
        Tuple of (QualityMode, config_dict) where config_dict contains tool-specific settings
        
    Raises:
        ValueError: If volume is outside 0-1000 range or not an integer
    """
    if not 0 <= volume <= 1000:
        raise ValueError(f"Volume must be between 0 and 1000, got {volume}")

    # Base configuration that applies to all modes
    base_config: Dict[str, Any] = {
        # Scale fixes more gradually (1-100) based on volume
        "max_fixes": min(MAX_FIXES, max(MIN_FIXES, volume // 10)),
        # Scale issues from MIN_ISSUES to 100 based on volume
        "max_issues": max(MIN_ISSUES, volume // 10),
        # Enable AI agents at the MODERATE threshold (200+)
        "enable_ai_agents": volume >= AI_AGENTS_THRESHOLD,
    }
    
    # Map volume ranges to quality modes
    if volume == 0:
        return QualityMode.ULTRA_FAST, {
            "max_fixes": 0,
            "max_issues": 10,  # Minimum issues to report
            "enable_ai_agents": False,
        }
    elif volume < 200:
        return QualityMode.ULTRA_FAST, base_config
    elif volume < 400:
        return QualityMode.FAST, base_config
    elif volume < 600:
        return QualityMode.SMART, base_config
    elif volume < 800:
        return QualityMode.COMPREHENSIVE, base_config
    else:  # 800-1000
        return QualityMode.AI_ENHANCED, {
            **base_config,
            "max_fixes": 100,  # More aggressive fixes at max volume
            "enable_ai_agents": True,
        }
