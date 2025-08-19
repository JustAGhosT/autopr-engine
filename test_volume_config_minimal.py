"""Minimal test for VolumeConfig import and basic functionality."""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from autopr.agents.base.volume_config import VolumeConfig

    # Test basic functionality
    config = VolumeConfig()

except Exception:
    import traceback

    traceback.print_exc()
