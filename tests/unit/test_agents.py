"""
Tests for the AutoPR Agent Framework.
"""
import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock, ANY, PropertyMock

from autopr.agents.crew import AutoPRCrew
from autopr.agents.models import CodeAnalysisReport, PlatformAnalysis, PlatformComponent, CodeIssue


class TestAutoPRCrew(unittest.IsolatedAsyncioTestCase):
    """Test cases for the AutoPRCrew class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a mock LLM
        self.mock_llm = MagicMock()
        
        # Create a mock LLM provider
        self.mock_llm_provider = MagicMock()
        self.mock_llm_provider.get_llm.return_value = self.mock_llm
        
        # Create mock agent instances
        self.mock_code_quality_agent = MagicMock()
        self.mock_platform_agent = MagicMock()
        self.mock_linting_agent = MagicMock()
        
        # Set up mock return values for agent methods
        self.mock_code_quality_agent.analyze_code_quality = AsyncMock(return_value={
            "metrics": {
                "maintainability_index": 85.5,
                "test_coverage": 78.2,
                "duplication": 2.1
            },
            "issues": [
                {
                    "file": "test.py",
                    "line": 1,
                    "message": "Missing docstring",
                    "severity": "low"
                }
            ]
        })
        
        self.mock_platform_agent.analyze_platform = AsyncMock(return_value=PlatformAnalysis(
            platform="Python",
            confidence=0.95,
            components=[
                PlatformComponent(
                    name="Python",
                    version="3.9",
                    confidence=0.95,
                    evidence=["File extensions: .py"]
                )
            ],
            recommendations=["Consider adding type hints"]
        ))
        
        self.mock_linting_agent.fix_code_issues = AsyncMock(return_value=[
            CodeIssue(
                file_path="test.py",
                line_number=1,
                message="Missing docstring",
                severity="low",
                rule_id="missing-docstring",
                category="style"
            )
        ])
    
    @patch('autopr.agents.crew.get_llm_provider_manager')
    @patch('autopr.agents.crew.CodeQualityAgent')
    @patch('autopr.agents.crew.PlatformAnalysisAgent')
    @patch('autopr.agents.crew.LintingAgent')
    @patch('autopr.agents.crew.Crew')
    async def test_analyze_repository(
        self,
        mock_crew_class,
        mock_linting_agent_cls,
        mock_platform_agent_cls,
        mock_code_quality_agent_cls,
        mock_get_llm_provider_manager
    ):
        """Test the full repository analysis workflow."""
        # Set up mock return values
        mock_get_llm_provider_manager.return_value = self.mock_llm_provider
        
        # Set up agent class mocks to return our instance mocks
        mock_code_quality_agent_cls.return_value = self.mock_code_quality_agent
        mock_platform_agent_cls.return_value = self.mock_platform_agent
        mock_linting_agent_cls.return_value = self.mock_linting_agent
        
        # Mock the Crew instance
        mock_crew_instance = MagicMock()
        mock_crew_class.return_value = mock_crew_instance
        
        # Create a temporary directory with some test files
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple Python file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def hello():\n    print('Hello, World!')")
            
            # Initialize the crew with the mocked dependencies
            crew = AutoPRCrew(llm_model="gpt-4")
            
            # Patch the crew's _create_*_task methods to return our mock tasks
            with patch.object(crew, '_create_code_quality_task') as mock_create_cq_task, \
                 patch.object(crew, '_create_platform_analysis_task') as mock_create_pa_task, \
                 patch.object(crew, '_create_linting_task') as mock_create_lint_task:
                
                # Mock the task creation to return completed tasks with our expected results
                mock_create_cq_task.return_value = asyncio.Future()
                mock_create_cq_task.return_value.set_result({
                    "metrics": {
                        "maintainability_index": 85.5,
                        "test_coverage": 78.2,
                        "duplication": 2.1
                    },
                    "issues": [
                        {
                            "file": "test.py",
                            "line": 1,
                            "message": "Missing docstring",
                            "severity": "low"
                        }
                    ]
                })
                
                mock_create_pa_task.return_value = asyncio.Future()
                mock_create_pa_task.return_value.set_result(PlatformAnalysis(
                    platform="Python",
                    confidence=0.95,
                    components=[
                        PlatformComponent(
                            name="Python",
                            version="3.9",
                            confidence=0.95,
                            evidence=["File extensions: .py"]
                        )
                    ],
                    recommendations=["Consider adding type hints"]
                ))
                
                mock_create_lint_task.return_value = asyncio.Future()
                mock_create_lint_task.return_value.set_result([
                    CodeIssue(
                        file_path="test.py",
                        line_number=1,
                        message="Missing docstring",
                        severity="low",
                        rule_id="missing-docstring",
                        category="style"
                    )
                ])
                
                # Run the analysis
                report = await crew.analyze_repository(tmpdir)
                
                # Verify the results
                self.assertIsInstance(report, CodeAnalysisReport)
                self.assertEqual(report.platform_analysis.platform, "Python")
                self.assertGreaterEqual(len(report.issues), 1)
                self.assertIn("maintainability_index", report.metrics)
                
                # Verify the mocks were called with the correct arguments
                mock_code_quality_agent_cls.assert_called_once_with(llm_model="gpt-4")
                mock_platform_agent_cls.assert_called_once_with(llm_model="gpt-4")
                mock_linting_agent_cls.assert_called_once_with(llm_model="gpt-4")
                
                # Verify the crew was initialized correctly
                mock_crew_class.assert_called_once()
                
                # Verify the tasks were created
                mock_create_cq_task.assert_called_once_with(Path(tmpdir))
                mock_create_pa_task.assert_called_once_with(Path(tmpdir))
                mock_create_lint_task.assert_called_once_with(Path(tmpdir))


if __name__ == "__main__":
    unittest.main()
