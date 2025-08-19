"""
Minimal test script to verify VolumeConfig boolean handling.
"""

from pathlib import Path
import sys

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from autopr.agents.agents import VolumeConfig
from autopr.utils.volume_utils import QualityMode


def test_volume_config():
    """Test VolumeConfig initialization and boolean handling."""

    # Test default initialization
    config = VolumeConfig()
    assert isinstance(config.volume, int)
    assert isinstance(config.quality_mode, QualityMode)
    assert isinstance(config.config, dict)
    assert "enable_ai_agents" in config.config
    assert isinstance(config.config["enable_ai_agents"], bool)

    # Test custom volume
    for volume in [0, 250, 500, 750, 1000]:
        config = VolumeConfig(volume=volume)
        assert isinstance(config.quality_mode, QualityMode)
        assert isinstance(config.config["enable_ai_agents"], bool)

    # Test explicit config override
    custom_config = {"enable_ai_agents": "true"}  # Should be converted to bool
    config = VolumeConfig(volume=500, config=custom_config)
    assert config.config["enable_ai_agents"] is True  # Should be converted to bool


if __name__ == "__main__":
    test_volume_config()
