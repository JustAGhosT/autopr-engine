"""Test Pydantic validation for VolumeConfig."""

import logging
import os
import sys
from pathlib import Path

# Set up debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from pydantic import ValidationError

# Debug: Print Python path and current working directory
logger.debug(f"Python path: {sys.path}")
logger.debug(f"Current working directory: {os.getcwd()}")

# Try to import VolumeConfig with error handling
try:
    from autopr.agents.agents import VolumeConfig

    logger.debug("Successfully imported VolumeConfig")
except ImportError as e:
    logger.exception(f"Failed to import VolumeConfig: {e}")
    raise


def test_volume_config_boolean_validation():
    """Test that VolumeConfig properly validates boolean fields."""
    # Test with explicit boolean values
    config = VolumeConfig(volume=500)
    assert isinstance(config.config["enable_ai_agents"], bool)

    # Test with string 'true'/'false'
    with pytest.raises(ValidationError):
        VolumeConfig(volume=500, config={"enable_ai_agents": "true"})

    with pytest.raises(ValidationError):
        VolumeConfig(volume=500, config={"enable_ai_agents": "false"})

    # Test with integer 0/1
    with pytest.raises(ValidationError):
        VolumeConfig(volume=500, config={"enable_ai_agents": 1})

    with pytest.raises(ValidationError):
        VolumeConfig(volume=500, config={"enable_ai_agents": 0})

    # Test with actual booleans (should work)
    config = VolumeConfig(volume=500, config={"enable_ai_agents": True})
    assert config.config["enable_ai_agents"] is True

    config = VolumeConfig(volume=500, config={"enable_ai_agents": False})
    assert config.config["enable_ai_agents"] is False


def test_volume_config_initialization():
    """Test VolumeConfig initialization and type conversion."""
    # Test volume clamping
    config = VolumeConfig(volume=1500)
    assert config.volume == 1000

    config = VolumeConfig(volume=-100)
    assert config.volume == 0

    # Test quality_mode inference
    config = VolumeConfig(volume=0)
    assert config.quality_mode is not None

    # Test config merging
    custom_config = {"some_setting": 123}
    config = VolumeConfig(volume=500, config=custom_config)
    assert "some_setting" in config.config
    assert "enable_ai_agents" in config.config  # Should still have default settings
