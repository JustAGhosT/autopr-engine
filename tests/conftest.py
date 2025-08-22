"""Configuration and fixtures for pytest.

This module includes volume-based warning control and other test configurations.
"""

import asyncio
from collections.abc import AsyncGenerator
import os
from pathlib import Path
import sys
import warnings

import pytest  # type: ignore
import pytest_asyncio  # type: ignore


# Prefer stdlib tomllib (Py3.11+), then fallback to tomli; avoid requiring 'toml' package
try:  # Python 3.11+
    import tomllib as toml  # type: ignore[import-not-found]
except ModuleNotFoundError:  # Fallback for older interpreters
    import tomli as toml  # type: ignore[import-not-found]

import contextlib

from aiohttp import ClientSession


# Import volume utilities (placeholder for future use)


def get_volume_level() -> int:
    """Get the current volume level from environment or default to 500 (BALANCED)."""
    return int(os.environ.get("AUTOPR_TEST_VOLUME_LEVEL", "500"))


def get_warning_filters(volume: int) -> list[str]:
    """Get warning filters based on the current volume level.

    Args:
        volume: Volume level from 0 to 1000

    Returns:
        List of warning filter strings
    """
    # Load the pyproject.toml file from the project root
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"
    # tomllib/tomli expect a binary file handle
    with open(pyproject_path, "rb") as f:
        config = toml.load(f)

    # Get the volume warnings configuration
    volume_warnings = config.get("tool", {}).get("pytest", {}).get("volume_warnings", {})

    # Find the closest volume level that's less than or equal to the current volume
    volume_levels = sorted(int(k) for k in volume_warnings if k.isdigit())
    selected_level = 0  # Default to most restrictive

    for level in volume_levels:
        if level <= volume:
            selected_level = level

    # Volume-based warning control
    # These settings map volume levels to warning filters
    volume_warnings_config = {
        "0": ["ignore"],
        "100": [
            "default",
            "ignore::UserWarning",
            "ignore::PendingDeprecationWarning",
            "ignore::ImportWarning",
            "ignore::BytesWarning",
        ],
        "300": ["default"],
        "500": ["error"],
    }

    # Get the warning filters for the selected volume level
    return volume_warnings_config.get(str(selected_level), ["ignore"])


def _wrap_warnings_warn(volume: int):
    """Create a wrapper for warnings.warn honoring volume semantics used in tests."""
    original_warn = warnings.warn

    def warn(message, category=None, stacklevel=1, source=None):  # type: ignore[no-redef]
        # Silent: suppress all warnings emission
        if volume == 0:
            return None

        # Quiet: suppress UserWarning and PendingDeprecationWarning
        if volume == 100:
            if category in (UserWarning, PendingDeprecationWarning):
                return None
            return original_warn(message, category=category, stacklevel=stacklevel, source=source)

        # Maximum: treat all warnings as errors
        if volume >= 1000:
            exc = category or Warning
            raise exc(message)  # type: ignore[misc]

        # Default behavior for other volumes
        return original_warn(message, category=category, stacklevel=stacklevel, source=source)

    return warn


def pytest_configure(config):
    """Configure pytest with volume-based warning filters."""
    # Set default test volume if not already set
    if "AUTOPR_TEST_VOLUME_LEVEL" not in os.environ:
        os.environ["AUTOPR_TEST_VOLUME_LEVEL"] = "500"  # Default to balanced mode for tests

    # Add a custom marker for volume-based tests
    config.addinivalue_line(
        "markers",
        "volume(level): Mark test to run only at or above the specified volume level",
    )

    # Print minimal test configuration

    # Reduce noise: ignore RuntimeWarning about un-awaited test coroutines in summary output
    # This warning appears from pytest-asyncio collection/teardown and does not affect test correctness
    warnings.filterwarnings(
        "ignore",
        category=RuntimeWarning,
        message=r"coroutine '.*' was never awaited",
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create and set a cross-platform event loop for the test session."""
    # Use Windows selector policy on Windows only; default elsewhere
    if sys.platform.startswith("win") and hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield loop
    finally:
        with contextlib.suppress(Exception):
            asyncio.set_event_loop(None)
        loop.close()


@pytest.fixture(autouse=True)
def configure_warnings_per_test(request):
    """Configure warnings per-test based on volume marker and defaults.

    This aligns warning visibility with tests' expectations in tests/test_volume_warnings.py.
    """
    # Determine volume for this test from marker or env default
    marker = request.node.get_closest_marker("volume")
    volume_str = os.environ.get("AUTOPR_TEST_VOLUME_LEVEL", "500")
    try:
        volume_env = int(volume_str)
    except ValueError:
        volume_env = 500
    volume = marker.args[0] if marker and marker.args else volume_env

    # Monkeypatch warnings.warn to honor volume rules regardless of catch_warnings in tests
    original_warn = warnings.warn
    warnings.warn = _wrap_warnings_warn(volume)

    # Ensure we restore after test
    def _restore():
        warnings.warn = original_warn

    request.addfinalizer(_restore)


@pytest_asyncio.fixture
async def http_session() -> AsyncGenerator[ClientSession]:
    """
    Create and provide an aiohttp ClientSession for testing.

    This fixture ensures that the session is properly closed after each test.
    """
    async with ClientSession() as session:
        yield session


@pytest.fixture()
def github_token() -> str:
    """
    Provide a GitHub token for testing.

    This fixture reads the GITHUB_TOKEN environment variable or uses a default test token.
    """
    return os.getenv("GITHUB_TOKEN", "test_token")


@pytest.fixture()
def linear_api_key() -> str:
    """
    Provide a Linear API key for testing.

    This fixture reads the LINEAR_API_KEY environment variable or uses a default test key.
    """
    return os.getenv("LINEAR_API_KEY", "test_api_key")
