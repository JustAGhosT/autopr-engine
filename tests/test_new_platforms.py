"""
Tests for newly added AI platforms (Base44, Windsurf, Continue, Aider, etc.)
"""
import unittest
from pathlib import Path
from autopr.actions.platform_detection.config import PlatformConfigManager


class TestNewPlatforms(unittest.TestCase):
    """Test suite for the 10 newly added AI platforms."""

    def setUp(self):
        """Set up test fixtures."""
        self.config_manager = PlatformConfigManager()
        self.ai_platforms = self.config_manager.get_ai_platforms()

    def test_base44_platform_exists(self):
        """Test that Base44 platform is properly configured."""
        self.assertIn("base44", self.ai_platforms, "Base44 platform not found")
        
        base44 = self.ai_platforms["base44"]
        self.assertEqual(base44["name"], "Base44")
        self.assertEqual(base44["category"], "ai_development")
        self.assertIn("detection", base44)
        self.assertIn("project_config", base44)
        
        # Check detection patterns
        detection = base44["detection"]
        self.assertIn(".base44", detection["files"])
        self.assertIn("@base44/core", detection["dependencies"])

    def test_windsurf_platform_exists(self):
        """Test that Windsurf platform is properly configured."""
        self.assertIn("windsurf", self.ai_platforms, "Windsurf platform not found")
        
        windsurf = self.ai_platforms["windsurf"]
        self.assertEqual(windsurf["name"], "Windsurf")
        self.assertEqual(windsurf["category"], "ai_development")
        
        # Check detection patterns
        detection = windsurf["detection"]
        self.assertIn(".windsurf", detection["files"])
        self.assertIn("@codeium/windsurf", detection["dependencies"])

    def test_continue_platform_exists(self):
        """Test that Continue platform is properly configured."""
        self.assertIn("continue", self.ai_platforms, "Continue platform not found")
        
        continue_platform = self.ai_platforms["continue"]
        self.assertEqual(continue_platform["name"], "Continue")
        self.assertEqual(continue_platform["category"], "ai_development")
        
        # Check detection patterns
        detection = continue_platform["detection"]
        self.assertIn(".continue", detection["files"])
        self.assertIn("continue-dev", detection["dependencies"])

    def test_aider_platform_exists(self):
        """Test that Aider platform is properly configured."""
        self.assertIn("aider", self.ai_platforms, "Aider platform not found")
        
        aider = self.ai_platforms["aider"]
        self.assertEqual(aider["name"], "Aider")
        self.assertEqual(aider["category"], "ai_development")
        
        # Check detection patterns
        detection = aider["detection"]
        self.assertIn(".aider", detection["files"])
        self.assertIn("aider-chat", detection["dependencies"])

    def test_amazon_q_platform_exists(self):
        """Test that Amazon Q Developer platform is properly configured."""
        self.assertIn("amazon_q", self.ai_platforms, "Amazon Q platform not found")
        
        amazon_q = self.ai_platforms["amazon_q"]
        self.assertEqual(amazon_q["name"], "Amazon Q Developer")
        self.assertEqual(amazon_q["category"], "ai_development")
        
        # Check detection patterns
        detection = amazon_q["detection"]
        self.assertIn(".amazonq", detection["files"])

    def test_google_ai_studio_platform_exists(self):
        """Test that Google AI Studio platform is properly configured."""
        self.assertIn("google_ai_studio", self.ai_platforms, "Google AI Studio not found")
        
        google_ai = self.ai_platforms["google_ai_studio"]
        self.assertEqual(google_ai["name"], "Google AI Studio")
        self.assertEqual(google_ai["category"], "ai_development")

    def test_huggingface_platform_exists(self):
        """Test that Hugging Face Code platform is properly configured."""
        self.assertIn("huggingface_code", self.ai_platforms, "Hugging Face Code not found")
        
        hf = self.ai_platforms["huggingface_code"]
        self.assertEqual(hf["name"], "Hugging Face Code")
        self.assertEqual(hf["category"], "ai_development")

    def test_codegpt_platform_exists(self):
        """Test that CodeGPT platform is properly configured."""
        self.assertIn("codegpt", self.ai_platforms, "CodeGPT not found")
        
        codegpt = self.ai_platforms["codegpt"]
        self.assertEqual(codegpt["name"], "CodeGPT")
        self.assertEqual(codegpt["category"], "ai_development")

    def test_phind_platform_exists(self):
        """Test that Phind platform is properly configured."""
        self.assertIn("phind", self.ai_platforms, "Phind not found")
        
        phind = self.ai_platforms["phind"]
        self.assertEqual(phind["name"], "Phind")
        self.assertEqual(phind["category"], "ai_development")

    def test_supermaven_platform_exists(self):
        """Test that Supermaven platform is properly configured."""
        self.assertIn("supermaven", self.ai_platforms, "Supermaven not found")
        
        supermaven = self.ai_platforms["supermaven"]
        self.assertEqual(supermaven["name"], "Supermaven")
        self.assertEqual(supermaven["category"], "ai_development")

    def test_all_new_platforms_have_required_fields(self):
        """Test that all new platforms have required fields."""
        new_platforms = [
            "base44", "windsurf", "continue", "aider", "amazon_q",
            "google_ai_studio", "huggingface_code", "codegpt", "phind", "supermaven"
        ]
        
        for platform_id in new_platforms:
            with self.subTest(platform=platform_id):
                self.assertIn(platform_id, self.ai_platforms, 
                            f"Platform {platform_id} not found")
                
                platform = self.ai_platforms[platform_id]
                
                # Required fields
                self.assertIn("id", platform)
                self.assertIn("name", platform)
                self.assertIn("description", platform)
                self.assertIn("category", platform)
                self.assertIn("detection", platform)
                self.assertIn("project_config", platform)
                
                # Detection must have at least one pattern
                detection = platform["detection"]
                has_pattern = (
                    detection.get("files") or 
                    detection.get("dependencies") or
                    detection.get("folder_patterns") or
                    detection.get("commit_patterns")
                )
                self.assertTrue(has_pattern, 
                              f"Platform {platform_id} has no detection patterns")

    def test_platform_priority_values(self):
        """Test that new platforms have reasonable priority values."""
        new_platforms = [
            "base44", "windsurf", "continue", "aider", "amazon_q",
            "google_ai_studio", "huggingface_code", "codegpt", "phind", "supermaven"
        ]
        
        for platform_id in new_platforms:
            with self.subTest(platform=platform_id):
                platform = self.ai_platforms[platform_id]
                priority = platform.get("priority", 0)
                
                # Priority should be between 1 and 100
                self.assertGreaterEqual(priority, 1, 
                                      f"{platform_id} priority too low")
                self.assertLessEqual(priority, 100, 
                                   f"{platform_id} priority too high")

    def test_platform_detection_in_detector(self):
        """Test that new platforms are registered in platform detector."""
        from autopr.actions.platform_detector import PlatformDetector
        
        detector = PlatformDetector()
        
        new_platforms = [
            "base44", "windsurf", "continue", "aider", "amazon_q",
            "google_ai_studio", "huggingface_code", "codegpt", "phind", "supermaven"
        ]
        
        for platform_id in new_platforms:
            with self.subTest(platform=platform_id):
                self.assertIn(platform_id, detector.platform_signatures,
                            f"Platform {platform_id} not in detector signatures")


if __name__ == "__main__":
    unittest.main()
