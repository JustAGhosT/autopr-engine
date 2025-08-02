#!/usr/bin/env python3
"""
Unit tests for volume control system
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add volume-control to path
test_dir = Path(__file__).parent
scripts_dir = test_dir.parent.parent / "scripts" / "volume-control"
sys.path.insert(0, str(scripts_dir))

from volume_knob import VolumeKnob
from config_loader import VolumeConfigLoader


class TestVolumeControl(unittest.TestCase):
    """Test volume control functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create .vscode directory
        Path(".vscode").mkdir(exist_ok=True)
        
        # Create initial VS Code settings
        self.vscode_settings_file = Path(".vscode/settings.json")
        self.initial_settings = {
            "python.enabled": False,
            "git.enabled": False,
            "yaml.validate": False,
            "problems.decorations.enabled": False
        }
        with open(self.vscode_settings_file, 'w') as f:
            json.dump(self.initial_settings, f, indent=2)
    
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_volume_0_to_50_transition(self):
        """Test volume transition from 0 to 50"""
        print("\n=== Testing Volume 0 to 50 Transition ===")
        
        # Create volume knob
        knob = VolumeKnob("dev")
        
        # Start at volume 0
        knob.set_volume(0)
        
        # Verify volume 0 settings
        with open(self.vscode_settings_file, 'r') as f:
            settings = json.load(f)
        
        # At volume 0, everything should be disabled
        self.assertFalse(settings.get("python.enabled", True))
        self.assertFalse(settings.get("git.enabled", True))
        self.assertFalse(settings.get("yaml.validate", True))
        self.assertFalse(settings.get("problems.decorations.enabled", True))
        print("✓ Volume 0: All tools disabled")
        
        # Transition to volume 50
        knob.set_volume(50)
        
        # Verify volume 50 settings
        with open(self.vscode_settings_file, 'r') as f:
            settings = json.load(f)
        
        # At volume 50, git, python, and problems should be enabled
        self.assertTrue(settings.get("python.enabled"))
        self.assertTrue(settings.get("git.enabled"))
        self.assertTrue(settings.get("problems.decorations.enabled"))
        
        # YAML should still be disabled (activates at volume 100)
        self.assertFalse(settings.get("yaml.validate", True))
        
        # Python should be in basic mode
        self.assertEqual(settings.get("python.languageServer"), "Pylance")
        self.assertEqual(settings.get("python.analysis.typeCheckingMode"), "basic")
        self.assertFalse(settings.get("python.linting.enabled", True))
        
        print("✓ Volume 50: Git, Python (basic), Problems enabled")
        print("✓ Volume 50: YAML validation still disabled (correct)")
        
        # Verify active tools
        active_tools = knob.config_loader.get_active_tools(50)
        expected_active = {"git", "python", "problems"}
        actual_active = set(active_tools)
        
        self.assertEqual(actual_active, expected_active)
        print(f"✓ Active tools at volume 50: {sorted(active_tools)}")
    
    def test_volume_50_to_0_transition(self):
        """Test volume transition from 50 to 0"""
        print("\n=== Testing Volume 50 → 0 Transition ===")
        
        # Create volume knob
        knob = VolumeKnob("dev")
        
        # Start at volume 50
        knob.set_volume(50)
        
        # Verify volume 50 settings are active
        with open(self.vscode_settings_file, 'r') as f:
            settings = json.load(f)
        
        self.assertTrue(settings.get("python.enabled"))
        self.assertTrue(settings.get("git.enabled"))
        self.assertTrue(settings.get("problems.decorations.enabled"))
        print("✓ Volume 50: Tools correctly enabled")
        
        # Transition down to volume 0
        knob.set_volume(0)
        
        # Verify volume 0 settings
        with open(self.vscode_settings_file, 'r') as f:
            settings = json.load(f)
        
        # Everything should be disabled again
        self.assertFalse(settings.get("python.enabled", True))
        self.assertFalse(settings.get("git.enabled", True))
        self.assertFalse(settings.get("problems.decorations.enabled", True))
        
        # Python should be completely disabled
        self.assertEqual(settings.get("python.languageServer"), "None")
        self.assertFalse(settings.get("python.analysis.enabled", True))
        
        # Files should be treated as plaintext
        file_associations = settings.get("files.associations", {})
        self.assertEqual(file_associations.get("*.py"), "plaintext")
        
        print("✓ Volume 0: All tools disabled")
        print("✓ Volume 0: Python files treated as plaintext")
        
        # Verify no active tools
        active_tools = knob.config_loader.get_active_tools(0)
        self.assertEqual(len(active_tools), 0)
        print("✓ No active tools at volume 0")
    
    def test_volume_persistence(self):
        """Test that volume settings persist across instances"""
        print("\n=== Testing Volume Persistence ===")
        
        # Create first knob instance and set volume
        knob1 = VolumeKnob("dev")
        knob1.set_volume(50)
        
        # Create second knob instance (should load saved volume)
        knob2 = VolumeKnob("dev")
        
        # Verify volume was loaded correctly
        self.assertEqual(knob2.get_volume(), 50)
        print("✓ Volume 50 persisted across instances")
        
        # Verify config file exists and has correct content
        config_file = Path(".volume-dev.json")
        self.assertTrue(config_file.exists())
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        self.assertEqual(config["volume"], 50)
        self.assertEqual(config["knob_name"], "dev")
        print("✓ Volume config file correctly saved")
    
    def test_volume_validation(self):
        """Test volume validation rules"""
        print("\n=== Testing Volume Validation ===")
        
        knob = VolumeKnob("dev")
        
        # Test invalid ranges
        with self.assertRaises(ValueError):
            knob.set_volume(-1)  # Below minimum
        
        with self.assertRaises(ValueError):
            knob.set_volume(1001)  # Above maximum
        
        with self.assertRaises(ValueError):
            knob.set_volume(37)  # Not multiple of 5
        
        # Test valid values
        valid_volumes = [0, 5, 50, 500, 1000]
        for volume in valid_volumes:
            try:
                knob.set_volume(volume)
                self.assertEqual(knob.get_volume(), volume)
            except Exception as e:
                self.fail(f"Valid volume {volume} raised exception: {e}")
        
        print("✓ Volume validation working correctly")
    
    def test_config_loader_integration(self):
        """Test that config loader correctly loads all tool configurations"""
        print("\n=== Testing Config Loader Integration ===")
        
        loader = VolumeConfigLoader()
        
        # Verify essential tools are loaded
        expected_tools = {"git", "python", "yaml", "problems", "github-actions"}
        loaded_tools = set(loader.tools.keys())
        
        for tool in expected_tools:
            self.assertIn(tool, loaded_tools, f"Tool {tool} not loaded")
        
        print(f"✓ Loaded {len(loaded_tools)} tool configurations")
        
        # Test volume 0 settings
        vol_0_settings = loader.get_settings_for_volume(0)
        self.assertFalse(vol_0_settings.get("python.enabled", True))
        self.assertFalse(vol_0_settings.get("git.enabled", True))
        
        # Test volume 50 settings
        vol_50_settings = loader.get_settings_for_volume(50)
        self.assertTrue(vol_50_settings.get("python.enabled"))
        self.assertTrue(vol_50_settings.get("git.enabled"))
        self.assertFalse(vol_50_settings.get("yaml.validate", True))  # Still disabled
        
        print("✓ Config loader applying correct settings for each volume")
    
    def test_incremental_volume_changes(self):
        """Test incremental volume up/down operations"""
        print("\n=== Testing Incremental Volume Changes ===")
        
        knob = VolumeKnob("dev")
        knob.set_volume(0)
        
        # Test volume_up (should go 0 → 5 → 10 → ... → 50)
        for i in range(10):  # 10 steps of 5 = 50
            knob.volume_up()
        
        self.assertEqual(knob.get_volume(), 50)
        print("✓ Volume up: 0 → 50 in 10 steps")
        
        # Test volume_down (should go 50 → 45 → 40 → ... → 0)
        for i in range(10):  # 10 steps of 5 = 50
            knob.volume_down()
        
        self.assertEqual(knob.get_volume(), 0)
        print("✓ Volume down: 50 → 0 in 10 steps")
        
        # Test multi-step changes
        knob.volume_up(10)  # 10 steps = 50
        self.assertEqual(knob.get_volume(), 50)
        
        knob.volume_down(5)  # 5 steps = 25
        self.assertEqual(knob.get_volume(), 25)
        
        print("✓ Multi-step volume changes working correctly")


class TestVolumeControlIntegration(unittest.TestCase):
    """Integration tests for the complete volume control system"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create .vscode directory
        Path(".vscode").mkdir(exist_ok=True)
    
    def tearDown(self):
        """Clean up integration test environment"""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_0_to_50_workflow(self):
        """Test complete workflow from volume 0 to 50"""
        print("\n=== Integration Test: Complete 0→50 Workflow ===")
        
        # Simulate starting fresh (no existing settings)
        knob = VolumeKnob("dev")
        
        # Apply volume 0 (complete silence)
        knob.set_volume(0)
        
        # Verify complete silence
        with open(Path(".vscode/settings.json"), 'r') as f:
            settings = json.load(f)
        
        silence_checks = [
            ("python.enabled", False),
            ("git.enabled", False), 
            ("yaml.validate", False),
            ("github-actions.validate", False),
            ("problems.decorations.enabled", False)
        ]
        
        for setting, expected in silence_checks:
            actual = settings.get(setting, not expected)  # Default opposite for testing
            self.assertEqual(actual, expected, f"Setting {setting} should be {expected} at volume 0")
        
        print("✓ Volume 0: Complete silence verified")
        
        # Apply volume 50 (1 tick up)
        knob.set_volume(50)
        
        # Verify essential tools enabled
        with open(Path(".vscode/settings.json"), 'r') as f:
            settings = json.load(f)
        
        essential_checks = [
            ("python.enabled", True),
            ("git.enabled", True),
            ("problems.decorations.enabled", True),
            ("python.analysis.typeCheckingMode", "basic"),
            ("python.linting.enabled", False),  # No linting yet
            ("yaml.validate", False),  # Still silent
        ]
        
        for setting, expected in essential_checks:
            actual = settings.get(setting)
            self.assertEqual(actual, expected, f"Setting {setting} should be {expected} at volume 50")
        
        print("✓ Volume 50: Essential tools enabled, linting still silent")
        print("✓ Integration test passed: 0→50 workflow complete")


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(argv=[''], verbosity=2, exit=False)
