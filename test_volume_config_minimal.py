"""Minimal test for VolumeConfig import and basic functionality."""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("Attempting to import VolumeConfig...")
try:
    from autopr.agents.base.volume_config import VolumeConfig

    print("✅ Successfully imported VolumeConfig")

    # Test basic functionality
    print("\nTesting VolumeConfig initialization:")
    config = VolumeConfig()
    print(f"✅ Volume: {config.volume}")
    print(f"✅ Quality Mode: {config.quality_mode}")
    print(f"✅ Config: {config.config}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
