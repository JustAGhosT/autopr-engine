"""Minimal test script to verify AutoPRCrew import and instantiation."""

from pathlib import Path
import sys

# Add project root to Python path
project_root = str(Path(__file__).parent.resolve())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now try to import and instantiate AutoPRCrew
try:
    print("Attempting to import AutoPRCrew...")
    from autopr.agents.crew import AutoPRCrew

    print("✅ Successfully imported AutoPRCrew")

    print("\nAttempting to instantiate AutoPRCrew...")
    crew = AutoPRCrew()
    print("✅ Successfully instantiated AutoPRCrew")

except Exception as e:
    print(f"\n❌ Error: {e}", file=sys.stderr)
    import traceback

    traceback.print_exc()
    sys.exit(1)
