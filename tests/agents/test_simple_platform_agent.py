import unittest

# Try to import the required modules
try:
    from autopr.actions.platform_detection.schema import PlatformType
    from autopr.agents.platform_analysis_agent import PlatformAnalysisAgent
    print("All imports successful!")
except ImportError as e:
    print(f"Import error: {e}")
    raise

class TestSimplePlatformAnalysis(unittest.TestCase):
    def test_imports_work(self):
        """Test that imports work correctly."""
        # This test will pass if we get here without import errors
        self.assertTrue(True)

if __name__ == "__main__":
    unittest.main()
