"""Debug script for CrewAI boolean validation issue."""

from pathlib import Path
import sys


# Add project root to Python path
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def debug_crew_instantiation():
    """Debug the AutoPRCrew instantiation process."""
    try:
        # Import with debug prints
        from autopr.actions.quality_engine.models import QualityInputs
        from autopr.actions.quality_engine.volume_mapping import get_volume_config
        from autopr.agents.crew import AutoPRCrew

        volume = 500
        get_volume_config(volume)

        QualityInputs()

        AutoPRCrew(llm_model="gpt-4")
        return True

    except Exception:
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    if debug_crew_instantiation():
        sys.exit(0)
    else:
        sys.exit(1)
