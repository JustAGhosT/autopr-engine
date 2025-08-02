"""GitHub API client for AutoPR with retry logic and rate limiting."""

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, TypeVar, Union

from aiohttp import ClientError, ClientResponse, ClientResponseError, ClientSession, ClientTimeout

# Default configuration constants
DEFAULT_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 0.5
DEFAULT_TIMEOUT = 30

# Type variable for generic response type
T = TypeVar("T")


@dataclass
class GitHubError(Exception):
    """Base exception for GitHub API errors."""

    message: str
    status_code: int | None = None
    response: Any | None = None

    def __str__(self) -> str:
        if self.status_code:
            return f"{self.message} (status: {self.status_code})"
        return self.message


class RateLimitExceeded(GitHubError):
    """Raised when GitHub API rate limit is exceeded."""

    def __init__(
        self,
        message: str = "GitHub API rate limit exceeded",
        status_code: int | None = 403,
        response: Any | None = None,
        reset_time: datetime | None = None,
    ) -> None:
        super().__init__(message, status_code, response)
        self.reset_time = reset_time or datetime.now(UTC)


class GitHubConfig:
    """Configuration for GitHub API client."""

    def __init__(
        self,
        token: str,
        base_url: str = "https://api.github.com",
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        user_agent: str = "AutoPR-GitHub-Client/1.0",
    ) -> None:
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.user_agent = user_agent
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": user_agent,
        }


# Type variable for JSON-serializable data
JSONType = Union[dict[str, Any], list[Any], str, int, float, bool, None]


class GitHubClient:
    """Asynchronous client for interacting with the GitHub API.

    This client handles authentication, rate limiting, and provides methods to interact
    with the GitHub API. It supports both REST API and GraphQL endpoints with retry logic.

    Args:
        config: GitHubConfig instance with client configuration
        session: Optional aiohttp ClientSession to use. If not provided, a new one will be created.
    """

    def __init__(
        self,
        config: GitHubConfig,
        session: ClientSession | None = None,
    ) -> None:
        self.config = config
        self._session = session
        self._session_owner = session is None
        self.logger = logging.getLogger(__name__)
        self.rate_limit_remaining = 5000  # Default rate limit
        self.rate_limit_reset = 0  # Timestamp when rate limit resets

    async def _get_session(self) -> ClientSession:
        """Get or create an aiohttp ClientSession.

        Returns:
            An aiohttp ClientSession instance
        """
        if self._session is None or self._session.closed:
            self._session = ClientSession(
                headers=self.config.headers, timeout=ClientTimeout(total=self.config.timeout)
            )
            self._session_owner = True
        return self._session

    async def _calculate_backoff(self, attempt: int) -> float:
        """Calculate backoff time with jitter to prevent thundering herd.

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Time to sleep in seconds
        """
        jitter = random.uniform(0, 0.1)  # Add up to 10% jitter  # - Used for backoff, not security
        backoff_time = min(
            (2**attempt) * self.config.backoff_factor * (1 + jitter), 60
        )  # Max 60 seconds
        return float(backoff_time)

    async def _handle_rate_limit(self, response: ClientResponse) -> None:
        """Update rate limit information from response headers.

        Args:
            response: The HTTP response from GitHub API
        """
        if "X-RateLimit-Remaining" in response.headers:
            self.rate_limit_remaining = int(response.headers["X-RateLimit-Remaining"])
        if "X-RateLimit-Reset" in response.headers:
            self.rate_limit_reset = int(response.headers["X-RateLimit-Reset"])

    async def _check_rate_limit(self) -> None:
        """Check if we're approaching rate limits and wait if needed."""
        now = time.time()
        if self.rate_limit_remaining < 100 and now < self.rate_limit_reset:
            sleep_time = max(1, self.rate_limit_reset - now + 1)  # Add 1s buffer
            self.logger.warning(f"Approaching rate limit. Waiting {sleep_time:.1f}s until reset")
            await asyncio.sleep(sleep_time)

    async def _request(self, method: str, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """Make an HTTP request with retry logic and rate limit handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/repos/owner/repo")
            **kwargs: Additional arguments to pass to the request

        Returns:
            Dict containing the JSON response

        Raises:
            GitHubError: For GitHub API errors
            RateLimitExceeded: When rate limited
            ClientError: For network or other client errors
        """
        url = f"{self.config.base_url}{endpoint}"
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                # Check rate limits before making the request
                await self._check_rate_limit()

                self.logger.debug(
                    f"{method} {url} (attempt {attempt + 1}/{self.config.max_retries + 1})"
                )

                async with self._get_session() as session:
                    async with session.request(method, url, **kwargs) as response:
                        # Update rate limit info from response
                        await self._handle_rate_limit(response)

                        if response.status == 403 and "X-RateLimit-Remaining" in response.headers:
                            if int(response.headers["X-RateLimit-Remaining"]) == 0:
                                reset_time = int(
                                    response.headers.get("X-RateLimit-Reset", time.time() + 60)
                                )
                                sleep_time = max(1, reset_time - time.time() + 1)  # Add 1s buffer
                                self.logger.warning(
                                    f"Rate limited. Waiting {sleep_time:.1f}s until reset"
                                )
                                await asyncio.sleep(sleep_time)
                                continue  # Retry the request after waiting

                        response.raise_for_status()

                        # Handle different response types
                        content_type = response.headers.get("Content-Type", "")
                        if "application/json" in content_type:
                            return await response.json()
                        if content_type.startswith("text/"):
                            return {"text": await response.text()}
                        return {}

            except ClientResponseError as e:
                if e.status == 403 and "rate limit" in (e.message or "").lower():
                    last_error = RateLimitExceeded(
                        "GitHub API rate limit exceeded",
                        status_code=e.status,
                        response=e.request_info,
                    )
                else:
                    last_error = GitHubError(
                        f"GitHub API request failed: {e}",
                        status_code=e.status,
                        response=e.request_info,
                    )

                # Don't retry on client errors (4xx) except for rate limits
                if 400 <= (e.status or 0) < 500 and e.status != 429:
                    break

            except (TimeoutError, ClientError) as e:
                last_error = e

            # If we have retries left, wait before retrying
            if attempt < self.config.max_retries:
                backoff = await self._calculate_backoff(attempt)
                self.logger.warning(
                    f"Request failed (attempt {attempt + 1}/{self.config.max_retries + 1}). "
                    f"Retrying in {backoff:.2f}s..."
                )
                await asyncio.sleep(backoff)

        # If we get here, all retries failed
        if last_error:
            raise last_error
        msg = "Request failed after all retries"
        raise GitHubError(msg)

    async def get(self, endpoint: str, **kwargs) -> dict[str, Any]:
        """Make a GET request to the GitHub API.

        Args:
            endpoint: API endpoint (e.g., "/repos/owner/repo")
            **kwargs: Additional arguments to pass to the request

        Returns:
            Dict containing the JSON response
        """
        return await self._request("GET", endpoint, **kwargs)

    async def post(
        self, endpoint: str, data: dict[str, Any] | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """Make a POST request to the GitHub API.

        Args:
            endpoint: API endpoint
            data: JSON-serializable data to send in the request body
            **kwargs: Additional arguments to pass to the request

        Returns:
            Dict containing the JSON response
        """
        if data is not None:
            kwargs["json"] = data
        return await self._request("POST", endpoint, **kwargs)

    async def put(
        self, endpoint: str, data: dict[str, Any] | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """Make a PUT request to the GitHub API.

        Args:
            endpoint: API endpoint
            data: JSON-serializable data to send in the request body
            **kwargs: Additional arguments to pass to the request

        Returns:
            Dict containing the JSON response
        """
        if data is not None:
            kwargs["json"] = data
        return await self._request("PUT", endpoint, **kwargs)

    async def patch(
        self, endpoint: str, data: dict[str, Any] | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """Make a PATCH request to the GitHub API.

        Args:
            endpoint: API endpoint
            data: JSON-serializable data to send in the request body
            **kwargs: Additional arguments to pass to the request

        Returns:
            Dict containing the JSON response
        """
        if data is not None:
            kwargs["json"] = data
        return await self._request("PATCH", endpoint, **kwargs)

    async def delete(self, endpoint: str, **kwargs: Any) -> bool:
        """Make a DELETE request to the GitHub API.

        Args:
            endpoint: API endpoint
            **kwargs: Additional arguments to pass to the request

        Returns:
            bool: True if the resource was successfully deleted (status 204)

        Raises:
            GitHubError: If the request fails
        """
        response = await self._request("DELETE", endpoint, **kwargs)
        return response.get("status", 0) == 204

    async def graphql(
        self, query: str, variables: dict[str, Any] | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """Execute a GraphQL query against the GitHub API.

        Args:
            query: The GraphQL query string
            variables: Variables for the GraphQL query
            **kwargs: Additional arguments to pass to the request

        Returns:
            Dict containing the GraphQL response data

        Raises:
            GitHubError: If the request fails or contains errors
        """
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        response = await self.post("/graphql", data=payload, **kwargs)

        if "errors" in response:
            errors = response.get("errors", [])
            error_messages = [e.get("message", "Unknown error") for e in errors]
            msg = f"GraphQL errors: {', '.join(error_messages)}"
            raise GitHubError(msg, response=response)

        return response.get("data", {})

    async def close(self) -> None:
        """Close the underlying HTTP session if it was created by this client."""
        if self._session_owner and self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> "GitHubClient":
        """Async context manager entry."""
        await self._get_session()
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any
    ) -> None:
        """Async context manager exit."""
        await self.close()
