import unittest
from unittest.mock import MagicMock, patch
from autopr.agents.platform_analysis_agent import PlatformAnalysisAgent
from autopr.actions.platform_detection.schema import PlatformType

class TestMinimalPlatformAnalysisAgent(unittest.TestCase):
    def setUp(self):
        self.agent = PlatformAnalysisAgent()
    
    @patch('autopr.agents.platform_analysis_agent.PlatformConfigManager')
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

if __name__ == "__main__":
    unittest.main()
