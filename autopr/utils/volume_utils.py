"""
Volume-related utility functions for AutoPR.

This module provides volume-based configuration and utilities that can be imported
without creating circular dependencies between modules.
"""

from enum import Enum
from typing import Any

from autopr.enums import QualityMode


# Volume threshold constants for consistent behavior
AI_AGENTS_THRESHOLD = 200  # Volume level at which to enable AI agents
MIN_FIXES = 1  # Minimum number of fixes to apply
MAX_FIXES = (
    500  # Maximum number of fixes to apply (increased for more aggressive AI fixing)
)
MIN_ISSUES = 10  # Minimum number of issues to report
MAX_ISSUES = (
    9999  # Maximum number of issues to report (increased for comprehensive analysis)
)


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

    Raises:
        ValueError: If volume is outside 0-1000 range or not an integer
    """
    MIN_VOLUME = 0
    MAX_VOLUME = 1000
    if not MIN_VOLUME <= volume <= MAX_VOLUME:
        msg = f"Volume must be between {MIN_VOLUME} and {MAX_VOLUME}, got {volume}"
        raise ValueError(msg)

    if volume == 0:
        return "Silent"
    # Match the legacy behavior from volume_mapping.py
    if volume <= 199:
        return "Quiet"
    if volume <= 399:
        return "Moderate"
    if volume <= 599:
        return "Balanced"
    if volume <= 799:
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
    MIN_VOLUME = 0
    MAX_VOLUME = 1000
    if not MIN_VOLUME <= volume <= MAX_VOLUME:
        msg = f"Volume must be between {MIN_VOLUME} and {MAX_VOLUME}, got {volume}"
        raise ValueError(msg)

    # Base configuration that applies to all modes
    # Use legacy max_fixes calculation: volume // 20 (legacy behavior)
    legacy_max_fixes = 0 if volume == 0 else max(1, volume // 20)
    base_config = {
        "max_fixes": min(MAX_FIXES, legacy_max_fixes),
        "max_issues": min(MAX_ISSUES, max(MIN_ISSUES, volume // 5)),
        "enable_ai_agents": volume >= AI_AGENTS_THRESHOLD,
        "ai_fixer_enabled": volume >= AI_AGENTS_THRESHOLD,
        "ai_fixer_max_fixes": min(MAX_FIXES, legacy_max_fixes),
        "ai_fixer_issue_types": _get_ai_fixer_issue_types(volume),
    }

    # Get the quality mode based on volume
    quality_mode = QualityMode.from_volume(volume)

    # Special case for minimum volume - ultra minimal checks
    if volume == MIN_VOLUME:
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
    if volume >= 300:
        basic_types.extend(["G004", "TRY401"])  # Logging issues
    if volume >= 500:
        basic_types.extend(["E501", "E741"])  # Line length, ambiguous names
    if volume >= 700:
        basic_types.extend(
            ["E722", "B001", "F821"]
        )  # Exception handling, undefined names
    if volume >= 800:
        basic_types.extend(["F811"])  # Redefined imports
    if volume >= 900:
        basic_types.extend(["*"])  # All issues at maximum volume

    return basic_types
