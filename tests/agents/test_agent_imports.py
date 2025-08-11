import unittest


class TestAgentImports(unittest.TestCase):
    def test_import_platform_analysis_agent(self):
        """Test that we can import PlatformAnalysisAgent."""
        try:
            from autopr.agents.platform_analysis_agent import PlatformAnalysisAgent
            self.assertTrue(True, "Successfully imported PlatformAnalysisAgent")
        except ImportError as e:
            self.fail(f"Failed to import PlatformAnalysisAgent: {e}")

    def test_import_platform_type(self):
        """Test that we can import PlatformType."""
        try:
            from autopr.actions.platform_detection.schema import PlatformType
            self.assertTrue(True, "Successfully imported PlatformType")
        except ImportError as e:
            self.fail(f"Failed to import PlatformType: {e}")

if __name__ == "__main__":
    unittest.main()
