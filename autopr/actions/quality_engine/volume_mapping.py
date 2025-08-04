"""
Volume to Quality Mode Mapping

Maps volume levels (0-1000) to QualityEngine quality modes and configurations.
"""

from enum import Enum
from typing import Any, Dict, Tuple, Optional

from .models import QualityMode


class VolumeLevel(Enum):
    """Named volume levels for better readability"""
    SILENT = 0
    QUIET = 250
    MODERATE = 500
    HIGH = 750
    MAX = 1000


def volume_to_quality_mode(volume: int) -> Tuple[QualityMode, Dict[str, Any]]:
    """
    Map a volume level (0-1000) to a QualityMode and configuration.
    
    Args:
        volume: Volume level from 0 to 1000
        
    Returns:
        Tuple of (QualityMode, config_dict) where config_dict contains tool-specific settings
        
    Raises:
        ValueError: If volume is outside 0-1000 range
    """
    if not 0 <= volume <= 1000:
        raise ValueError(f"Volume must be between 0 and 1000, got {volume}")
    
    # Base configuration that applies to all modes
    base_config: Dict[str, Any] = {
        "max_fixes": max(1, volume // 20),  # 0-50 fixes based on volume
        "max_issues": max(10, volume // 10),  # 10-100 issues based on volume
        "enable_ai_agents": bool(volume > 200),
    }
    
    # Map volume ranges to quality modes
    if volume == 0:
        return QualityMode.ULTRA_FAST, {
            **base_config,
            "enable_ai_agents": False,
            "max_fixes": 0,  # No fixes in silent mode
        }
    elif volume < 200:
        return QualityMode.ULTRA_FAST, base_config
    elif volume < 400:
        return QualityMode.FAST, base_config
    elif volume < 600:
        return QualityMode.SMART, base_config
    elif volume < 800:
        return QualityMode.COMPREHENSIVE, base_config
    else:
        return QualityMode.AI_ENHANCED, {
            **base_config,
            "enable_ai_agents": True,
            "max_fixes": 100,  # More aggressive fixes at max volume
        }


def get_volume_level_name(volume: int) -> str:
    """Get a human-readable name for a volume level"""
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
    
    Returns a dictionary that can be used to update QualityInputs.
    """
    quality_mode, config = volume_to_quality_mode(volume)
    return {
        "mode": quality_mode,
        **config
    }
