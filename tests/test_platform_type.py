import unittest

from autopr.actions.platform_detection.schema import PlatformType


class TestPlatformType(unittest.TestCase):
    def test_platform_type_enum(self):
        """Test that PlatformType enum is accessible and has expected values."""
        self.assertTrue(hasattr(PlatformType, "IDE"))
        self.assertTrue(hasattr(PlatformType, "CLOUD"))
        self.assertTrue(hasattr(PlatformType, "VCS"))
        self.assertEqual(PlatformType.IDE.value, "ide")
        self.assertEqual(PlatformType.CLOUD.value, "cloud")
        self.assertEqual(PlatformType.VCS.value, "vcs")

if __name__ == "__main__":
    unittest.main()
