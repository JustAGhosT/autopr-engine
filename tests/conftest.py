"""Configuration and fixtures for pytest.

This module includes volume-based warning control and other test configurations.
"""

import asyncio
import os
import warnings
import sys
from pathlib import Path
from typing import List
from collections.abc import AsyncGenerator

import pytest  # type: ignore
import pytest_asyncio  # type: ignore
import toml  # type: ignore
from aiohttp import ClientSession

# Import volume utilities (placeholder for future use)


def get_volume_level() -> int:
    """Get the current volume level from environment or default to 500 (BALANCED)."""
    return int(os.environ.get("AUTOPR_TEST_VOLUME_LEVEL", "500"))


def get_warning_filters(volume: int) -> List[str]:
    """Get warning filters based on the current volume level.

    Args:
        volume: Volume level from 0 to 1000

    Returns:
        List of warning filter strings
    """
    # Load the pyproject.toml file from the project root
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"
    with open(pyproject_path) as f:
        config = toml.load(f)

    # Get the volume warnings configuration
    volume_warnings = config.get("tool", {}).get("pytest", {}).get("volume_warnings", {})

    # Find the closest volume level that's less than or equal to the current volume
    volume_levels = sorted(int(k) for k in volume_warnings.keys() if k.isdigit())
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


def apply_warning_filters(filters: List[str]) -> None:
    """Apply warning filters to the warnings module.

    Args:
        filters: List of warning filter strings
    """
    # Clear existing filters
    warnings.resetwarnings()

    # Apply each filter
    for filter_str in filters:
        warnings.filterwarnings(filter_str)

    # Always show ResourceWarning in tests to catch unclosed resources
    warnings.simplefilter("always", ResourceWarning)
    warnings.simplefilter("always", DeprecationWarning)


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
    print("\n=== Test Configuration ===")
    print("Running with default test configuration")
    print("======================\n")


@pytest.fixture(scope="session")
def event_loop():
    """Create a cross-platform event loop for the test session."""
    # Use Windows selector policy on Windows only; default elsewhere
    if sys.platform.startswith("win") and hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()


@pytest.fixture(scope="session", autouse=True)
def configure_warnings():
    """Configure warnings for the test session."""
    # Simple warning configuration
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=ResourceWarning)
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=RuntimeWarning)


@pytest_asyncio.fixture
async def http_session() -> AsyncGenerator[ClientSession, None]:
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
