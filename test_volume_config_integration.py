"""Integration test for VolumeConfig and QualityMode."""
from pathlib import Path
import sys

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("Testing VolumeConfig and QualityMode integration...")

# Import the modules we need to test
try:
    from autopr.agents.base.volume_config import VolumeConfig
    from autopr.enums import QualityMode
    print("✅ Successfully imported VolumeConfig and QualityMode")
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    raise

def test_volume_config():
    """Test VolumeConfig initialization and quality mode mapping."""
    print("\nTesting VolumeConfig...")

    # Test default initialization
    config = VolumeConfig()
    print(f"✅ Default volume: {config.volume}")
    print(f"✅ Default quality mode: {config.quality_mode}")
    print(f"✅ Default config: {config.config}")

    # Test volume clamping
    config = VolumeConfig(volume=1500)  # Should clamp to 1000
    assert config.volume == 1000, f"Expected volume 1000, got {config.volume}"
    print("✅ Volume clamping works")

    # Test quality mode mapping
    test_cases = [
        (0, QualityMode.ULTRA_FAST),
        (100, QualityMode.ULTRA_FAST),
        (200, QualityMode.FAST),
        (400, QualityMode.SMART),
        (600, QualityMode.COMPREHENSIVE),
        (800, QualityMode.AI_ENHANCED),
        (1000, QualityMode.AI_ENHANCED),
    ]

    for volume, expected_mode in test_cases:
        config = VolumeConfig(volume=volume)
        assert config.quality_mode == expected_mode, \
            f"Expected {expected_mode} for volume {volume}, got {config.quality_mode}"
    print("✅ Volume to quality mode mapping works")

    # Test boolean conversion in config
    config = VolumeConfig(volume=500, config={
        "enable_ai_agents": "true",
        "allow_updates": "yes",
        "is_verified": "1",
        "has_issues": "false",
    })

    assert config.config["enable_ai_agents"] is True
    assert config.config["allow_updates"] is True
    assert config.config["is_verified"] is True
    assert config.config["has_issues"] is False
    print("✅ Boolean conversion in config works")

    print("✅ All VolumeConfig tests passed!")

if __name__ == "__main__":
    test_volume_config()
