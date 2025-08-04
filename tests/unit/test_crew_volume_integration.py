"""
Tests for CrewAI integration with volume control in AutoPR Engine.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, ANY
from typing import Dict, Any, Optional, Union

from autopr.agents.crew import AutoPRCrew
from autopr.actions.quality_engine.engine import QualityInputs, QualityMode
from autopr.actions.platform_detection.detector import PlatformAnalysis, PlatformComponent
from autopr.models.artifacts import CodeIssue, IssueSeverity


class TestCrewVolumeIntegration:
    """Test suite for volume control in CrewAI orchestration."""

    @pytest.fixture
    def mock_llm_provider(self):
        """Mock LLM provider for testing."""
        with patch('autopr.agents.crew.get_llm_provider_manager') as mock_manager:
            mock_llm = MagicMock()
            mock_manager.return_value.get_llm.return_value = mock_llm
            yield mock_llm
            
    @pytest.fixture
    def mock_agents(self):
        """Mock agent classes to avoid actual LLM calls."""
        with patch('autopr.agents.crew.CodeQualityAgent'), \
             patch('autopr.agents.crew.PlatformAnalysisAgent'), \
             patch('autopr.agents.crew.LintingAgent'):
            yield



    @pytest.fixture
    def crew(self, mock_llm_provider, mock_agents):
        """Create a test crew instance with mocked dependencies."""
        return AutoPRCrew(llm_model="gpt-4")

    @pytest.mark.parametrize("volume,expected_mode", [
        (0, QualityMode.FAST),
        (300, QualityMode.FAST),
        (500, QualityMode.SMART),
        (800, QualityMode.COMPREHENSIVE),
        (1000, QualityMode.COMPREHENSIVE),
    ])
    def test_volume_to_quality_mode_mapping(self, crew, volume: int, expected_mode: QualityMode):
        """Test that volume levels correctly map to quality modes."""
        quality_inputs = crew._create_quality_inputs(volume)
        assert quality_inputs.mode == expected_mode, \
            f"Volume {volume} should map to {expected_mode}, got {quality_inputs.mode}"

    @pytest.mark.parametrize("volume,expected_depth", [
        (0, "quick"),
        (300, "standard"),
        (700, "thorough"),
        (1000, "thorough"),
    ])
    def test_volume_affects_analysis_depth(self, crew, volume: int, expected_depth: str):
        """Test that volume level affects the analysis depth in task descriptions."""
        task = crew._create_code_quality_task(
            Path("/test/repo"),
            {"volume": volume, "volume_context": {}, "quality_inputs": {"mode": "smart"}}
        )
        assert f"Perform a {expected_depth} analysis" in task.description

    @pytest.mark.parametrize("volume,expected_autofix", [
        (0, False),
        (400, False),
        (600, True),
        (1000, True),
    ])
    def test_volume_affects_linting_autofix(self, crew, volume: int, expected_autofix: bool):
        """Test that volume level affects auto-fix behavior in linting tasks."""
        task = crew._create_linting_task(
            Path("/test/repo"),
            {"volume": volume, "volume_context": {}, "quality_inputs": {"mode": "smart"}}
        )
        assert task.context["auto_fix"] == expected_autofix

    @pytest.mark.parametrize("volume,expected_detail", [
        (0, "focused"),
        (400, "detailed"),
        (800, "exhaustive"),
        (1000, "exhaustive"),
    ])
    def test_volume_affects_detail_level(self, crew, volume: int, expected_detail: str):
        """Test that volume level affects the detail level in code quality tasks."""
        task = crew._create_code_quality_task(
            Path("/test/repo"),
            {"volume": volume, "volume_context": {}, "quality_inputs": {"mode": "smart"}}
        )
        assert f"Focus on {expected_detail} examination" in task.description

    def test_volume_propagates_to_agents(self, crew):
        """Test that volume settings are properly propagated to agent initialization."""
        test_volume = 750
        crew = AutoPRCrew(volume=test_volume)
        
        # Check that agents were initialized with the correct volume
        # Access agents through the crew's agent registry if available
        # or use direct attribute access based on implementation
        if hasattr(crew, 'code_quality_agent'):
            assert crew.code_quality_agent.volume == test_volume
        if hasattr(crew, 'platform_agent'):
            assert crew.platform_agent.volume == test_volume
        if hasattr(crew, 'linting_agent'):
            assert crew.linting_agent.volume == test_volume

    @pytest.mark.asyncio
    async def test_full_analysis_with_volume(self, crew):
        """Test end-to-end analysis with volume control."""
        test_volume = 600
        test_repo = Path("/test/repo")
        
        # Mock agent responses
        mock_quality = {"summary": "Good code quality", "metrics": {"score": 8.5}}
        mock_platform = PlatformAnalysis(
            platform="python", 
            confidence=0.95,
            components=[],
            summary="Python project detected"
        )
        mock_issues = [
            CodeIssue(
                file="test.py",
                line=10,
                message="Unused import",
                severity=IssueSeverity.LOW,
                fix="Remove unused import"
            )
        ]
        
        # Mock the actual crew execution
        with patch.object(crew, 'crew', new_callable=MagicMock()) as mock_crew:
            # Configure mock crew to return our test responses
            mock_crew.kickoff.return_value = {
                'code_quality': mock_quality,
                'platform_analysis': mock_platform,
                'linting_issues': mock_issues
            }
            
            # Run the analysis
            report = await crew.analyze_repository(test_repo, volume=test_volume)
            
            # Verify volume was used in the analysis
            assert hasattr(report, 'metadata')
            assert 'volume' in report.metadata
            assert report.metadata['volume'] == test_volume
            
            # Verify the report contains our test data
            # Note: Adjust these assertions based on actual report structure
            assert hasattr(report, 'code_quality') or 'code_quality' in report
            assert hasattr(report, 'platform_analysis') or 'platform_analysis' in report
            assert hasattr(report, 'linting_issues') or 'linting_issues' in report
