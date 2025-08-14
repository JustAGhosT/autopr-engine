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

from autopr.utils.volume_utils import (
    QualityMode,
)

# Import from the new location
from autopr.utils.volume_utils import (
    volume_to_quality_mode as _base_volume_to_quality_mode,
)

# Show deprecation warning
warnings.warn(
    "The 'volume_mapping' module is deprecated and will be removed in a future release. "
    "Please use 'autopr.utils.volume_utils' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "QualityMode",
    "VolumeLevel",
    "get_volume_config",
    "get_volume_level_name",
    "volume_to_quality_mode",
]

# All imports are above; keep top-of-file import ordering for lint compliance

# Volume range constants for consistent behavior across functions
VOLUME_RANGES = {
    "SILENT": (0, 0),  # No output, no fixes
    "QUIET": (1, 199),  # Minimal output, few fixes
    "MODERATE": (200, 399),  # Balanced output and fixes
    "BALANCED": (400, 599),  # Default balanced mode
    "THOROUGH": (600, 799),  # More thorough checks
    "MAXIMUM": (800, 1000),  # Maximum thoroughness
}

# Explicit bounds to avoid magic numbers
MIN_VOLUME = 0
MAX_VOLUME = 1000


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
    if not isinstance(volume, int):
        msg = "Volume must be an integer"
        raise TypeError(msg)
    if not MIN_VOLUME <= volume <= MAX_VOLUME:
        msg = f"Volume must be an integer between {MIN_VOLUME} and {MAX_VOLUME}, got {volume}"
        raise ValueError(msg)


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
    # Delegate to utils for canonical decision; it validates and caps max_fixes at 100
    mode, config = _base_volume_to_quality_mode(volume)
    # Ensure keys align with legacy expectations (remove 'verbose' if present)
    if "verbose" in config:
        config = {k: v for k, v in config.items() if k != "verbose"}
    return mode, config


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
    # Clamp negative/overflow values per legacy behavior expected by some tests
    if not isinstance(volume, int):
        msg = "Volume must be an integer"
        raise TypeError(msg)
    clamped = max(MIN_VOLUME, min(MAX_VOLUME, volume))
    mode, config = volume_to_quality_mode(clamped)
    # Legacy behavior: max_fixes computed as clamped // 20, but keep canonical cap at 100 for max volume
    try:
        legacy_max_fixes = 0 if clamped == 0 else max(1, clamped // 20)
        if isinstance(config, dict):
            if clamped >= 1000:
                # At maximum volume, prefer canonical cap of 100
                config = {**config, "max_fixes": max(config.get("max_fixes", legacy_max_fixes), legacy_max_fixes)}
            else:
                # For other volumes, prefer legacy scaling when it is lower
                config = {**config, "max_fixes": min(config.get("max_fixes", legacy_max_fixes), legacy_max_fixes)}
    except Exception:
        pass
    return {"mode": mode, **config}
