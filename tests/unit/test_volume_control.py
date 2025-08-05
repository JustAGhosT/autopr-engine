#!/usr/bin/env python3
"""Unit tests for volume control system"""

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

class BaseVolumeTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        Path(".vscode").mkdir(exist_ok=True)
        self.vscode_settings = Path(".vscode/settings.json")
        with open(self.vscode_settings, 'w') as f:
            json.dump({
                "python.enabled": False,
                "git.enabled": False,
                "yaml.validate": False,
                "problems.decorations.enabled": False
            }, f, indent=2)
    
    def tearDown(self):
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

class TestVolumeControl(BaseVolumeTest):
    def test_volume_transitions(self):
        knob = VolumeKnob("dev")
        
        # Test 0 → 50 transition
        knob.set_volume(0)
        settings = json.loads(self.vscode_settings.read_text())
        self.assertFalse(settings.get("python.enabled", True))
        
        knob.set_volume(50)
        settings = json.loads(self.vscode_settings.read_text())
        self.assertTrue(settings.get("python.enabled"))
        self.assertTrue(settings.get("git.enabled"))
        self.assertFalse(settings.get("yaml.validate", True))
        
        # Test 50 → 0 transition
        knob.set_volume(0)
        settings = json.loads(self.vscode_settings.read_text())
        self.assertFalse(settings.get("python.enabled", True))
        self.assertEqual(settings.get("python.languageServer"), "None")
        
    def test_volume_validation(self):
        knob = VolumeKnob("dev")
        with self.assertRaises(ValueError):
            knob.set_volume(-1)
        with self.assertRaises(ValueError):
            knob.set_volume(1001)
        knob.set_volume(0)  # Should not raise
        knob.set_volume(1000)  # Should not raise

class TestCommitVolumeControl(BaseVolumeTest):
    def test_separate_volumes(self):
        dev_knob = VolumeKnob("dev")
        commit_knob = VolumeKnob("commit")
        
        dev_knob.set_volume(50)
        commit_knob.set_volume(200)
        
        self.assertEqual(dev_knob.get_volume(), 50)
        self.assertEqual(commit_knob.get_volume(), 200)
        
        dev_tools = set(dev_knob.config_loader.get_active_tools(50))
        commit_tools = set(commit_knob.config_loader.get_active_tools(200))
        
        self.assertIn("python", dev_tools)
        self.assertIn("yaml", commit_tools)

if __name__ == "__main__":
    unittest.main(verbosity=2)