"""Direct test for VolumeConfig validation."""
from pathlib import Path
import sys

# Add project root to path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("\n=== Direct VolumeConfig Test ===\n")

# Import VolumeConfig directly from its module
print("1. Importing VolumeConfig...")
try:
    from autopr.agents.agents import VolumeConfig
    print(f"✅ Successfully imported VolumeConfig from {VolumeConfig.__module__}")
except Exception as e:
    print(f"❌ Failed to import VolumeConfig: {e}")
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

print("\n2. Testing VolumeConfig initialization...")
for name, volume, config, should_pass in test_cases:
    try:
        print(f"\nTesting with {name}...")
        config_obj = VolumeConfig(volume=volume, config=config)
        result = config_obj.config.get("enable_ai_agents")
        if should_pass:
            print(f"✅ Passed: {name} -> {result} (type: {type(result).__name__})")
        else:
            print(f"❌ Unexpectedly passed: {name} -> {result} (type: {type(result).__name__})")
    except Exception as e:
        if should_pass:
            print(f"❌ Failed: {name} -> {e}")
        else:
            print(f"✅ Correctly failed validation: {name} -> {e}")

print("\n3. Testing VolumeConfig with direct attribute access...")
try:
    config = VolumeConfig(volume=500, config={"enable_ai_agents": True})
    print(f"✅ Direct access: config.enable_ai_agents = {config.enable_ai_agents}")
except Exception as e:
    print(f"❌ Failed direct access: {e}")

print("\n=== Test Complete ===\n")
