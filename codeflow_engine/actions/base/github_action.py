"""
GitHub-specific action class for AutoPR.
"""

from typing import Any

from codeflow_engine.actions.base.action import Action


class GitHubAction(Action):
    """
    Base class for GitHub-specific actions.

    Provides common functionality for actions that interact with GitHub API.
    """

    def __init__(self, name: str, description: str = "", version: str = "1.0.0"):
        super().__init__(name, description, version)
        self.supported_platforms = ["github"]
        self.required_permissions.extend(["repo", "pull_requests"])

    def get_github_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Extract GitHub-specific context information.

        Args:
            context: Full execution context

        Returns:
            GitHub context dictionary
        """
        return {
            "repository": context.get("repository"),
            "pull_request": context.get("pull_request"),
            "issue": context.get("issue"),
            "sender": context.get("sender"),
            "installation": context.get("installation"),
            "github_token": context.get("github_token"),
        }
