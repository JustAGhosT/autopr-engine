"""
DEPRECATED: This module is deprecated and will be removed in a future release.
Please use autopr.utils.volume_utils instead.

Volume-based quality control configuration.

This module provides functions to map volume levels (0-1000) to quality modes
and configurations that control the behavior of the quality engine.
"""

import warnings
from enum import Enum
from typing import Any, TypedDict

# Import from the new location
from autopr.utils.volume_utils import get_volume_config as _get_volume_config
from autopr.utils.volume_utils import get_volume_level_name as _get_volume_level_name
from autopr.utils.volume_utils import volume_to_quality_mode as _volume_to_quality_mode

# Show deprecation warning
warnings.warn(
    "The 'volume_mapping' module is deprecated and will be removed in a future release. "
    "Please use 'autopr.utils.volume_utils' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export functions from the new location
get_volume_config = _get_volume_config
volume_to_quality_mode = _volume_to_quality_mode
get_volume_level_name = _get_volume_level_name

# Import QualityMode for backward compatibility
from autopr.utils.volume_utils import QualityMode

# Volume range constants for consistent behavior across functions
VOLUME_RANGES = {
    "SILENT": (0, 0),  # No output, no fixes
    "QUIET": (1, 199),  # Minimal output, few fixes
    "MODERATE": (200, 399),  # Balanced output and fixes
    "BALANCED": (400, 599),  # Default balanced mode
    "THOROUGH": (600, 799),  # More thorough checks
    "MAXIMUM": (800, 1000),  # Maximum thoroughness
}


class VolumeRange(TypedDict):
    min: int
    max: int


class VolumeLevel(Enum):
    """Named volume levels for better readability"""

    SILENT = 0
    QUIET = 100
    MODERATE = 300
    BALANCED = 500
    THOROUGH = 700
    MAXIMUM = 1000


def _validate_volume(volume: int) -> None:
    """Validate that volume is within the valid range (0-1000).

    Args:
        volume: Volume level to validate

    Raises:
        ValueError: If volume is outside 0-1000 range
    """
    if not isinstance(volume, int) or not 0 <= volume <= 1000:
        raise ValueError(f"Volume must be an integer between 0 and 1000, got {volume}")


def _get_volume_range(volume: int) -> str:
    """Get the volume range name for a given volume level.

    Args:
        volume: Volume level from 0 to 1000

    Returns:
        Name of the volume range (e.g., 'SILENT', 'QUIET')

    Raises:
        ValueError: If volume is outside 0-1000 range or not an integer
    """
    _validate_volume(volume)

    for name, (min_vol, max_vol) in VOLUME_RANGES.items():
        if min_vol <= volume <= max_vol:
            return name
    return "BALANCED"  # Default fallback


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
    # This will raise ValueError if volume is invalid
    volume_range = _get_volume_range(volume)

    # Base configuration that applies to all modes
    base_config: dict[str, Any] = {
        "max_fixes": max(1, volume // 20) if volume > 0 else 0,  # 0-50 fixes based on volume
        "max_issues": max(10, volume // 10),  # 10-100 issues based on volume
        "enable_ai_agents": volume > VOLUME_RANGES["MODERATE"][0],
    }

    # Map volume ranges to quality modes
    if volume_range == "SILENT":
        return QualityMode.ULTRA_FAST, {
            "max_fixes": 0,
            "max_issues": 10,  # Minimum issues to report
            "enable_ai_agents": False,
        }
    if volume_range == "QUIET":
        # Align with tests: 100-volume should map to FAST
        return QualityMode.FAST, base_config
    if volume_range == "MODERATE":
        return QualityMode.FAST, base_config
    if volume_range == "BALANCED":
        return QualityMode.SMART, base_config
    if volume_range == "THOROUGH":
        return QualityMode.COMPREHENSIVE, base_config
    # MAXIMUM
    return QualityMode.AI_ENHANCED, {
        **base_config,
        "max_fixes": 100,  # More aggressive fixes at max volume
        "enable_ai_agents": True,
    }


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
    # _get_volume_range will validate the volume
    volume_range = _get_volume_range(volume)
    return volume_range.title()


def get_volume_config(volume: int) -> dict[str, Any]:
    """
    Get the complete configuration for a given volume level.

    Args:
        volume: Volume level from 0 to 1000

    Returns:
        Dictionary with 'mode' and configuration settings that can be used to update QualityInputs

    Raises:
        ValueError: If volume is outside 0-1000 range or not an integer
    """
    # volume_to_quality_mode will validate the volume through _get_volume_range
    quality_mode, config = volume_to_quality_mode(volume)
    return {"mode": quality_mode, **config}
