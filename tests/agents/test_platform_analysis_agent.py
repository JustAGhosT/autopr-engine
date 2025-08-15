from dataclasses import dataclass
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from autopr.actions.platform_detection.schema import (
    PlatformCategory,
    PlatformConfig,
    PlatformStatus,
    PlatformType,
)
from autopr.agents.platform_analysis_agent import (
    PlatformAnalysisAgent,
    PlatformAnalysisInputs,
)


@dataclass
class MockPlatformConfig(PlatformConfig):
    """Mock PlatformConfig for testing."""

    def __init__(self, **kwargs):
        # Set default values for required fields
        defaults = {
            "id": "test_platform",
            "name": "Test Platform",
            "display_name": "Test Platform",
            "description": "A test platform",
            "type": PlatformType.FRAMEWORK,
            "category": PlatformCategory.WEB,
            "status": PlatformStatus.ACTIVE,
            "is_active": True,
            "is_beta": False,
            "is_deprecated": False,
            "version": "1.0.0",
            "detection": {
                "files": ["package.json"],
                "dependencies": ["test-package"],
                "folder_patterns": ["test/*"],
                "content_patterns": [r"test-pattern"],
                "package_scripts": ["test"],
            },
        }
        defaults.update(kwargs)
        super().__init__(**defaults)


class TestPlatformAnalysisAgent(unittest.TestCase):
    def setUp(self):
        self.agent = PlatformAnalysisAgent()

    @patch("autopr.agents.platform_analysis_agent.PlatformConfigManager")
    def test_get_platform_info_returns_none_for_unknown_platform(self, mock_config_manager):
        """Test that None is returned for unknown platform types."""
        # Setup mock to return None for unknown platform
        mock_manager = MagicMock()
        mock_manager.get_platform.return_value = None
        mock_config_manager.return_value = mock_manager

        # Test with unknown platform
        result = self.agent._get_platform_info(PlatformType.UNKNOWN)

        # Verify
        assert result is None
        mock_manager.get_platform.assert_called_once_with(PlatformType.UNKNOWN.value)

    @patch("autopr.agents.platform_analysis_agent.PlatformConfigManager")
    def test_get_platform_info_returns_expected_structure(self, mock_config_manager):
        """Test that platform info is returned with expected structure."""
        # Create a test platform config
        test_config = MockPlatformConfig(
            id="test_platform",
            name="Test Platform",
            display_name="Test Platform Display",
            description="A test platform",
            type=PlatformType.FRAMEWORK,
            category=PlatformCategory.WEB,
            subcategory="Frontend",
            tags=["test", "frontend"],
            status=PlatformStatus.ACTIVE,
            documentation_url="https://example.com",
            is_active=True,
            is_beta=False,
            is_deprecated=False,
            version="1.0.0",
            last_updated="2025-01-01T00:00:00Z",
            supported_languages=["TypeScript", "JavaScript"],
            supported_frameworks=["React", "Next.js"],
            integrations=["Vercel", "Netlify"],
            detection={
                "files": ["package.json"],
                "dependencies": ["test-package"],
                "folder_patterns": ["test/*"],
                "commit_patterns": ["test:.*"],
                "content_patterns": [r"test-pattern"],
                "package_scripts": ["test"],
            },
            project_config={
                "build_command": "npm run build",
                "start_command": "npm start",
                "output_directory": "dist",
            },
        )

        # Setup mock to return our test config
        mock_manager = MagicMock()
        mock_manager.get_platform.return_value = test_config
        mock_config_manager.return_value = mock_manager

        # Test with known platform
        result = self.agent._get_platform_info(PlatformType.REACT)

        # Verify basic structure
        assert result is not None
        assert result["id"] == "test_platform"
        assert result["name"] == "Test Platform"
        assert result["display_name"] == "Test Platform Display"
        assert result["description"] == "A test platform"
        assert result["type"] == "framework"
        assert result["category"] == "web"
        assert result["subcategory"] == "Frontend"
        assert result["tags"] == ["test", "frontend"]
        assert result["status"] == "active"
        assert result["documentation_url"] == "https://example.com"
        assert result["is_active"]
        assert not result["is_beta"]
        assert not result["is_deprecated"]
        assert result["version"] == "1.0.0"
        assert result["last_updated"] == "2025-01-01T00:00:00Z"
        assert result["supported_languages"] == ["TypeScript", "JavaScript"]
        assert result["supported_frameworks"] == ["React", "Next.js"]
        assert result["integrations"] == ["Vercel", "Netlify"]

        # Verify detection rules
        assert "detection_rules" in result
        assert result["detection_rules"]["files"] == ["package.json"]
        assert result["detection_rules"]["dependencies"] == ["test-package"]
        assert result["detection_rules"]["folder_patterns"] == ["test/*"]
        assert result["detection_rules"]["commit_patterns"] == ["test:.*"]
        assert result["detection_rules"]["content_patterns"] == [r"test-pattern"]
        assert result["detection_rules"]["package_scripts"] == ["test"]

        # Verify project config
        assert "project_config" in result
        assert result["project_config"] == {"build_command": "npm run build", "start_command": "npm start", "output_directory": "dist"}

        # Verify the config manager was called correctly
        mock_manager.get_platform.assert_called_once_with(PlatformType.REACT.value)

        # Test with a known platform type
        self.agent._get_platform_info(PlatformType.IDE)

    def test_get_platform_info_unknown_platform(self):
        """Test getting platform info for an unknown platform value."""
        # Ensure the manager returns None for unknown platforms
        with patch("autopr.agents.platform_analysis_agent.PlatformConfigManager") as MockMgr:
            instance = MockMgr.return_value
            instance.get_platform.return_value = None

            platform_info = self.agent._get_platform_info("unknown_platform")
            assert platform_info is None
            instance.get_platform.assert_called_once_with("unknown_platform")

    @patch("autopr.agents.platform_analysis_agent.PlatformDetector")
    @patch("autopr.agents.platform_analysis_agent.PlatformAnalysis")
    async def test_analyze_platforms(self, mock_analysis, mock_detector):
        """Test the analyze_platforms method."""
        # Setup mocks
        mock_detector_instance = AsyncMock()
        mock_detector.return_value = mock_detector_instance

        # Mock the detector's analyze method to return a mock analysis
        mock_analysis_instance = MagicMock()
        mock_analysis_instance.platforms = [(PlatformType.REACT, 0.9), (PlatformType.NEXT_JS, 0.8)]
        mock_analysis_instance.tools = ["npm", "yarn"]
        mock_analysis_instance.frameworks = ["React", "Next.js"]
        mock_analysis_instance.languages = ["TypeScript", "JavaScript"]
        mock_analysis_instance.config_files = ["package.json", "next.config.js"]

        mock_analysis.return_value = mock_analysis_instance

        # Call the method
        inputs = PlatformAnalysisInputs(
            repo_path="/path/to/repo", file_paths=["package.json", "next.config.js"]
        )

        result = await self.agent.analyze_platforms(inputs)

        # Verify the result
        assert result is not None
        assert len(result.platforms) == 2
        assert result.platforms[0][0] == PlatformType.REACT.value
        assert result.platforms[0][1] == 0.9
        assert result.platforms[1][0] == PlatformType.NEXT_JS.value
        assert result.platforms[1][1] == 0.8
        assert "npm" in result.tools
        assert "yarn" in result.tools
        assert "React" in result.frameworks
        assert "Next.js" in result.frameworks
        assert "TypeScript" in result.languages
        assert "JavaScript" in result.languages
        assert "package.json" in result.config_files
        assert "next.config.js" in result.config_files

        # Verify the detector was called with the correct arguments
        mock_detector_instance.analyze.assert_called_once_with(
            Path("/path/to/repo"), file_paths=["package.json", "next.config.js"]
        )


if __name__ == "__main__":
    unittest.main()
