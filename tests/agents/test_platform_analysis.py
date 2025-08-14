import unittest
from unittest.mock import MagicMock, patch

from autopr.agents.agents import PlatformAnalysisAgent


class TestPlatformAnalysisAgent(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.agent = PlatformAnalysisAgent(volume=500, verbose=False, llm_model="gpt-4")

    @patch("autopr.actions.platform_detection.PlatformDetector")
    async def test_analyze_platform_returns_platform_analysis(self, mock_detector):
        """Test that analyze_platform returns a PlatformAnalysis object."""
        # Setup mock detector
        mock_detector_instance = MagicMock()
        mock_detector.return_value = mock_detector_instance

        # Setup mock analysis result
        mock_analysis = MagicMock()
        mock_detector_instance.analyze.return_value = mock_analysis

        # Test analyze_platform
        repo_path = "/path/to/repo"
        result = await self.agent.analyze_platform(repo_path)

        # Verify
        assert result == mock_analysis
        mock_detector_instance.analyze.assert_called_once_with(repo_path)

    @patch("autopr.actions.platform_detection.PlatformDetector")
    def test_platform_detector_property_returns_detector(self, mock_detector):
        """Test that the platform_detector property returns the detector instance."""
        # Setup mock detector
        mock_detector_instance = MagicMock()
        mock_detector.return_value = mock_detector_instance

        # Test platform_detector property
        result = self.agent.platform_detector

        # Verify
        assert result == mock_detector_instance
        mock_detector.assert_called_once()

        # Test that subsequent calls return the same instance
        assert self.agent.platform_detector is mock_detector_instance


if __name__ == "__main__":
    # Run async tests
    import unittest

    # Create a test runner
    runner = unittest.TextTestRunner()

    # Create a test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestPlatformAnalysisAgent)

    # Run the tests
    runner.run(suite)
