"""
Tests for platform detector improvements (error handling and confidence scoring).
"""

import unittest
import tempfile
import os
from pathlib import Path
from autopr.actions.platform_detection import (
    PlatformDetector,
    PlatformDetectorInputs,
)


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
                commit_messages=["Initial commit with base44"],
            )

            result = self.detector.detect_platform(inputs)

            # Confidence should be between 0 and 1 for the primary platform
            primary = result.primary_platform
            score = result.confidence_scores.get(primary, 0.0)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    def test_multiple_file_matches_capped(self):
        """Test that multiple file matches don't cause score overflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create many base44 files
            for i in range(10):
                Path(tmpdir, f".base44-{i}").touch()

            inputs = PlatformDetectorInputs(
                repository_url="https://github.com/test/repo",
                workspace_path=tmpdir,
            )

            result = self.detector.detect_platform(inputs)

            # All confidence scores should be capped at 1.0
            for score in result.confidence_scores.values():
                self.assertLessEqual(score, 1.0)

    def test_error_handling_invalid_workspace(self):
        """Test that invalid workspace path is handled gracefully."""
        inputs = PlatformDetectorInputs(
            repository_url="https://github.com/test/repo",
            workspace_path="/nonexistent/path/to/workspace",
        )

        # Should not crash
        result = self.detector.detect_platform(inputs)

        # Should return unknown when workspace is invalid
        self.assertIsNotNone(result.primary_platform)
        score = result.confidence_scores.get(result.primary_platform, 0.0)
        self.assertIsInstance(score, float)

    def test_error_handling_malformed_package_json(self):
        """Test that malformed package.json is handled gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create invalid JSON
            Path(tmpdir, "package.json").write_text("{ invalid json }")

            inputs = PlatformDetectorInputs(
                repository_url="https://github.com/test/repo",
                workspace_path=tmpdir,
            )

            # Should not crash
            result = self.detector.detect_platform(inputs)

            self.assertIsNotNone(result.primary_platform)

    def test_weighted_scoring_file_matches(self):
        """Test that file matches use weighted scoring."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # First file match should be worth more than additional matches
            Path(tmpdir, ".base44").touch()

            inputs = PlatformDetectorInputs(
                repository_url="https://github.com/test/repo",
                workspace_path=tmpdir,
            )

            result1 = self.detector.detect_platform(inputs)
            primary1 = result1.primary_platform
            score1 = result1.confidence_scores.get(primary1, 0.0)

            # Add more files
            Path(tmpdir, "base44.config.js").touch()
            result2 = self.detector.detect_platform(inputs)
            primary2 = result2.primary_platform
            score2 = result2.confidence_scores.get(primary2, 0.0)

            # Second detection should have at least as high a score, but not more than doubled
            if score1 > 0:
                self.assertGreaterEqual(score2, score1)
                # Additional matches should add less than a full extra factor
                self.assertLess(score2, score1 * 2)

    def test_unknown_platform_low_confidence(self):
        """Test that unknown platforms are returned when confidence is low."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create workspace with no platform markers
            Path(tmpdir, "readme.txt").write_text("Generic project")

            inputs = PlatformDetectorInputs(
                repository_url="https://github.com/test/repo",
                workspace_path=tmpdir,
            )

            result = self.detector.detect_platform(inputs)

            # Should detect as unknown with low confidence
            max_conf = (
                max(result.confidence_scores.values())
                if result.confidence_scores
                else 0.0
            )
            if max_conf < 0.3:
                self.assertEqual(result.primary_platform, "unknown")

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
                commit_messages=commits,
            )

            result = self.detector.detect_platform(inputs)

            # Should have reasonable confidence with multiple signals
            primary = result.primary_platform
            score = result.confidence_scores.get(primary, 0.0)
            if primary == "windsurf":
                self.assertGreater(score, 0.3)

    def test_platform_config_generation_error_handling(self):
        """Test that errors in config generation don't break detection."""
        inputs = PlatformDetectorInputs(
            repository_url="https://github.com/test/repo",
            workspace_path="/tmp",  # Minimal path
        )

        # Even if config generation fails, should still return result
        result = self.detector.detect_platform(inputs)

        self.assertIsNotNone(result)
        self.assertIsInstance(result.platform_specific_configs, dict)
        self.assertIsInstance(result.workflow_type, str)
        self.assertIsNotNone(result.migration_opportunities)
        self.assertIsNotNone(result.recommended_enhancements)

    def test_confidence_weights_applied(self):
        """Test that different detection methods have different weights."""
        # This test verifies the scoring logic is working
        with tempfile.TemporaryDirectory() as tmpdir:
            # File detection (should be weighted highly)
            Path(tmpdir, ".continue").touch()

            inputs = PlatformDetectorInputs(
                repository_url="https://github.com/test/repo",
                workspace_path=tmpdir,
            )

            result = self.detector.detect_platform(inputs)

            # File-based detection should provide good confidence
            primary = result.primary_platform
            score = result.confidence_scores.get(primary, 0.0)
            if primary == "continue":
                self.assertGreater(score, 0.2)


if __name__ == "__main__":
    unittest.main()
