"""
Volume-related utility functions for AutoPR.

This module provides volume-based configuration and utilities that can be imported
without creating circular dependencies between modules.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


@dataclass
class VolumeThresholds:
    """Configuration for volume level thresholds and mappings."""

    # Volume thresholds for quality modes
    ULTRA_FAST_MAX = 100
    FAST_MAX = 300
    SMART_MAX = 600
    COMPREHENSIVE_MAX = 800
    AI_ENHANCED_MIN = 800

    # Volume thresholds for AI agents
    AI_AGENTS_THRESHOLD = 200

    # Volume thresholds for fix types
    BASIC_FIXES_MAX = 300
    LOGGING_FIXES_MIN = 300
    STANDARD_FIXES_MIN = 500
    ADVANCED_FIXES_MIN = 700
    STRICT_FIXES_MIN = 800
    MAXIMUM_FIXES_MIN = 900


# Global instance for consistent behavior
VOLUME_THRESHOLDS = VolumeThresholds()


class VolumeLevel(Enum):
    """Named volume levels for better readability"""

    SILENT = 0
    QUIET = 100
    MODERATE = 300
    BALANCED = 500
    THOROUGH = 700
    MAXIMUM = 1000


def get_volume_level_name(volume: int) -> str:
    """
    Get a human-readable name for a volume level.

    Args:
        volume: Volume level from 0 to 1000

    Returns:
        Human-readable name of the volume level (e.g., 'Silent', 'Quiet')

    Note:
        Volume is clamped to 0-1000 range if outside bounds
    """
    MIN_VOLUME = 0
    MAX_VOLUME = 1000

    # Clamp volume to valid range (consistent with get_volume_config behavior)
    clamped_volume = max(MIN_VOLUME, min(MAX_VOLUME, volume))

    if clamped_volume == 0:
        return "Silent"
    # Match the legacy behavior from volume_mapping.py
    if clamped_volume <= 199:
        return "Quiet"
    if clamped_volume <= 399:
        return "Moderate"
    if clamped_volume <= 599:
        return "Balanced"
    if clamped_volume <= 799:
        return "Thorough"
    return "Maximum"


def get_volume_config(volume: int) -> dict[str, Any]:
    """
    Get the complete configuration for a given volume level.

    Args:
        volume: Volume level from 0 to 1000

    Returns:
        Dictionary with 'mode' and configuration settings that can be used to update QualityInputs

    Note:
        Negative volumes are clamped to 0, volumes above 1000 are clamped to 1000
    """
    # Clamp volume to valid range (legacy behavior)
    MIN_VOLUME = 0
    MAX_VOLUME = 1000
    clamped_volume = max(MIN_VOLUME, min(MAX_VOLUME, volume))

    quality_mode, config = volume_to_quality_mode(clamped_volume)
    return {"mode": quality_mode, **config}


def volume_to_quality_mode(volume: int) -> tuple[QualityMode, dict[str, Any]]:
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
        msg = f"Volume must be between 0 and 1000, got {volume}"
        raise ValueError(msg)

    # Base configuration that applies to all modes
    # Use legacy max_fixes calculation: volume // 20 (legacy behavior)
    legacy_max_fixes = 0 if volume == 0 else max(1, volume // 20)
    base_config = {
        "max_fixes": min(MAX_FIXES, legacy_max_fixes),
        "max_issues": min(MAX_ISSUES, max(MIN_ISSUES, volume // 5)),
        "enable_ai_agents": volume >= VOLUME_THRESHOLDS.AI_AGENTS_THRESHOLD,
        "ai_fixer_enabled": volume >= VOLUME_THRESHOLDS.AI_AGENTS_THRESHOLD,
        "ai_fixer_max_fixes": min(MAX_FIXES, legacy_max_fixes),
        "ai_fixer_issue_types": _get_ai_fixer_issue_types(volume),
    }

    # Get the quality mode based on volume thresholds
    if volume < VOLUME_THRESHOLDS.ULTRA_FAST_MAX:
        quality_mode = QualityMode.ULTRA_FAST
    elif volume < VOLUME_THRESHOLDS.FAST_MAX:
        quality_mode = QualityMode.FAST
    elif volume < VOLUME_THRESHOLDS.SMART_MAX:
        quality_mode = QualityMode.SMART
    elif volume < VOLUME_THRESHOLDS.COMPREHENSIVE_MAX:
        quality_mode = QualityMode.COMPREHENSIVE
    else:
        quality_mode = QualityMode.AI_ENHANCED

    # Special case for minimum volume - ultra minimal checks
    if volume == 0:
        return quality_mode, {
            **base_config,
            "max_fixes": 0,  # No fixes in silent mode
            "max_issues": 1,  # Minimum issues to report
            "enable_ai_agents": False,
        }
    if quality_mode == QualityMode.AI_ENHANCED:
        return (
            quality_mode,
            {
                **base_config,
                "max_fixes": 500,  # More aggressive fixes at max volume (increased for maximum AI fixing)
                "enable_ai_agents": True,
            },
        )
    return quality_mode, base_config


def _get_ai_fixer_issue_types(volume: int) -> list[str]:
    """Get AI fixer issue types based on volume level."""
    # Start with basic, safe fixes
    basic_types = ["F401", "F841", "F541"]  # Unused imports, variables, f-strings

    # Add more aggressive fixes at higher volumes
    if volume >= VOLUME_THRESHOLDS.LOGGING_FIXES_MIN:
        basic_types.extend(["G004", "TRY401"])  # Logging issues
    if volume >= VOLUME_THRESHOLDS.STANDARD_FIXES_MIN:
        basic_types.extend(["E501", "E741"])  # Line length, ambiguous names
    if volume >= VOLUME_THRESHOLDS.ADVANCED_FIXES_MIN:
        basic_types.extend(
            ["E722", "B001", "F821"]
        )  # Exception handling, undefined names
    if volume >= VOLUME_THRESHOLDS.STRICT_FIXES_MIN:
        basic_types.extend(["F811"])  # Redefined imports
    if volume >= VOLUME_THRESHOLDS.MAXIMUM_FIXES_MIN:
        basic_types.extend(["*"])  # All issues at maximum volume

    return basic_types
