"""Simple test file to diagnose import issues."""

from pathlib import Path
import sys
from unittest.mock import patch


# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def test_imports():
    """Test that we can import the required modules."""
    with patch("codeflow_engine.agents.crew.get_llm_provider_manager"):
        from codeflow_engine.agents.crew import AutoPRCrew

        assert AutoPRCrew is not None


def test_volume_imports():
    """Test that we can import volume-related modules."""
    from codeflow_engine.utils.volume_utils import get_volume_level_name

    assert get_volume_level_name(500) == "Balanced"
