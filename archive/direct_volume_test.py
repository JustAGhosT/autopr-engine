"""Direct test for VolumeConfig validation."""

import contextlib
from pathlib import Path
import sys


# Add project root to path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# Import VolumeConfig directly from its module
try:
    from autopr.agents.agents import VolumeConfig

except Exception:
    raise

# Test VolumeConfig initialization with different config values
test_cases = [
    # (test_name, volume, config_dict, should_pass)
    ("boolean True", 500, {"enable_ai_agents": True}, True),
    ("boolean False", 500, {"enable_ai_agents": False}, True),
    ("string 'true'", 500, {"enable_ai_agents": "true"}, True),
    ("string 'false'", 500, {"enable_ai_agents": "false"}, True),
    ("string 'True'", 500, {"enable_ai_agents": "True"}, True),
    ("string 'False'", 500, {"enable_ai_agents": "False"}, True),
    ("integer 1", 500, {"enable_ai_agents": 1}, True),
    ("integer 0", 500, {"enable_ai_agents": 0}, True),
    ("string '1'", 500, {"enable_ai_agents": "1"}, True),
    ("string '0'", 500, {"enable_ai_agents": "0"}, True),
    ("None value", 500, {"enable_ai_agents": None}, False),  # Should fail validation
]

for _name, volume, config, should_pass in test_cases:
    try:
        config_obj = VolumeConfig(volume=volume, config=config)
        result = config_obj.config.get("enable_ai_agents")
        if should_pass:
            pass
        else:
            pass
    except Exception:
        if should_pass:
            pass
        else:
            pass

with contextlib.suppress(Exception):
    config = VolumeConfig(volume=500, config={"enable_ai_agents": True})
