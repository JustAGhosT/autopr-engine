"""Comprehensive pytest tests for VolumeConfig validation."""

from pathlib import Path
import sys
from typing import Any

import pytest  # type: ignore[import-not-found]

print("=== Starting test_volume_config_simple.py ===")
print(f"Python path: {sys.path}")

# Add project root to path
project_root = str(Path(__file__).parent.parent.absolute())
print(f"Project root: {project_root}")

if project_root not in sys.path:
    print(f"Adding {project_root} to sys.path")
    sys.path.insert(0, project_root)

print("Attempting to import VolumeConfig...")
try:
    from autopr.agents.base.volume_config import VolumeConfig

    print("Successfully imported VolumeConfig")
except ImportError as e:
    print(f"Import error: {e}")
    raise

# Test cases for VolumeConfig initialization
TEST_CASES = [
    # (test_name, volume, config_dict, expected_ai_agents, should_pass)
    ("boolean True", 500, {"enable_ai_agents": True}, True, True),
    ("boolean False", 500, {"enable_ai_agents": False}, False, True),
    ("string 'true'", 500, {"enable_ai_agents": "true"}, True, True),
    ("string 'false'", 500, {"enable_ai_agents": "false"}, False, True),
    ("string 'True'", 500, {"enable_ai_agents": "True"}, True, True),
    ("string 'False'", 500, {"enable_ai_agents": "False"}, False, True),
    ("integer 1", 500, {"enable_ai_agents": 1}, True, True),
    ("integer 0", 500, {"enable_ai_agents": 0}, False, True),
    ("string '1'", 500, {"enable_ai_agents": "1"}, True, True),
    ("string '0'", 500, {"enable_ai_agents": "0"}, False, True),
    ("None value", 500, {"enable_ai_agents": None}, None, False),
    ("empty string", 500, {"enable_ai_agents": ""}, False, True),
    ("invalid string", 500, {"enable_ai_agents": "invalid"}, False, True),
]


@pytest.mark.parametrize("test_name,volume,config_dict,expected_ai_agents,should_pass", TEST_CASES)
def test_volume_config_initialization(
    test_name: str,
    volume: int,
    config_dict: dict[str, Any],
    expected_ai_agents: bool,
    should_pass: bool,
):
    """Test VolumeConfig initialization with various config values."""
    print(f"\n=== Testing: {test_name} ===")
    print(f"Volume: {volume}")
    print(f"Config: {config_dict}")
    print(f"Expected AI Agents: {expected_ai_agents}")
    print(f"Should pass: {should_pass}")

    if not should_pass:
        with pytest.raises(ValueError):
            VolumeConfig(volume=volume, config=config_dict)
        print("✅ Correctly failed validation")
        return

    # Should pass validation
    if test_name == "invalid string":
        # Expect a specific conversion warning and capture it
        with pytest.warns(UserWarning, match="Could not convert value 'invalid' to boolean, defaulting to False"):
            config = VolumeConfig(volume=volume, config=config_dict)
    else:
        config = VolumeConfig(volume=volume, config=config_dict)
    assert config.volume == volume
    assert config.config.get("enable_ai_agents") is expected_ai_agents
    print(f"✅ Config: {config.config}")


def test_volume_config_defaults():
    """Test VolumeConfig default values."""
    print("\n=== Testing Default Values ===")
    config = VolumeConfig()

    # Check default volume
    assert config.volume == 500  # Default volume
    print(f"✅ Default volume: {config.volume}")

    # Check default config
    assert isinstance(config.config, dict)
    print(f"✅ Default config: {config.config}")

    # Check enable_ai_agents default is True
    assert config.config.get("enable_ai_agents") is True
    print("✅ Default enable_ai_agents is True")


def test_volume_config_volume_validation():
    """Test volume parameter validation."""
    print("\n=== Testing Volume Validation ===")

    # Test volume clamping
    config = VolumeConfig(volume=2000)  # Should clamp to 1000
    assert config.volume == 1000
    print(f"✅ Volume clamped from 2000 to {config.volume}")

    config = VolumeConfig(volume=-100)  # Should clamp to 0
    assert config.volume == 0
    print(f"✅ Volume clamped from -100 to {config.volume}")

    # Test invalid volume types
    with pytest.raises(ValueError):
        VolumeConfig(volume="invalid")  # type: ignore
    print("✅ Correctly rejected invalid volume type")
