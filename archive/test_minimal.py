"""Minimal test script to verify imports without pytest."""

import os
from pathlib import Path
import sys

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set environment variable to control logging
os.environ["AUTOPR_LOG_LEVEL"] = "DEBUG"

print("Python path:")
for p in sys.path:
    print(f"  {p}")

try:
    print("\nAttempting to import from autopr.agents.crew...")
    from autopr.agents.crew import AutoPRCrew

    print("✅ Successfully imported AutoPRCrew")
    print(f"AutoPRCrew class: {AutoPRCrew}")
except Exception as e:
    print(f"❌ Failed to import AutoPRCrew: {e}")
    import traceback

    traceback.print_exc()

try:
    print("\nAttempting to import volume mapping...")
    from autopr.actions.quality_engine.volume_mapping import get_volume_level_name

    print("✅ Successfully imported get_volume_level_name")
    print(f"get_volume_level_name(500): {get_volume_level_name(500)}")
except Exception as e:
    print(f"❌ Failed to import get_volume_level_name: {e}")
    import traceback

    traceback.print_exc()
