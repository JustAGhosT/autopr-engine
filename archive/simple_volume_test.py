"""Simple test for VolumeConfig validation."""

import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("\n=== Starting VolumeConfig Test ===\n")
print("1. Importing VolumeConfig...")
try:
    from autopr.agents.agents import VolumeConfig

    print("✅ Successfully imported VolumeConfig")

    print("\n2. Testing VolumeConfig with boolean True...")
    try:
        config = VolumeConfig(volume=500, config={"enable_ai_agents": True})
        print(
            f"✅ Success! enable_ai_agents = {config.config.get('enable_ai_agents')} (type: {type(config.config.get('enable_ai_agents'))})"
        )
    except Exception as e:
        print(f"❌ Failed with boolean True: {e}")
        raise

    print("\n3. Testing VolumeConfig with string 'true'...")
    try:
        config = VolumeConfig(volume=500, config={"enable_ai_agents": "true"})
        print(
            f"✅ Success! enable_ai_agents = {config.config.get('enable_ai_agents')} (type: {type(config.config.get('enable_ai_agents'))})"
        )
    except Exception as e:
        print(f"❌ Failed with string 'true': {e}")
        raise

    print("\n✅ All tests passed!")

except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
