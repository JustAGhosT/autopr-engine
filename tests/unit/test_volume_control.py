#!/usr/bin/env python3
"""Unit tests for volume control system"""

import json
from pathlib import Path
import shutil
import tempfile

import pytest

from scripts.volume_control.volume_knob import VolumeController, VolumeKnob


class TestVolumeKnob:
    """Test the VolumeKnob class."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.original_cwd = Path.cwd()
        self.temp_dir.chdir()

    def teardown_method(self):
        """Clean up test environment."""
        self.original_cwd.chdir()
        shutil.rmtree(self.temp_dir)

    def test_volume_knob_initialization(self):
        """Test VolumeKnob initialization."""
        knob = VolumeKnob("test")
        assert knob.knob_name == "test"
        assert knob.current_volume == 0

    def test_volume_settings_low_volume(self):
        """Test volume settings for low volume."""
        knob = VolumeKnob("test")
        knob.apply_settings_for_volume(100)

        # Check VS Code settings
        settings_path = Path(".vscode/settings.json")
        assert settings_path.exists()

        with settings_path.open() as f:
            settings = json.load(f)

        assert not settings.get("python.enabled", True)
        assert settings.get("git.enabled")
        assert not settings.get("yaml.validate", True)

    def test_volume_settings_high_volume(self):
        """Test volume settings for high volume."""
        knob = VolumeKnob("test")
        knob.apply_settings_for_volume(800)

        # Check VS Code settings
        settings_path = Path(".vscode/settings.json")
        assert settings_path.exists()

        with settings_path.open() as f:
            settings = json.load(f)

        assert settings.get("python.enabled")
        assert settings.get("git.enabled")
        assert settings.get("yaml.validate")

    def test_volume_settings_disabled_tools(self):
        """Test volume settings with disabled tools."""
        knob = VolumeKnob("test")
        knob.apply_settings_for_volume(0)

        # Check VS Code settings
        settings_path = Path(".vscode/settings.json")
        assert settings_path.exists()

        with settings_path.open() as f:
            settings = json.load(f)

        assert not settings.get("python.enabled", True)
        assert settings.get("python.languageServer") == "None"

    def test_volume_validation(self):
        """Test volume validation."""
        knob = VolumeKnob("test")

        # Test invalid volumes
        with pytest.raises(ValueError):
            knob.set_volume(-1)

        with pytest.raises(ValueError):
            knob.set_volume(1001)

    def test_volume_controller(self):
        """Test VolumeController."""
        controller = VolumeController()

        # Test initial volumes
        assert controller.dev_knob.get_volume() == 50
        assert controller.commit_knob.get_volume() == 200

        # Test active tools
        dev_tools = controller.dev_knob.config_loader.get_active_tools(50)
        commit_tools = controller.commit_knob.config_loader.get_active_tools(200)

        assert "python" in dev_tools
        assert "yaml" in commit_tools
