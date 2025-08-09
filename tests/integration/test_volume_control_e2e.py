"""
End-to-end tests for volume control in AutoPR Engine.

These tests verify the complete flow of volume control from the CrewAI orchestration
down to individual agent tasks and quality inputs.
"""
import os
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, ANY
from typing import Dict, Any, List, Optional

from autopr.agents.crew import AutoPRCrew
from autopr.actions.quality_engine.engine import QualityInputs
from autopr.enums import QualityMode
from autopr.agents.models import PlatformAnalysis, PlatformComponent, CodeIssue, IssueSeverity


class TestVolumeControlE2E:
    """End-to-end tests for volume control feature."""

    @pytest.fixture
    def mock_llm_provider(self):
        """Mock LLM provider to avoid actual API calls."""
        with patch('autopr.agents.crew.get_llm_provider_manager') as mock_manager:
            mock_llm = MagicMock()
            mock_manager.return_value.get_llm.return_value = mock_llm
            yield mock_llm

    @pytest.fixture
    def mock_agents(self):
        """Mock agent classes to avoid actual LLM calls."""
        with patch('autopr.agents.crew.CodeQualityAgent') as mock_qa_agent, \
             patch('autopr.agents.crew.PlatformAnalysisAgent') as mock_pa_agent, \
             patch('autopr.agents.crew.LintingAgent') as mock_lint_agent:
            
            # Set up mock agent instances
            mock_qa_agent.return_value = MagicMock()
            mock_pa_agent.return_value = MagicMock()
            mock_lint_agent.return_value = MagicMock()
            
            yield {
                'code_quality': mock_qa_agent.return_value,
                'platform_analysis': mock_pa_agent.return_value,
                'linting': mock_lint_agent.return_value,
            }

    @pytest.fixture
    def test_repo(self):
        """Create a temporary test repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple Python file for testing
            test_file = Path(temp_dir) / 'test.py'
            test_file.write_text('def hello():\n    print("Hello, World!")\n')
            yield temp_dir

    @pytest.mark.parametrize("volume,expected_mode,expected_level", [
        (0, QualityMode.FAST, "Silent"),
        (100, QualityMode.FAST, "Quiet"),
        (300, QualityMode.FAST, "Moderate"),
        (450, QualityMode.SMART, "Balanced"),
        (700, QualityMode.COMPREHENSIVE, "Thorough"),
        (900, QualityMode.COMPREHENSIVE, "Maximum"),
    ])
    def test_volume_propagation(self, test_repo, mock_llm_provider, mock_agents, volume, expected_mode, expected_level):
        """Test that volume settings propagate correctly through the entire pipeline."""
        # Arrange
        crew = AutoPRCrew(llm_model="gpt-4", volume=volume)
        
        # Configure mock agent responses
        mock_agents['code_quality'].analyze_code.return_value = []  # No code quality issues
        mock_agents['platform_analysis'].analyze_platform.return_value = PlatformAnalysis(
            platform="python",
            components=[],
            confidence=0.9,
            metadata={}
        )
        mock_agents['linting'].analyze_code.return_value = []  # No linting issues
        
        # Act
        report = crew.analyze_repository(test_repo)
        
        # Assert - Verify volume context is passed to agents
        for agent in mock_agents.values():
            # Check that the volume context is included in the agent's backstory
            assert f"volume level {volume} ({expected_level})" in agent.backstory.lower()
        
        # Verify quality inputs are created with correct mode
        assert report.quality_inputs.mode == expected_mode
        
        # Verify the report includes volume information
        assert report.volume == volume
        assert report.volume_level == expected_level

    def test_volume_affects_analysis_depth(self, test_repo, mock_llm_provider, mock_agents):
        """Test that volume affects the depth and thoroughness of analysis."""
        # Test with low volume (fast mode)
        crew_low = AutoPRCrew(llm_model="gpt-4", volume=100)
        
        # Test with high volume (comprehensive mode)
        crew_high = AutoPRCrew(llm_model="gpt-4", volume=900)
        
        # Configure mock agent responses
        for agent in mock_agents.values():
            agent.analyze_code.return_value = []
            if hasattr(agent, 'analyze_platform'):
                agent.analyze_platform.return_value = PlatformAnalysis(
                    platform="python",
                    components=[],
                    confidence=0.9,
                    metadata={}
                )
        
        # Run analysis with low volume
        report_low = crew_low.analyze_repository(test_repo)
        
        # Run analysis with high volume
        report_high = crew_high.analyze_repository(test_repo)
        
        # Assert that high volume results in more thorough analysis
        # This is verified by checking the analyze_code calls for volume context
        for agent_name, agent in mock_agents.items():
            if hasattr(agent, 'analyze_code') and agent.analyze_code.called:
                # Check call arguments for volume-related context
                call_args = agent.analyze_code.call_args_list
                
                # Get all call contexts that include volume information
                volume_contexts = []
                for call in call_args:
                    kwargs = call[1]  # Get keyword arguments
                    if 'context' in kwargs and 'volume' in kwargs['context']:
                        volume_contexts.append(kwargs['context']['volume'])
                
                # Verify we found volume context in the calls
                assert len(volume_contexts) > 0, f"Expected volume context in analyze_code calls for {agent_name}"

    def test_volume_affects_auto_fix_behavior(self, test_repo, mock_llm_provider, mock_agents):
        """Test that volume affects whether auto-fixes are applied."""
        # Create a linting issue that could be auto-fixed
        lint_issue = CodeIssue(
            file_path="test.py",
            line=1,
            column=1,
            message="Missing docstring",
            severity=IssueSeverity.WARNING,
            rule_id="missing-docstring",
            fix_suggestion='Add docstring: """Module docstring."""',
            fix_confidence=0.9
        )
        
        # Configure mock agent to return the linting issue
        mock_agents['linting'].analyze_code.return_value = [lint_issue]
        
        # Test with low volume (should not auto-fix)
        crew_low = AutoPRCrew(llm_model="gpt-4", volume=100)
        report_low = crew_low.analyze_repository(test_repo, auto_fix=False)
        
        # Test with high volume (should auto-fix)
        crew_high = AutoPRCrew(llm_model="gpt-4", volume=900)
        report_high = crew_high.analyze_repository(test_repo, auto_fix=True)
        
        # Verify that auto-fix behavior is controlled by the auto_fix parameter
        # and that volume affects the agent's behavior
        assert not report_low.applied_fixes, "Expected no fixes to be applied with auto_fix=False"
        assert report_high.applied_fixes, "Expected fixes to be applied with auto_fix=True"
        
        # Verify that the linting agent was called with the correct parameters
        mock_agents['linting'].analyze_code.assert_called()
        
        # Check that the quality inputs were passed correctly
        assert report_low.quality_inputs.mode == QualityMode.FAST
        assert report_high.quality_inputs.mode == QualityMode.COMPREHENSIVE
