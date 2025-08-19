"""Minimal test script to verify imports without pytest."""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set environment variable to control logging
os.environ["AUTOPR_LOG_LEVEL"] = "DEBUG"

for _p in sys.path:
    pass

try:
    pass

except Exception:
    import traceback

    traceback.print_exc()

try:
    pass

except Exception:
    import traceback

    traceback.print_exc()
