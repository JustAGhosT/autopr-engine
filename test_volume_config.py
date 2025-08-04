"""
Minimal test script to verify VolumeConfig boolean handling.
"""
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from autopr.agents.agents import VolumeConfig
from autopr.actions.quality_engine.engine import QualityMode

def test_volume_config():
    """Test VolumeConfig initialization and boolean handling."""
    print("Testing VolumeConfig...")
    
    # Test default initialization
    print("\n1. Testing default initialization...")
    config = VolumeConfig()
    print(f"Default config: volume={config.volume}, mode={config.quality_mode}")
    print(f"Config dict: {config.config}")
    assert isinstance(config.volume, int)
    assert isinstance(config.quality_mode, QualityMode)
    assert isinstance(config.config, dict)
    assert 'enable_ai_agents' in config.config
    assert isinstance(config.config['enable_ai_agents'], bool)
    
    # Test custom volume
    print("\n2. Testing custom volume...")
    for volume in [0, 250, 500, 750, 1000]:
        config = VolumeConfig(volume=volume)
        print(f"Volume {volume} -> Mode: {config.quality_mode}, "
              f"AI Agents: {config.config['enable_ai_agents']}")
        assert isinstance(config.quality_mode, QualityMode)
        assert isinstance(config.config['enable_ai_agents'], bool)
    
    # Test explicit config override
    print("\n3. Testing explicit config override...")
    custom_config = {
        'enable_ai_agents': 'true'  # Should be converted to bool
    }
    config = VolumeConfig(volume=500, config=custom_config)
    print(f"Config with overrides: {config.config}")
    assert config.config['enable_ai_agents'] is True  # Should be converted to bool
    
    print("\nAll VolumeConfig tests passed!")

if __name__ == "__main__":
    test_volume_config()
