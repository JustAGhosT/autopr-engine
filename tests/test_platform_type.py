import unittest

from autopr.actions.platform_detection.schema import PlatformType


class TestPlatformType(unittest.TestCase):
    def test_platform_type_enum(self):
        """Test that PlatformType enum is accessible and has expected values."""
        assert hasattr(PlatformType, "IDE")
        assert hasattr(PlatformType, "CLOUD")
        assert hasattr(PlatformType, "VCS")
        assert PlatformType.IDE.value == "ide"
        assert PlatformType.CLOUD.value == "cloud"
        assert PlatformType.VCS.value == "vcs"


if __name__ == "__main__":
    unittest.main()
