"""Minimal test script to diagnose import issues."""
from pathlib import Path
import sys

# Add the project root to the Python path
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    # Try importing AutoPRCrew
    from autopr.agents.crew import AutoPRCrew
    print("✅ Successfully imported AutoPRCrew")
    print(f"AutoPRCrew class: {AutoPRCrew}")
except Exception as e:
    print(f"❌ Failed to import AutoPRCrew: {e}")
    import traceback
    traceback.print_exc()

try:
    # Try importing volume mapping
    from autopr.actions.quality_engine.volume_mapping import get_volume_level_name
    print("\n✅ Successfully imported get_volume_level_name")
    print(f"get_volume_level_name(500): {get_volume_level_name(500)}")
except Exception as e:
    print(f"\n❌ Failed to import get_volume_level_name: {e}")
    import traceback
    traceback.print_exc()
