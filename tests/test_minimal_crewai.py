"""
Minimal test script to diagnose CrewAI integration test issues.
"""

from pathlib import Path
import sys

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def test_import_autopr_crew():
    """Test if we can import AutoPRCrew."""
    from autopr.agents.crew import AutoPRCrew
    assert AutoPRCrew is not None
    print("✅ Successfully imported AutoPRCrew")


def test_instantiate_autopr_crew():
    """Test if we can instantiate AutoPRCrew."""
    from autopr.agents.crew import AutoPRCrew
    crew = AutoPRCrew(llm_model="gpt-4")
    assert crew is not None
    print("✅ Successfully instantiated AutoPRCrew")


if __name__ == "__main__":
    print("Running minimal CrewAI integration tests...")
    import_result = test_import_autopr_crew()
    instantiate_result = False
    if import_result:
        instantiate_result = test_instantiate_autopr_crew()

    if import_result and instantiate_result:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)
