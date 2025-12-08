"""
Tests for Dashboard Security

Tests path validation and directory traversal prevention (BUG-6 fix).

NOTE: These tests validate the security patterns in the DashboardState class
which provides path validation and sanitization for the FastAPI dashboard.
"""

from pathlib import Path
import pytest
import tempfile
import os

# Try to import the dashboard state, but skip tests if dependencies not available
pytest.importorskip("pydantic", reason="Dashboard dependencies not installed")

try:
    from codeflow_engine.dashboard.router import DashboardState
except ImportError:
    pytest.skip("Dashboard module not available", allow_module_level=True)


@pytest.fixture
def dashboard():
    """Create dashboard state instance for testing."""
    return DashboardState()


@pytest.fixture
def temp_test_dir():
    """Create temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some test files
        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("# Test file\nprint('hello')\n")

        subdir = Path(tmpdir) / "subdir"
        subdir.mkdir()
        (subdir / "nested.py").write_text("# Nested file\n")

        yield tmpdir


class TestPathValidation:
    """Tests for path validation to prevent directory traversal attacks."""

    def test_validate_path_in_allowed_directory(self, dashboard, temp_test_dir):
        """Test that paths within allowed directories are accepted."""
        # Add temp dir to allowed directories
        dashboard._allowed_directories.append(Path(temp_test_dir))

        # Test file in allowed directory
        test_file = os.path.join(temp_test_dir, "test.py")
        is_valid, error = dashboard.validate_path(test_file)

        assert is_valid is True
        assert error is None

    def test_validate_path_outside_allowed_directory(self, dashboard):
        """Test that paths outside allowed directories are rejected."""
        # Try to access /etc/passwd (outside allowed directories)
        is_valid, error = dashboard.validate_path("/etc/passwd")

        assert is_valid is False
        assert "outside allowed directories" in error.lower()

    def test_validate_path_traversal_attempt(self, dashboard, temp_test_dir):
        """Test that directory traversal attempts are blocked."""
        # Add temp dir to allowed directories
        dashboard._allowed_directories.append(Path(temp_test_dir))

        # Try to escape using ../../../
        traversal_path = os.path.join(temp_test_dir, "..", "..", "..", "etc", "passwd")
        is_valid, error = dashboard.validate_path(traversal_path)

        # Should be rejected as it resolves outside allowed directories
        assert is_valid is False
        assert "outside allowed directories" in error.lower()

    def test_validate_nonexistent_path(self, dashboard, temp_test_dir):
        """Test that non-existent paths are rejected."""
        # Add temp dir to allowed directories
        dashboard._allowed_directories.append(Path(temp_test_dir))

        nonexistent = os.path.join(temp_test_dir, "nonexistent.py")
        is_valid, error = dashboard.validate_path(nonexistent)

        assert is_valid is False
        assert "does not exist" in error.lower()

    def test_validate_path_with_symlink_escape(self, dashboard, temp_test_dir):
        """Test that symlinks pointing outside allowed directories are blocked."""
        # Add temp dir to allowed directories
        dashboard._allowed_directories.append(Path(temp_test_dir))

        # Create symlink to /etc
        symlink_path = os.path.join(temp_test_dir, "escape_link")
        try:
            os.symlink("/etc", symlink_path)

            # Try to access through symlink
            is_valid, error = dashboard.validate_path(symlink_path)

            # Should be rejected as it points outside allowed directories
            assert is_valid is False
            assert "outside allowed directories" in error.lower()
        except OSError:
            # Symlink creation might fail on some systems, skip test
            pytest.skip("Cannot create symlinks on this system")

    def test_validate_path_resolves_correctly(self, dashboard, temp_test_dir):
        """Test that path resolution handles . and .. correctly."""
        # Add temp dir to allowed directories
        dashboard._allowed_directories.append(Path(temp_test_dir))

        # Path with . and .. that stays within allowed directory
        complex_path = os.path.join(temp_test_dir, "subdir", "..", "test.py")
        is_valid, error = dashboard.validate_path(complex_path)

        assert is_valid is True
        assert error is None


class TestFileListSanitization:
    """Tests for file list validation and sanitization."""

    def test_sanitize_valid_file_list(self, dashboard, temp_test_dir):
        """Test that valid file lists are properly sanitized."""
        # Add temp dir to allowed directories
        dashboard._allowed_directories.append(Path(temp_test_dir))

        files = [
            os.path.join(temp_test_dir, "test.py"),
            os.path.join(temp_test_dir, "subdir", "nested.py"),
        ]

        valid_files, errors = dashboard.sanitize_file_list(files)

        assert len(valid_files) == 2
        assert len(errors) == 0

        # Verify paths are resolved to absolute
        for file_path in valid_files:
            assert os.path.isabs(file_path)

    def test_sanitize_mixed_file_list(self, dashboard, temp_test_dir):
        """Test that mixed valid/invalid file lists are properly filtered."""
        # Add temp dir to allowed directories
        dashboard._allowed_directories.append(Path(temp_test_dir))

        files = [
            os.path.join(temp_test_dir, "test.py"),  # Valid
            "/etc/passwd",  # Invalid - outside allowed
            os.path.join(temp_test_dir, "nonexistent.py"),  # Invalid - doesn't exist
        ]

        valid_files, errors = dashboard.sanitize_file_list(files)

        assert len(valid_files) == 1
        assert len(errors) == 2

        # Verify error messages are descriptive
        assert any("outside allowed directories" in err.lower() for err in errors)
        assert any("does not exist" in err.lower() for err in errors)

    def test_sanitize_empty_file_list(self, dashboard):
        """Test that empty file lists are handled correctly."""
        valid_files, errors = dashboard.sanitize_file_list([])

        assert len(valid_files) == 0
        assert len(errors) == 0

    def test_sanitize_file_list_with_traversal(self, dashboard, temp_test_dir):
        """Test that file lists with traversal attempts are filtered."""
        # Add temp dir to allowed directories
        dashboard._allowed_directories.append(Path(temp_test_dir))

        files = [
            os.path.join(temp_test_dir, "..", "..", "etc", "passwd"),
        ]

        valid_files, errors = dashboard.sanitize_file_list(files)

        assert len(valid_files) == 0
        assert len(errors) == 1
        assert "outside allowed directories" in errors[0].lower()


class TestSecurityIntegration:
    """Integration tests for security features."""

    def test_allowed_directories_configured(self, dashboard):
        """Test that allowed directories are properly configured."""
        # Should have at least current working directory
        assert len(dashboard._allowed_directories) > 0

        # All should be absolute paths
        for directory in dashboard._allowed_directories:
            assert directory.is_absolute()

    def test_path_validation_prevents_common_attacks(self, dashboard):
        """Test that common directory traversal attacks are prevented."""
        attack_paths = [
            "/etc/passwd",
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/var/log/syslog",
            "../../../../proc/self/environ",
            "file:///etc/passwd",
        ]

        for attack_path in attack_paths:
            is_valid, error = dashboard.validate_path(attack_path)

            # All should be rejected
            assert is_valid is False, f"Attack path '{attack_path}' was not blocked!"
            assert error is not None

    def test_null_byte_injection_prevented(self, dashboard):
        """Test that null byte injection is prevented."""
        # Null byte injection attempt
        attack_path = "safe_file.txt\x00../../etc/passwd"

        is_valid, error = dashboard.validate_path(attack_path)

        # Should be rejected (either as invalid path or outside allowed dirs)
        assert is_valid is False

    def test_unicode_normalization_attacks(self, dashboard):
        """Test that Unicode normalization attacks are handled."""
        # Unicode dot variations
        unicode_attacks = [
            "safe\u2024\u2024/etc/passwd",  # ONE DOT LEADER
            "safe\uFF0E\uFF0E/etc/passwd",  # FULLWIDTH FULL STOP
        ]

        for attack_path in unicode_attacks:
            is_valid, error = dashboard.validate_path(attack_path)

            # Should be rejected
            assert is_valid is False


class TestAllowedDirectoriesConfiguration:
    """Tests for allowed directories configuration."""

    def test_default_allowed_directories(self, dashboard):
        """Test that default allowed directories are reasonable."""
        allowed = dashboard._allowed_directories

        # Should include current working directory
        cwd = Path.cwd().resolve()
        assert any(cwd == allowed_dir for allowed_dir in allowed)

        # Should include home directory
        home = Path.home().resolve()
        assert any(home == allowed_dir for allowed_dir in allowed)

    def test_can_add_custom_allowed_directory(self, dashboard, temp_test_dir):
        """Test that custom allowed directories can be added."""
        temp_path = Path(temp_test_dir)

        # Add to allowed directories
        dashboard._allowed_directories.append(temp_path)

        # Verify it's in the list
        assert temp_path in dashboard._allowed_directories

        # Verify files in this directory can now be validated
        test_file = os.path.join(temp_test_dir, "test.py")
        is_valid, error = dashboard.validate_path(test_file)

        assert is_valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
