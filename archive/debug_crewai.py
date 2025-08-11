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
        print("\n=== Importing modules ===")
        from autopr.actions.quality_engine.models import QualityInputs
        from autopr.actions.quality_engine.volume_mapping import get_volume_config
        from autopr.agents.crew import AutoPRCrew

        print("\n=== Testing volume mapping ===")
        volume = 500
        config = get_volume_config(volume)
        print(f"Volume config for {volume}:", config)
        print("enable_ai_agents type:", type(config["enable_ai_agents"]).__name__)

        print("\n=== Testing QualityInputs creation ===")
        inputs = QualityInputs()
        print("Default QualityInputs:", inputs.dict())

        print("\n=== Testing AutoPRCrew instantiation ===")
        crew = AutoPRCrew(llm_model="gpt-4")
        print("✅ Successfully instantiated AutoPRCrew")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Debugging CrewAI instantiation...")
    if debug_crew_instantiation():
        print("\n✅ Debug completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Debug failed")
        sys.exit(1)
