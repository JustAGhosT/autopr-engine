"""Test file to verify imports from the codebase."""

from unittest.mock import patch


def test_import_volume_config():
    """Test importing VolumeConfig from agents.py."""
    from autopr.agents.agents import VolumeConfig

    assert VolumeConfig is not None

    # Test basic initialization
    config = VolumeConfig(volume=500)
    assert config.volume == 500
    assert hasattr(config, "quality_mode")
    assert hasattr(config, "config")
    assert "enable_ai_agents" in config.config
    assert isinstance(config.config["enable_ai_agents"], bool)


def test_import_crew():
    """Test importing AutoPRCrew from crew.py."""
    from autopr.agents.crew import AutoPRCrew

    assert AutoPRCrew is not None

    # Test basic initialization with mocks
    with patch("autopr.agents.crew.get_llm_provider_manager"):
        crew = AutoPRCrew(llm_model="test-model")
        assert crew is not None


def test_import_volume_mapping():
    """Test importing from volume_utils.py."""
    from autopr.utils.volume_utils import get_volume_config, volume_to_quality_mode

    # Test volume mapping
    mode, config = volume_to_quality_mode(500)
    assert mode is not None
    assert isinstance(config, dict)
    assert "enable_ai_agents" in config
    assert isinstance(config["enable_ai_agents"], bool)

    # Test volume config
    config = get_volume_config(500)
    assert isinstance(config, dict)
    assert "enable_ai_agents" in config
    assert isinstance(config["enable_ai_agents"], bool)
