#!/usr/bin/env python3
"""Unit tests for volume control system"""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture(scope="module")
def volume_knob_classes():
    """Import volume knob classes with proper path setup."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "volume-control"))
    try:
        from volume_knob import CommitVolumeKnob, DevVolumeKnob, VolumeKnob
        return CommitVolumeKnob, DevVolumeKnob, VolumeKnob
    except ImportError as e:
        pytest.skip(f"Could not import volume_knob module: {e}")


class TestVolumeKnob:
    """Test the VolumeKnob class."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.original_cwd = Path.cwd()
        os.chdir(self.temp_dir)
        
        # Create .vscode directory for settings tests
        (self.temp_dir / ".vscode").mkdir(exist_ok=True)

    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_volume_knob_initialization(self, volume_knob_classes):
        """Test VolumeKnob initialization."""
        _, _, VolumeKnob = volume_knob_classes
        knob = VolumeKnob("test")
        assert knob.knob_type == "test"
        assert knob.config_file.name == ".volume-test.json"
        assert knob.get_volume() == 0  # Default volume when no config exists

    def test_volume_settings_low_volume(self, volume_knob_classes):
        """Test volume settings for low volume."""
        _, _, VolumeKnob = volume_knob_classes
        knob = VolumeKnob("test")
        knob.set_volume(100)
        
        # Verify volume was set correctly
        assert knob.get_volume() == 100
        assert knob.get_volume_level() == "QUIET"
        assert knob.get_volume_description() == "Basic syntax only"
        
        # Verify config file was created
        assert knob.config_file.exists()
        
        # Verify config file content
        with open(knob.config_file, 'r') as f:
            config = json.load(f)
        assert config["volume"] == 100

    def test_volume_settings_high_volume(self, volume_knob_classes):
        """Test volume settings for high volume."""
        _, _, VolumeKnob = volume_knob_classes
        knob = VolumeKnob("test")
        knob.set_volume(800)
        
        # Verify volume was set correctly
        assert knob.get_volume() == 800
        assert knob.get_volume_level() == "LOUD"
        assert knob.get_volume_description() == "Extreme checks"
        
        # Verify config file was created
        assert knob.config_file.exists()

    def test_volume_settings_disabled_tools(self, volume_knob_classes):
        """Test volume settings with disabled tools."""
        _, _, VolumeKnob = volume_knob_classes
        knob = VolumeKnob("test")
        knob.set_volume(0)
        
        # Verify volume was set correctly
        assert knob.get_volume() == 0
        assert knob.get_volume_level() == "OFF"
        assert knob.get_volume_description() == "No linting/checks"
        
        # Verify config file was created
        assert knob.config_file.exists()

    def test_volume_validation(self, volume_knob_classes):
        """Test volume validation."""
        _, _, VolumeKnob = volume_knob_classes
        knob = VolumeKnob("test")
        
        # Test volume clamping to valid range
        knob.set_volume(-1)
        assert knob.get_volume() == 0
        
        knob.set_volume(1001)
        assert knob.get_volume() == 1000
        
        # Test volume rounding to multiples of 5
        knob.set_volume(123)
        assert knob.get_volume() == 120
        
        knob.set_volume(127)
        assert knob.get_volume() == 125

    def test_volume_level_descriptions(self, volume_knob_classes):
        """Test volume level descriptions."""
        _, _, VolumeKnob = volume_knob_classes
        knob = VolumeKnob("test")
        
        # Test various volume levels
        test_cases = [
            (0, "OFF", "No linting/checks"),
            (25, "ULTRA QUIET", "Only critical errors"),
            (75, "QUIET", "Basic syntax only"),
            (150, "LOW", "Basic formatting"),
            (250, "MEDIUM-LOW", "Standard formatting"),
            (350, "MEDIUM", "Standard + imports"),
            (450, "MEDIUM-HIGH", "Enhanced checks"),
            (550, "HIGH", "Strict mode"),
            (650, "VERY HIGH", "Very strict"),
            (750, "LOUD", "Extreme checks"),
            (850, "VERY LOUD", "Maximum strictness"),
            (950, "MAXIMUM", "Nuclear mode"),
        ]
        
        for volume, expected_level, expected_description in test_cases:
            knob.set_volume(volume)
            assert knob.get_volume_level() == expected_level
            assert knob.get_volume_description() == expected_description

    def test_volume_up_down_methods(self, volume_knob_classes):
        """Test volume_up and volume_down methods (backward compatibility)."""
        _, _, VolumeKnob = volume_knob_classes
        knob = VolumeKnob("test")
        
        # These methods are no-op for backward compatibility
        # They should not raise errors
        knob.volume_up()
        knob.volume_up(5)
        knob.volume_down()
        knob.volume_down(3)
        
        # Volume should remain at default
        assert knob.get_volume() == 0

    def test_config_file_persistence(self, volume_knob_classes):
        """Test that volume settings persist across instances."""
        _, _, VolumeKnob = volume_knob_classes
        knob1 = VolumeKnob("test")
        knob1.set_volume(250)
        
        # Create new instance
        knob2 = VolumeKnob("test")
        assert knob2.get_volume() == 250

    def test_invalid_config_file_handling(self, volume_knob_classes):
        """Test handling of invalid config files."""
        _, _, VolumeKnob = volume_knob_classes
        knob = VolumeKnob("test")
        
        # Create invalid JSON file
        with open(knob.config_file, 'w') as f:
            f.write("invalid json")
        
        # Should return 0 for invalid JSON
        assert knob.get_volume() == 0
        
        # Create config with missing volume key
        with open(knob.config_file, 'w') as f:
            json.dump({"other_key": "value"}, f)
        
        # Should return 0 for missing volume key
        assert knob.get_volume() == 0


class TestDevVolumeKnob:
    """Test the DevVolumeKnob class."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.original_cwd = Path.cwd()
        os.chdir(self.temp_dir)

    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_dev_volume_knob_initialization(self, volume_knob_classes):
        """Test DevVolumeKnob initialization."""
        _, DevVolumeKnob, _ = volume_knob_classes
        knob = DevVolumeKnob()
        assert knob.knob_type == "dev"
        assert knob.config_file.name == ".volume-dev.json"

    def test_dev_volume_functionality(self, volume_knob_classes):
        """Test DevVolumeKnob functionality."""
        _, DevVolumeKnob, _ = volume_knob_classes
        knob = DevVolumeKnob()
        
        # Test volume setting
        knob.set_volume(300)
        assert knob.get_volume() == 300
        assert knob.get_volume_level() == "MEDIUM-LOW"
        assert knob.get_volume_description() == "Standard formatting"


class TestCommitVolumeKnob:
    """Test the CommitVolumeKnob class."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.original_cwd = Path.cwd()
        os.chdir(self.temp_dir)

    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_commit_volume_knob_initialization(self, volume_knob_classes):
        """Test CommitVolumeKnob initialization."""
        CommitVolumeKnob, _, _ = volume_knob_classes
        knob = CommitVolumeKnob()
        assert knob.knob_type == "commit"
        assert knob.config_file.name == ".volume-commit.json"

    def test_commit_volume_functionality(self, volume_knob_classes):
        """Test CommitVolumeKnob functionality."""
        CommitVolumeKnob, _, _ = volume_knob_classes
        knob = CommitVolumeKnob()
        
        # Test volume setting
        knob.set_volume(500)
        assert knob.get_volume() == 500
        assert knob.get_volume_level() == "MEDIUM-HIGH"
        assert knob.get_volume_description() == "Enhanced checks"


class TestVolumeController:
    """Test VolumeController functionality (simulated)."""
    
    def test_volume_controller_simulation(self, volume_knob_classes):
        """Test VolumeController simulation since it doesn't exist yet."""
        # Create both knobs
        CommitVolumeKnob, DevVolumeKnob, _ = volume_knob_classes
        dev_knob = DevVolumeKnob()
        commit_knob = CommitVolumeKnob()
        
        # Test initial volumes (should be 0 when no config exists)
        assert dev_knob.get_volume() == 0
        assert commit_knob.get_volume() == 0
        
        # Test setting different volumes
        dev_knob.set_volume(50)
        commit_knob.set_volume(200)
        
        assert dev_knob.get_volume() == 50
        assert commit_knob.get_volume() == 200
        
        # Test volume levels
        assert dev_knob.get_volume_level() == "ULTRA QUIET"
        assert commit_knob.get_volume_level() == "LOW"
