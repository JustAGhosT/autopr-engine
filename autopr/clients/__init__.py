"""Client implementations for various services used by AutoPR.

This package provides client implementations for external services like GitHub, Linear, etc.
These clients are used throughout the AutoPR codebase to interact with external APIs.
"""

from autopr.clients.github_client import GitHubClient
from autopr.clients.linear_client import LinearClient


__all__ = ["GitHubClient", "LinearClient"]
