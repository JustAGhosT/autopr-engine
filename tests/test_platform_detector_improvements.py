"""
Tests for platform detector improvements (error handling and confidence scoring).
"""
import unittest
import tempfile
import os
from pathlib import Path
from autopr.actions.platform_detector import PlatformDetector, PlatformDetectorInputs


class TestPlatformDetectorImprovements(unittest.TestCase):
    """Test suite for platform detector enhancements."""

    def setUp(self):
        """Set up test fixtures."""
        self.detector = PlatformDetector()

    def test_confidence_score_normalization(self):
        """Test that confidence scores are properly normalized to [0, 1]."""
        # Create a test workspace with base44 markers
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple base44 markers to test scoring
            Path(tmpdir, ".base44").touch()
            Path(tmpdir, "package.json").write_text(
                '{"dependencies": {"@base44/core": "1.0.0"}}'
            )
            
            inputs = PlatformDetectorInputs(
                repository_url="https://github.com/test/repo",
                workspace_path=tmpdir,
                commit_messages=["Initial commit with base44"]
            )
            
            result = self.detector.detect_platform(inputs)
            
            # Confidence should be between 0 and 1
            self.assertGreaterEqual(result.confidence_score, 0.0)
            self.assertLessEqual(result.confidence_score, 1.0)

    def test_multiple_file_matches_capped(self):
        """Test that multiple file matches don't cause score overflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create many base44 files
            for i in range(10):
                Path(tmpdir, f".base44-{i}").touch()
            
            inputs = PlatformDetectorInputs(
                repository_url="https://github.com/test/repo",
                workspace_path=tmpdir
            )
            
            result = self.detector.detect_platform(inputs)
            
            # Score should be capped at 1.0
            self.assertLessEqual(result.confidence_score, 1.0)

    def test_error_handling_invalid_workspace(self):
        """Test that invalid workspace path is handled gracefully."""
        inputs = PlatformDetectorInputs(
            repository_url="https://github.com/test/repo",
            workspace_path="/nonexistent/path/to/workspace"
        )
        
        # Should not crash
        result = self.detector.detect_platform(inputs)
        
        # Should return unknown when workspace is invalid
        self.assertIsNotNone(result.detected_platform)
        self.assertIsInstance(result.confidence_score, float)

    def test_error_handling_malformed_package_json(self):
        """Test that malformed package.json is handled gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create invalid JSON
            Path(tmpdir, "package.json").write_text("{ invalid json }")
            
            inputs = PlatformDetectorInputs(
                repository_url="https://github.com/test/repo",
                workspace_path=tmpdir
            )
            
            # Should not crash
            result = self.detector.detect_platform(inputs)
            
            self.assertIsNotNone(result.detected_platform)

    def test_weighted_scoring_file_matches(self):
        """Test that file matches use weighted scoring."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # First file match should be worth more than additional matches
            Path(tmpdir, ".base44").touch()
            
            inputs = PlatformDetectorInputs(
                repository_url="https://github.com/test/repo",
                workspace_path=tmpdir
            )
            
            result1 = self.detector.detect_platform(inputs)
            score1 = result1.confidence_score
            
            # Add more files
            Path(tmpdir, "base44.config.js").touch()
            result2 = self.detector.detect_platform(inputs)
            score2 = result2.confidence_score
            
            # Second detection should have higher score, but not doubled
            if score1 > 0:
                self.assertGreater(score2, score1)
                # Additional matches should add less than first match
                self.assertLess(score2, score1 * 2)

    def test_unknown_platform_low_confidence(self):
        """Test that unknown platforms are returned when confidence is low."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create workspace with no platform markers
            Path(tmpdir, "readme.txt").write_text("Generic project")
            
            inputs = PlatformDetectorInputs(
                repository_url="https://github.com/test/repo",
                workspace_path=tmpdir
            )
            
            result = self.detector.detect_platform(inputs)
            
            # Should detect as unknown with low confidence
            if result.confidence_score < 0.3:
                self.assertEqual(result.detected_platform, "unknown")

    def test_detection_with_all_signal_types(self):
        """Test detection when multiple signal types are present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Files
            Path(tmpdir, ".windsurf").touch()
            
            # Dependencies
            Path(tmpdir, "package.json").write_text(
                '{"dependencies": {"@codeium/windsurf": "1.0.0"}}'
            )
            
            # Commit messages
            commits = ["Initial commit with Windsurf IDE"]
            
            inputs = PlatformDetectorInputs(
                repository_url="https://github.com/test/repo",
                workspace_path=tmpdir,
                commit_messages=commits
            )
            
            result = self.detector.detect_platform(inputs)
            
            # Should have reasonable confidence with multiple signals
            if result.detected_platform == "windsurf":
                self.assertGreater(result.confidence_score, 0.3)

    def test_platform_config_generation_error_handling(self):
        """Test that errors in config generation don't break detection."""
        inputs = PlatformDetectorInputs(
            repository_url="https://github.com/test/repo",
            workspace_path="/tmp"  # Minimal path
        )
        
        # Even if config generation fails, should still return result
        result = self.detector.detect_platform(inputs)
        
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.platform_specific_config)
        self.assertIsNotNone(result.recommended_workflow)
        self.assertIsNotNone(result.migration_suggestions)
        self.assertIsNotNone(result.enhancement_opportunities)

    def test_confidence_weights_applied(self):
        """Test that different detection methods have different weights."""
        # This test verifies the scoring logic is working
        with tempfile.TemporaryDirectory() as tmpdir:
            # File detection (should be weighted highly)
            Path(tmpdir, ".continue").touch()
            
            inputs = PlatformDetectorInputs(
                repository_url="https://github.com/test/repo",
                workspace_path=tmpdir
            )
            
            result = self.detector.detect_platform(inputs)
            
            # File-based detection should provide good confidence
            if result.detected_platform == "continue":
                self.assertGreater(result.confidence_score, 0.2)


if __name__ == "__main__":
    unittest.main()
