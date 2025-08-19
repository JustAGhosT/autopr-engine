"""
Tests for volume mapping functionality in AutoPR Engine.
"""

import pytest

from autopr.enums import QualityMode
from autopr.utils.volume_utils import (
    VolumeLevel,
    get_volume_config,
    get_volume_level_name,
    volume_to_quality_mode,
)


class TestVolumeMapping:
    """Test suite for volume mapping functionality."""

    @pytest.mark.parametrize(
        ("volume", "expected_mode", "expected_config_keys"),
        [
            # Test minimum volume (0)
            (
                0,
                QualityMode.ULTRA_FAST,
                {"enable_ai_agents", "max_fixes", "max_issues"},
            ),
            # Test quiet volume (250)
            (250, QualityMode.FAST, {"enable_ai_agents", "max_fixes", "max_issues"}),
            # Test moderate volume (500)
            (500, QualityMode.SMART, {"enable_ai_agents", "max_fixes", "max_issues"}),
            # Test high volume (750)
            (
                750,
                QualityMode.COMPREHENSIVE,
                {"enable_ai_agents", "max_fixes", "max_issues"},
            ),
            # Test maximum volume (1000)
            (
                1000,
                QualityMode.AI_ENHANCED,
                {"enable_ai_agents", "max_fixes", "max_issues"},
            ),
        ],
    )
    def test_volume_to_quality_mode(self, volume, expected_mode, expected_config_keys):
        """Test mapping volume to quality mode and config."""
        mode, config = volume_to_quality_mode(volume)
        assert mode == expected_mode
        assert set(config.keys()) == expected_config_keys

        # Verify config values are reasonable
        assert isinstance(config["enable_ai_agents"], bool)
        assert isinstance(config["max_fixes"], int)
        assert isinstance(config["max_issues"], int)

        if volume == 0:
            assert not config["enable_ai_agents"]
            assert config["max_fixes"] == 0
        else:
            assert config["max_fixes"] > 0
            assert config["max_issues"] > 0

    @pytest.mark.parametrize(
        ("volume", "expected_name"),
        [
            (0, "Silent"),
            (100, "Quiet"),
            (250, "Moderate"),  # 200-399
            (300, "Moderate"),  # 200-399
            (400, "Balanced"),  # 400-599
            (500, "Balanced"),  # 400-599
            (600, "Thorough"),  # 600-799
            (750, "Thorough"),  # 600-799
            (800, "Maximum"),  # 800-1000
            (1000, "Maximum"),  # 800-1000
        ],
    )
    def test_get_volume_level_name(self, volume, expected_name):
        """Test getting human-readable volume level names."""
        assert get_volume_level_name(volume) == expected_name

    def test_volume_to_quality_mode_invalid_volume(self):
        """Test that invalid volume levels raise ValueError."""
        with pytest.raises(ValueError):
            volume_to_quality_mode(-1)
        with pytest.raises(ValueError):
            volume_to_quality_mode(1001)

    @pytest.mark.parametrize(
        ("volume", "expected_mode"),
        [
            (0, QualityMode.ULTRA_FAST),
            (300, QualityMode.SMART),  # Updated to canonical mapping
            (500, QualityMode.SMART),
            (700, QualityMode.COMPREHENSIVE),
            (900, QualityMode.AI_ENHANCED),
        ],
    )
    def test_get_volume_config(self, volume, expected_mode):
        """Test getting complete volume configuration."""
        config = get_volume_config(volume)
        assert config["mode"] == expected_mode
        assert "max_fixes" in config
        assert "max_issues" in config
        assert "enable_ai_agents" in config

    def test_volume_level_enum(self):
        """Test VolumeLevel enum values."""
        assert VolumeLevel.SILENT.value == 0
        assert (
            VolumeLevel.QUIET.value == 100
        )  # Matches actual implementation (1-199 range)
        assert VolumeLevel.MODERATE.value == 300  # 200-399 range
        assert VolumeLevel.BALANCED.value == 500  # 400-599 range
        assert VolumeLevel.THOROUGH.value == 700  # 600-799 range
        assert VolumeLevel.MAXIMUM.value == 1000  # 800-1000 range
