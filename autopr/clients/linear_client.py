"""Linear API client implementation."""

import logging
import os
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class LinearClient:
    """Simple Linear API client for AutoPR."""

    def __init__(self, api_key: str | None = None):
        """Initialize the Linear client.

        Args:
            api_key: Linear API key. If not provided, will try to get from LINEAR_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("LINEAR_API_KEY")
        if not self.api_key:
            logger.warning(
                "No Linear API key provided and LINEAR_API_KEY environment variable not set"
            )

        self.base_url = "https://api.linear.app/graphql"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def query(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a GraphQL query against the Linear API."""
        data = {"query": query, "variables": variables or {}}

        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_url, headers=self.headers, json=data) as response:
                response.raise_for_status()
                result = await response.json()

                if "errors" in result:
                    error_messages = [
                        e.get("message", "Unknown error") for e in result.get("errors", [])
                    ]
                    msg = f"Linear API error: {', '.join(error_messages)}"
                    raise Exception(msg)

                return result.get("data", {})

    # Add more Linear API methods as needed
