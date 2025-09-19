"""Simple test for VolumeConfig validation."""

from pathlib import Path
import sys


# Add project root to path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from autopr.agents.agents import VolumeConfig

    try:
        config = VolumeConfig(volume=500, config={"enable_ai_agents": True})
    except Exception:
        raise

    try:
        config = VolumeConfig(volume=500, config={"enable_ai_agents": "true"})
    except Exception:
        raise


except Exception:
    import traceback

    traceback.print_exc()
    sys.exit(1)
