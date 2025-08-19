"""Minimal test script to diagnose import issues."""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    # Try importing AutoPRCrew
    pass

except Exception:
    import traceback

    traceback.print_exc()

try:
    # Try importing volume mapping
    pass

except Exception:
    import traceback

    traceback.print_exc()
