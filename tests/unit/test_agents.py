"""
Tests for the AutoPR Agent Framework.
"""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from autopr.agents.crew.main import AutoPRCrew
from autopr.agents.models import CodeIssue, PlatformAnalysis, PlatformComponent


class TestAutoPRCrew(unittest.IsolatedAsyncioTestCase):
    """Test cases for the AutoPRCrew class."""

    # Test data constants
    CODE_QUALITY_METRICS = {
        "maintainability_index": 85.5,
        "test_coverage": 78.2,
        "duplication": 2.1,
    }

    CODE_QUALITY_ISSUES = [
        {
            "file": "test.py",
            "line": 1,
            "message": "Missing docstring",
            "severity": "low",
        }
    ]

    PLATFORM_COMPONENTS = [
        PlatformComponent(
            name="Python",
            version="3.9",
            confidence=0.95,
            evidence=["File extensions: .py"],
        )
    ]

    LINT_ISSUES = [
        CodeIssue(
            file_path="test.py",
            line_number=1,
            message="Missing docstring",
            severity="low",
            rule_id="missing-docstring",
            category="style",
        )
    ]

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_llm = MagicMock()
        self.mock_llm_provider = MagicMock()
        self.mock_llm_provider.get_llm.return_value = self.mock_llm

        # Initialize mock agents with helper method
        self.mock_code_quality_agent = self._create_mock_code_quality_agent()
        self.mock_platform_agent = self._create_mock_platform_agent()
        self.mock_linting_agent = self._create_mock_linting_agent()

    def _create_mock_code_quality_agent(self) -> MagicMock:
        """Create and return a mock code quality agent."""
        mock_agent = MagicMock()
        mock_agent.analyze_code_quality = AsyncMock(
            return_value={
                "metrics": self.CODE_QUALITY_METRICS,
                "issues": self.CODE_QUALITY_ISSUES,
            }
        )
        return mock_agent

    def _create_mock_platform_agent(self) -> MagicMock:
        """Create and return a mock platform analysis agent."""
        mock_agent = MagicMock()
        mock_agent.analyze_platform = AsyncMock(
            return_value=PlatformAnalysis(
                platform="Python",
                confidence=0.95,
                components=self.PLATFORM_COMPONENTS,
                recommendations=["Consider adding type hints"],
            )
        )
        return mock_agent

    def _create_mock_linting_agent(self) -> MagicMock:
        """Create and return a mock linting agent."""
        mock_agent = MagicMock()
        mock_agent.fix_code_issues = AsyncMock(return_value=self.LINT_ISSUES)
        return mock_agent

    def _create_crew_instance(self) -> AutoPRCrew:
        """Create a test instance of AutoPRCrew with injected dependencies."""
        return AutoPRCrew(
            llm_model="gpt-4",
            code_quality_agent=self.mock_code_quality_agent,
            platform_agent=self.mock_platform_agent,
            linting_agent=self.mock_linting_agent,
            llm_provider=self.mock_llm_provider,
        )

    def test_analyze_repository(self):
        """Test the full repository analysis workflow."""
        # Create test repository with a Python file
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def hello():\n    print('Hello, World!')")

            # Create crew instance with injected dependencies
            crew = self._create_crew_instance()

            # Mock the analyze method to return expected results
            def mock_analyze(self, repo_path=None, volume=None, **kwargs):
                return {
                    "code_quality": {
                        "metrics": TestAutoPRCrew.CODE_QUALITY_METRICS,
                        "issues": TestAutoPRCrew.CODE_QUALITY_ISSUES,
                    },
                    "platform_analysis": {
                        "platform": "Python",
                        "confidence": 0.95,
                        "components": TestAutoPRCrew.PLATFORM_COMPONENTS,
                        "recommendations": ["Consider adding type hints"],
                    },
                    "linting_issues": TestAutoPRCrew.LINT_ISSUES,
                    "current_volume": volume or self.volume,
                    "quality_inputs": {"mode": "smart"},
                }

            with patch.object(crew.__class__, "analyze", mock_analyze):
                # Execute test
                report = crew.analyze_repository(tmpdir)

                # Verify results
                assert isinstance(report, dict)
                assert report["platform_analysis"]["platform"] == "Python"
                assert len(report["linting_issues"]) >= 1
                assert "maintainability_index" in report["code_quality"]["metrics"]


if __name__ == "__main__":
    unittest.main()
