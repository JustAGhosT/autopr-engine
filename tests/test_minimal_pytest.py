"""Minimal pytest test to diagnose import issues."""

import sys
from pathlib import Path


def test_import_paths():
    """Test that the Python path is set up correctly."""
    print("\nPython path in pytest:")
    for p in sys.path:
        print(f"  {p}")

    # Check if project root is in path
    project_root = str(Path(__file__).parent.parent.absolute())
    assert project_root in sys.path, f"Project root {project_root} not in sys.path"


def test_import_crew():
    """Test importing the crew module."""
    try:
        from autopr.agents.crew import AutoPRCrew

        assert AutoPRCrew is not None
        print("✅ Successfully imported AutoPRCrew in pytest")
    except Exception as e:
        print(f"❌ Failed to import AutoPRCrew in pytest: {e}")
        import traceback

        traceback.print_exc()
        raise


def test_import_volume_mapping():
    """Test importing the volume mapping module."""
    try:
        from autopr.actions.quality_engine.volume_mapping import get_volume_level_name

        assert get_volume_level_name(500) == "Balanced"
        print("✅ Successfully imported get_volume_level_name in pytest")
    except Exception as e:
        print(f"❌ Failed to import get_volume_level_name in pytest: {e}")
        import traceback

        traceback.print_exc()
        raise
