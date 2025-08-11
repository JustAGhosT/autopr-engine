import unittest
from dataclasses import dataclass
from pathlib import Path
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
        self.assertIsNone(result)
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
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "test_platform")
        self.assertEqual(result["name"], "Test Platform")
        self.assertEqual(result["display_name"], "Test Platform Display")
        self.assertEqual(result["description"], "A test platform")
        self.assertEqual(result["type"], "framework")
        self.assertEqual(result["category"], "web")
        self.assertEqual(result["subcategory"], "Frontend")
        self.assertEqual(result["tags"], ["test", "frontend"])
        self.assertEqual(result["status"], "active")
        self.assertEqual(result["documentation_url"], "https://example.com")
        self.assertTrue(result["is_active"])
        self.assertFalse(result["is_beta"])
        self.assertFalse(result["is_deprecated"])
        self.assertEqual(result["version"], "1.0.0")
        self.assertEqual(result["last_updated"], "2025-01-01T00:00:00Z")
        self.assertEqual(result["supported_languages"], ["TypeScript", "JavaScript"])
        self.assertEqual(result["supported_frameworks"], ["React", "Next.js"])
        self.assertEqual(result["integrations"], ["Vercel", "Netlify"])

        # Verify detection rules
        self.assertIn("detection_rules", result)
        self.assertEqual(result["detection_rules"]["files"], ["package.json"])
        self.assertEqual(result["detection_rules"]["dependencies"], ["test-package"])
        self.assertEqual(result["detection_rules"]["folder_patterns"], ["test/*"])
        self.assertEqual(result["detection_rules"]["commit_patterns"], ["test:.*"])
        self.assertEqual(result["detection_rules"]["content_patterns"], [r"test-pattern"])
        self.assertEqual(result["detection_rules"]["package_scripts"], ["test"])

        # Verify project config
        self.assertIn("project_config", result)
        self.assertEqual(
            result["project_config"],
            {
                "build_command": "npm run build",
                "start_command": "npm start",
                "output_directory": "dist",
            },
        )

        # Verify the config manager was called correctly
        mock_manager.get_platform.assert_called_once_with(PlatformType.REACT.value)

        # Test with a known platform type
        platform_info = self.agent._get_platform_info(PlatformType.IDE)

    def test_get_platform_info_unknown_platform(self):
        """Test getting platform info for an unknown platform type."""

        # Test with an unknown platform type
        class UnknownPlatform(PlatformType):
            UNKNOWN = "unknown_platform"

        platform_info = self.agent._get_platform_info(UnknownPlatform.UNKNOWN)
        self.assertIsNone(platform_info)

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
        self.assertIsNotNone(result)
        self.assertEqual(len(result.platforms), 2)
        self.assertEqual(result.platforms[0][0], PlatformType.REACT.value)
        self.assertEqual(result.platforms[0][1], 0.9)
        self.assertEqual(result.platforms[1][0], PlatformType.NEXT_JS.value)
        self.assertEqual(result.platforms[1][1], 0.8)
        self.assertIn("npm", result.tools)
        self.assertIn("yarn", result.tools)
        self.assertIn("React", result.frameworks)
        self.assertIn("Next.js", result.frameworks)
        self.assertIn("TypeScript", result.languages)
        self.assertIn("JavaScript", result.languages)
        self.assertIn("package.json", result.config_files)
        self.assertIn("next.config.js", result.config_files)

        # Verify the detector was called with the correct arguments
        mock_detector_instance.analyze.assert_called_once_with(
            Path("/path/to/repo"), file_paths=["package.json", "next.config.js"]
        )


if __name__ == "__main__":
    unittest.main()
