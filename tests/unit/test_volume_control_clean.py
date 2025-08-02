#!/usr/bin/env python3
"""
Unit tests for volume control system (Unicode-free version)
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
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
        print("PASS: Volume 0: All tools disabled")
        
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
        
        print("PASS: Volume 50: Git, Python (basic), Problems enabled")
        print("PASS: Volume 50: YAML validation still disabled (correct)")
        
        # Verify active tools
        active_tools = knob.config_loader.get_active_tools(50)
        expected_active = {"git", "python", "problems"}
        actual_active = set(active_tools)
        
        self.assertEqual(actual_active, expected_active)
        print(f"PASS: Active tools at volume 50: {sorted(active_tools)}")
    
    def test_volume_50_to_0_transition(self):
        """Test volume transition from 50 to 0"""
        print("\n=== Testing Volume 50 to 0 Transition ===")
        
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
        print("PASS: Volume 50: Tools correctly enabled")
        
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
        
        print("PASS: Volume 0: All tools disabled")
        print("PASS: Volume 0: Python files treated as plaintext")
        
        # Verify no active tools
        active_tools = knob.config_loader.get_active_tools(0)
        self.assertEqual(len(active_tools), 0)
        print("PASS: No active tools at volume 0")
    
    def test_volume_incremental_changes(self):
        """Test volume up and down operations"""
        print("\n=== Testing Incremental Volume Changes ===")
        
        knob = VolumeKnob("dev")
        knob.set_volume(0)
        
        # Test volume_up (should go 0 -> 5 -> 10 -> ... -> 50)
        for i in range(10):  # 10 steps of 5 = 50
            knob.volume_up()
        
        self.assertEqual(knob.get_volume(), 50)
        print("PASS: Volume up: 0 to 50 in 10 steps")
        
        # Test volume_down (should go 50 -> 45 -> 40 -> ... -> 0)
        for i in range(10):  # 10 steps of 5 = 50
            knob.volume_down()
        
        self.assertEqual(knob.get_volume(), 0)
        print("PASS: Volume down: 50 to 0 in 10 steps")
        
        # Test multi-step changes
        knob.volume_up(10)  # 10 steps = 50
        self.assertEqual(knob.get_volume(), 50)
        
        knob.volume_down(5)  # 5 steps = 25
        self.assertEqual(knob.get_volume(), 25)
        
        print("PASS: Multi-step volume changes working correctly")
    
    def test_settings_integration(self):
        """Test that VS Code settings are correctly applied"""
        print("\n=== Testing VS Code Settings Integration ===")
        
        knob = VolumeKnob("dev")
        
        # Test volume 0 -> 50 settings
        knob.set_volume(0)
        with open(self.vscode_settings_file, 'r') as f:
            vol_0_settings = json.load(f)
        
        knob.set_volume(50)
        with open(self.vscode_settings_file, 'r') as f:
            vol_50_settings = json.load(f)
        
        # Verify specific setting changes
        self.assertFalse(vol_0_settings.get("python.enabled", True))
        self.assertTrue(vol_50_settings.get("python.enabled"))
        
        self.assertFalse(vol_0_settings.get("git.enabled", True))
        self.assertTrue(vol_50_settings.get("git.enabled"))
        
        # Verify Python language server changes
        self.assertEqual(vol_0_settings.get("python.languageServer"), "None")
        self.assertEqual(vol_50_settings.get("python.languageServer"), "Pylance")
        
        print("PASS: VS Code settings correctly updated")
        print("PASS: Python language server: None -> Pylance")
        print("PASS: Git and problems panel enabled at volume 50")


class TestCommitVolumeControl(unittest.TestCase):
    """Test commit volume control functionality"""
    
    def setUp(self):
        """Set up commit test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        Path(".vscode").mkdir(exist_ok=True)
    
    def tearDown(self):
        """Clean up commit test environment"""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_separate_dev_commit_volumes(self):
        """Test that dev and commit volumes can be set independently"""
        print("\n=== Testing Separate Dev/Commit Volumes ===")
        
        # Create separate knobs
        dev_knob = VolumeKnob("dev")
        commit_knob = VolumeKnob("commit")
        
        # Set different volumes
        dev_knob.set_volume(50)
        commit_knob.set_volume(200)
        
        # Verify they are independent
        self.assertEqual(dev_knob.get_volume(), 50)
        self.assertEqual(commit_knob.get_volume(), 200)
        
        # Verify different tools are active
        dev_tools = set(dev_knob.config_loader.get_active_tools(50))
        commit_tools = set(commit_knob.config_loader.get_active_tools(200))
        
        # At volume 50: git, problems, python
        expected_dev = {"git", "problems", "python"}
        self.assertEqual(dev_tools, expected_dev)
        
        # At volume 200: git, json, problems, python, typescript, yaml  
        expected_commit = {"git", "json", "problems", "python", "typescript", "yaml"}
        self.assertEqual(commit_tools, expected_commit)
        
        print("PASS: Dev and commit volumes set independently")
        print(f"PASS: Dev tools (vol 50): {sorted(dev_tools)}")
        print(f"PASS: Commit tools (vol 200): {sorted(commit_tools)}")
    
    def test_commit_volume_persistence(self):
        """Test that commit volume settings persist"""
        print("\n=== Testing Commit Volume Persistence ===")
        
        # Set commit volume
        commit_knob = VolumeKnob("commit")
        commit_knob.set_volume(300)
        
        # Create new instance (should load saved volume)
        commit_knob2 = VolumeKnob("commit")
        self.assertEqual(commit_knob2.get_volume(), 300)
        
        # Verify config file exists
        config_file = Path(".volume-commit.json")
        self.assertTrue(config_file.exists())
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        self.assertEqual(config["volume"], 300)
        self.assertEqual(config["knob_name"], "commit")
        
        print("PASS: Commit volume persisted correctly")
    
    def test_volume_scenario_workflows(self):
        """Test common development workflow scenarios"""
        print("\n=== Testing Workflow Scenarios ===")
        
        dev_knob = VolumeKnob("dev")
        commit_knob = VolumeKnob("commit")
        
        # Scenario 1: Quiet coding (light IDE, basic commit checks)
        dev_knob.set_volume(50)
        commit_knob.set_volume(200)
        
        dev_tools = set(dev_knob.config_loader.get_active_tools(50))
        commit_tools = set(commit_knob.config_loader.get_active_tools(200))
        
        # Dev should have minimal tools
        self.assertLessEqual(len(dev_tools), 3)
        self.assertIn("git", dev_tools)
        self.assertIn("python", dev_tools)
        
        # Commit should have more validation
        self.assertGreater(len(commit_tools), len(dev_tools))
        self.assertIn("yaml", commit_tools)
        self.assertIn("json", commit_tools)
        
        print("PASS: Quiet coding scenario works")
        
        # Scenario 2: Complete silence (emergency debugging)
        dev_knob.set_volume(0)
        commit_knob.set_volume(0)
        
        dev_tools = dev_knob.config_loader.get_active_tools(0)
        commit_tools = commit_knob.config_loader.get_active_tools(0)
        
        self.assertEqual(len(dev_tools), 0)
        self.assertEqual(len(commit_tools), 0)
        
        print("PASS: Complete silence scenario works")
        
        # Scenario 3: Production ready (full validation)
        dev_knob.set_volume(500)
        commit_knob.set_volume(1000)
        
        dev_tools = set(dev_knob.config_loader.get_active_tools(500))
        commit_tools = set(commit_knob.config_loader.get_active_tools(1000))
        
        # Both should have comprehensive tooling
        self.assertGreaterEqual(len(dev_tools), 6)
        self.assertGreaterEqual(len(commit_tools), 6)
        self.assertIn("github-actions", commit_tools)
        self.assertIn("powershell", commit_tools)
        
        print("PASS: Production ready scenario works")


class TestVolumeControlValidation(unittest.TestCase):
    """Test volume control validation and edge cases"""
    
    def setUp(self):
        """Set up validation test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        Path(".vscode").mkdir(exist_ok=True)
    
    def tearDown(self):
        """Clean up validation test environment"""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
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
        
        print("PASS: Volume validation working correctly")
    
    def test_boundary_conditions(self):
        """Test boundary conditions for volume changes"""
        print("\n=== Testing Boundary Conditions ===")
        
        knob = VolumeKnob("dev")
        
        # Test volume boundaries
        knob.set_volume(0)
        knob.volume_down()  # Should stay at 0
        self.assertEqual(knob.get_volume(), 0)
        
        knob.set_volume(1000) 
        knob.volume_up()  # Should stay at 1000
        self.assertEqual(knob.get_volume(), 1000)
        
        # Test large step changes
        knob.set_volume(0)
        knob.volume_up(200)  # 200 * 5 = 1000
        self.assertEqual(knob.get_volume(), 1000)
        
        knob.volume_down(200)  # 200 * 5 = 1000
        self.assertEqual(knob.get_volume(), 0)
        
        print("PASS: Boundary conditions handled correctly")


def run_volume_tests():
    """Run all volume control tests"""
    print("VOLUME CONTROL UNIT TESTS")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestVolumeControl))
    suite.addTests(loader.loadTestsFromTestCase(TestCommitVolumeControl))
    suite.addTests(loader.loadTestsFromTestCase(TestVolumeControlValidation))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("STATUS: ALL TESTS PASSED")
    else:
        print("STATUS: SOME TESTS FAILED")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_volume_tests()
