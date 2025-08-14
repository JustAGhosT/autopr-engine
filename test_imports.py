"""Minimal test script to verify imports."""

from pathlib import Path
import sys

print("=== Testing Imports ===")
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path}")

# Add project root to path
project_root = str(Path(__file__).parent.absolute())
print(f"\nProject root: {project_root}")

if project_root not in sys.path:
    print(f"Adding {project_root} to sys.path")
    sys.path.insert(0, project_root)

print("\nAttempting imports...")
try:
    print("\n1. Testing autopr.enums import...")
    from autopr.enums import QualityMode

    print(f"✅ Successfully imported QualityMode: {QualityMode}")

    print("\n2. Testing autopr.utils.volume_utils import...")
    from autopr.utils.volume_utils import volume_to_quality_mode

    print(f"✅ Successfully imported volume_to_quality_mode: {volume_to_quality_mode}")

    print("\n3. Testing autopr.agents.base.volume_config import...")
    from autopr.agents.base.volume_config import VolumeConfig

    print(f"✅ Successfully imported VolumeConfig: {VolumeConfig}")

    print("\n✅ All imports successful!")

except ImportError as e:
    print(f"\n❌ Import failed: {e}")
    raise
