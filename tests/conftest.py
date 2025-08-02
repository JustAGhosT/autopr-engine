"""Configuration and fixtures for pytest."""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from aiohttp import ClientSession


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create an instance of the default event loop for the test session.

    This fixture ensures that the event loop is properly closed after all tests.
    """
    # Create a new event loop for the test session
    loop = asyncio.new_event_loop()

    # Yield the event loop to the test
    yield loop

    # Clean up the event loop
    loop.close()


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
