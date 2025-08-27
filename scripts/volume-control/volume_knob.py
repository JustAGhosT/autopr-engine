#!/usr/bin/env python3
"""
Volume Control Knob Classes

Provides VolumeKnob, CommitVolumeKnob, and DevVolumeKnob classes for managing
volume settings in the AutoPR system.
"""

import json
from pathlib import Path
from typing import Optional


class VolumeKnob:
    """Base class for volume control knobs."""

    def __init__(self, knob_type: str):
        self.knob_type = knob_type
        # Build path relative to this source file, then resolve to absolute path
        self.config_file = (
            Path(__file__).resolve().parent.parent.parent / f".volume-{knob_type}.json"
        )

    def get_volume(self) -> int:
        """Get current volume setting."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    return data.get("volume", 0)
            except (json.JSONDecodeError, KeyError):
                return 0
        return 0

    def set_volume(self, volume: int) -> None:
        """Set volume to specified value."""
        # Ensure volume is a multiple of 5
        volume = (volume // 5) * 5
        volume = max(0, min(1000, volume))  # Clamp to 0-1000

        data = {"volume": volume}
        with open(self.config_file, "w") as f:
            json.dump(data, f, indent=2)

    def volume_up(self, steps: int = 1) -> None:
        """Backward compatibility shim for volume_up method."""
        # No-op method to prevent AttributeError for existing callers
        pass

    def volume_down(self, steps: int = 1) -> None:
        """Backward compatibility shim for volume_down method."""
        # No-op method to prevent AttributeError for existing callers
        pass

    def get_volume_level(self) -> str:
        """Get volume level description."""
        volume = self.get_volume()
        if volume == 0:
            return "OFF"
        elif volume <= 50:
            return "ULTRA QUIET"
        elif volume <= 100:
            return "QUIET"
        elif volume <= 200:
            return "LOW"
        elif volume <= 300:
            return "MEDIUM-LOW"
        elif volume <= 400:
            return "MEDIUM"
        elif volume <= 500:
            return "MEDIUM-HIGH"
        elif volume <= 600:
            return "HIGH"
        elif volume <= 700:
            return "VERY HIGH"
        elif volume <= 800:
            return "LOUD"
        elif volume <= 900:
            return "VERY LOUD"
        else:
            return "MAXIMUM"

    def get_volume_description(self) -> str:
        """Get detailed volume description."""
        volume = self.get_volume()
        if volume == 0:
            return "No linting/checks"
        elif volume <= 50:
            return "Only critical errors"
        elif volume <= 100:
            return "Basic syntax only"
        elif volume <= 200:
            return "Basic formatting"
        elif volume <= 300:
            return "Standard formatting"
        elif volume <= 400:
            return "Standard + imports"
        elif volume <= 500:
            return "Enhanced checks"
        elif volume <= 600:
            return "Strict mode"
        elif volume <= 700:
            return "Very strict"
        elif volume <= 800:
            return "Extreme checks"
        elif volume <= 900:
            return "Maximum strictness"
        else:
            return "Nuclear mode"


class DevVolumeKnob(VolumeKnob):
    """Development environment volume control."""

    def __init__(self):
        super().__init__("dev")


class CommitVolumeKnob(VolumeKnob):
    """Commit volume control."""

    def __init__(self):
        super().__init__("commit")
