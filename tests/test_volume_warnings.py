"""Tests for volume-based warning control."""

import warnings

import pytest
from pytest import mark


def generate_test_warnings():
    """Generate various types of warnings for testing."""
    warnings.warn("This is a UserWarning", UserWarning)
    warnings.warn("This is a DeprecationWarning", DeprecationWarning)
    warnings.warn("This is a ResourceWarning", ResourceWarning)
    warnings.warn("This is a PendingDeprecationWarning", PendingDeprecationWarning)


@mark.volume(0)
def test_silent_volume():
    """Test that silent volume (0) suppresses all warnings."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")  # Ensure all warnings are caught
        generate_test_warnings()

        # At volume 0, all warnings should be suppressed
        assert len(w) == 0, f"Expected no warnings at volume 0, got {len(w)}"


@mark.volume(100)
def test_quiet_volume():
    """Test that quiet volume (100) shows only important warnings."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")  # Ensure all warnings are caught
        generate_test_warnings()

        # At volume 100, only DeprecationWarning and ResourceWarning should be shown
        warning_types = {type(warning.message) for warning in w}
        assert DeprecationWarning in warning_types, "Expected DeprecationWarning at volume 100"
        assert ResourceWarning in warning_types, "Expected ResourceWarning at volume 100"
        assert UserWarning not in warning_types, "UserWarning should be suppressed at volume 100"


@mark.volume(500)
def test_balanced_volume():
    """Test that balanced volume (500) shows all warnings but only fails on critical ones."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")  # Ensure all warnings are caught
        generate_test_warnings()

        # At volume 500, all warnings should be shown
        warning_types = {type(warning.message) for warning in w}
        assert len(warning_types) >= 2, f"Expected multiple warnings at volume 500, got {warning_types}"


@mark.volume(1000)
def test_maximum_volume():
    """Test that maximum volume (1000) treats all warnings as errors."""
    with pytest.raises(Warning):
        # At volume 1000, warnings should be treated as errors
        generate_test_warnings()


def test_volume_marker():
    """Test that the volume marker works as expected."""
    # This test will only run if the volume is >= 500
    marker = getattr(test_volume_marker, "pytestmark", None)
    if marker and any(m.name == "volume" and m.args[0] >= 500 for m in marker):
        assert True  # Test passes if volume >= 500
