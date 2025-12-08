"""Integration test for VolumeConfig and QualityMode."""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# Import the modules we need to test
try:
    from codeflow_engine.agents.base.volume_config import VolumeConfig
    from codeflow_engine.enums import QualityMode

except ImportError:
    raise


def test_volume_config():
    """Test VolumeConfig initialization and quality mode mapping."""

    # Test default initialization
    config = VolumeConfig()

    # Test volume clamping
    config = VolumeConfig(volume=1500)  # Should clamp to 1000
    assert config.volume == 1000, f"Expected volume 1000, got {config.volume}"

    # Test quality mode mapping
    test_cases = [
        (0, QualityMode.ULTRA_FAST),
        (100, QualityMode.FAST),
        (200, QualityMode.FAST),
        (400, QualityMode.SMART),
        (600, QualityMode.COMPREHENSIVE),
        (800, QualityMode.AI_ENHANCED),
        (1000, QualityMode.AI_ENHANCED),
    ]

    for volume, expected_mode in test_cases:
        config = VolumeConfig(volume=volume)
        assert (
            config.quality_mode == expected_mode
        ), f"Expected {expected_mode} for volume {volume}, got {config.quality_mode}"

    # Test boolean conversion in config
    config = VolumeConfig(
        volume=500,
        config={
            "enable_ai_agents": "true",
            "allow_updates": "yes",
            "is_verified": "1",
            "has_issues": "false",
        },
    )

    assert config.config["enable_ai_agents"] is True
    assert config.config["allow_updates"] is True
    assert config.config["is_verified"] is True
    assert config.config["has_issues"] is False


if __name__ == "__main__":
    test_volume_config()
