"""Minimal test script to verify imports."""

import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.absolute())

if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from autopr.agents.base.volume_config import VolumeConfig
    from autopr.enums import QualityMode
    from autopr.utils.volume_utils import volume_to_quality_mode


except ImportError:
    raise
