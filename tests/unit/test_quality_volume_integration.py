"""
Tests for volume control integration with QualityEngine.
"""

from typing import Any
import unittest
from unittest.mock import MagicMock, patch, ANY
from pathlib import Path

from autopr.actions.quality_engine.engine import QualityEngine
from autopr.actions.quality_engine.models import QualityInputs, QualityMode
from autopr.actions.quality_engine.volume_mapping import get_volume_config, get_volume_level_name


class TestVolumeIntegration(unittest.TestCase):
    """Test volume control integration with QualityEngine."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a mock tool registry
        self.mock_tool_registry = MagicMock()
        self.mock_tool_registry.get_all_tools.return_value = [
            MagicMock(name="ruff"),
            MagicMock(name="bandit"),
            MagicMock(name="black"),
            MagicMock(name="mypy"),
            MagicMock(name="pylint"),
        ]
        
        # Initialize QualityEngine with mock dependencies
        self.engine = QualityEngine(
            config_path="pyproject.toml",
            tool_registry=self.mock_tool_registry,
            handler_registry=MagicMock(),
        )
        
        # Patch the tool runner to avoid actual execution
        self.tool_runner_patcher = patch('autopr.actions.quality_engine.engine.run_tool')
        self.mock_run_tool = self.tool_runner_patcher.start()
        self.mock_run_tool.return_value = MagicMock(
            issues=[],
            files_with_issues=[],
            summary="Test summary",
            execution_time=0.1,
        )
    
    def tearDown(self):
        """Clean up test environment."""
        self.tool_runner_patcher.stop()
    
    def test_volume_mapping(self):
        """Test volume level to quality mode mapping."""
        # Test volume 0 (silent)
        config = get_volume_config(0)
        self.assertEqual(config["mode"], QualityMode.ULTRA_FAST)
        self.assertEqual(config["max_fixes"], 0)
        self.assertFalse(config["enable_ai_agents"])
        
        # Test volume 250 (quiet)
        config = get_volume_config(250)
        self.assertEqual(config["mode"], QualityMode.FAST)
        self.assertEqual(config["max_fixes"], 12)  # 250 / 20 = 12.5 -> 12
        
        # Test volume 500 (moderate)
        config = get_volume_config(500)
        self.assertEqual(config["mode"], QualityMode.SMART)
        self.assertEqual(config["max_fixes"], 25)  # 500 / 20 = 25
        
        # Test volume 750 (thorough)
        config = get_volume_config(750)
        self.assertEqual(config["mode"], QualityMode.COMPREHENSIVE)
        self.assertEqual(config["max_fixes"], 37)  # 750 / 20 = 37.5 -> 37
        
        # Test volume 1000 (max)
        config = get_volume_config(1000)
        self.assertEqual(config["mode"], QualityMode.AI_ENHANCED)
        self.assertEqual(config["max_fixes"], 100)  # Capped at 100
    
    async def test_volume_based_tool_selection(self):
        """Test that tool selection is influenced by volume level."""
        # Test volume 0 (silent) - only ruff should be used
        inputs = QualityInputs(volume=0)
        await self.engine.execute(inputs, {})
        called_tools = {call[0][0].name for call in self.mock_run_tool.call_args_list}
        self.assertEqual(called_tools, {"ruff"})
        
        # Reset mock for next test
        self.mock_run_tool.reset_mock()
        
        # Test volume 300 (moderate) - ruff, bandit, black
        inputs = QualityInputs(volume=300)
        await self.engine.execute(inputs, {})
        called_tools = {call[0][0].name for call in self.mock_run_tool.call_args_list}
        self.assertEqual(called_tools, {"ruff", "bandit", "black"})
        
        # Reset mock for next test
        self.mock_run_tool.reset_mock()
        
        # Test volume 800 (high) - all tools including mypy and pylint
        inputs = QualityInputs(volume=800)
        await self.engine.execute(inputs, {})
        called_tools = {call[0][0].name for call in self.mock_run_tool.call_args_list}
        self.assertEqual(called_tools, {"ruff", "bandit", "black", "mypy", "pylint"})
    
    async def test_volume_updates_inputs(self):
        """Test that volume updates QualityInputs parameters."""
        # Test with volume 0
        inputs = QualityInputs(
            mode=QualityMode.SMART,  # Will be overridden
            max_fixes=50,  # Will be overridden
            enable_ai_agents=True,  # Will be overridden
            volume=0
        )
        
        # Apply volume settings
        inputs.apply_volume_settings()
        
        # Verify inputs were updated
        self.assertEqual(inputs.mode, QualityMode.ULTRA_FAST)
        self.assertEqual(inputs.max_fixes, 0)
        self.assertFalse(inputs.enable_ai_agents)
        
        # Test with volume 1000
        inputs = QualityInputs(volume=1000)
        inputs.apply_volume_settings()
        
        # Verify inputs were updated
        self.assertEqual(inputs.mode, QualityMode.AI_ENHANCED)
        self.assertEqual(inputs.max_fixes, 100)
        self.assertTrue(inputs.enable_ai_agents)
    
    async def test_volume_in_execute_method(self):
        """Test that volume is properly handled in the execute method."""
        # Test with volume parameter
        inputs = QualityInputs()
        await self.engine.execute(inputs, {}, volume=0)
        
        # Verify mode was set to ULTRA_FAST for volume 0
        self.assertEqual(inputs.mode, QualityMode.ULTRA_FAST)
        
        # Test with volume in inputs
        inputs = QualityInputs(volume=1000)
        await self.engine.execute(inputs, {})
        
        # Verify mode was set to AI_ENHANCED for volume 1000
        self.assertEqual(inputs.mode, QualityMode.AI_ENHANCED)


if __name__ == "__main__":
    unittest.main()
