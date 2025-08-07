"""Configuration and fixtures for pytest.

This module includes volume-based warning control and other test configurations.
"""

import asyncio
import os
import sys
import warnings
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections.abc import AsyncGenerator, Generator

# Add the project root to the Python path
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
import pytest_asyncio
import toml
from aiohttp import ClientSession

# Import volume utilities
from autopr.utils.volume_utils import get_volume_level_name

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
    # Load the pyproject.toml file
    pyproject_path = Path(__file__).parent / "pyproject.toml"
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
    
    # Get the warning filters for the selected volume level
    return volume_warnings.get(str(selected_level), ["ignore"])


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
    if 'AUTOPR_TEST_VOLUME_LEVEL' not in os.environ:
        os.environ['AUTOPR_TEST_VOLUME_LEVEL'] = '500'  # Default to balanced mode for tests
        
    volume = get_volume_level()
    warning_filters = get_warning_filters(volume)
    
    # Apply the warning filters
    apply_warning_filters(warning_filters)
    
    # Add a custom marker for volume-based tests
    config.addinivalue_line(
        "markers",
        "volume(level): Mark test to run only at or above the specified volume level"
    )
    
    # Set a custom marker for the current volume level
    current_mark = config.option.markexpr or 'True'
    config.option.markexpr = f"volume<={volume} and {current_mark}"
    
    # Print test configuration for debugging
    print(f"\n=== Test Configuration ===")
    print(f"Volume level: {volume} ({get_volume_level_name(volume)})")
    print(f"Warning filters: {warning_filters}")
    print(f"Active markers: {config.option.markexpr}")
    print("======================\n")


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create an instance of the default event loop for the test session.

    This fixture ensures that the event loop is properly closed after all tests.
    """
    # Create a new event loop for the test session
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Yield the event loop to the test
        yield loop
    finally:
        # Clean up the event loop
        loop.close()
        asyncio.set_event_loop(None)


@pytest.fixture(scope="session", autouse=True)
def configure_warnings():
    """Configure warnings based on the current volume level."""
    volume = get_volume_level()
    warning_filters = get_warning_filters(volume)
    apply_warning_filters(warning_filters)
    
    # Log the current warning configuration
    print(f"\n[Volume: {volume} - {get_volume_level_name(volume)}]")
    print("Warning filters:")
    for f in warning_filters:
        print(f"  {f}")
    print()


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
