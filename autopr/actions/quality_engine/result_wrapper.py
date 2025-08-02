"""
Generic wrapper for tool results.
"""

from typing import Any, Generic, TypeVar

T = TypeVar("T")


class ToolResult(Generic[T]):
    """
    A wrapper for tool results that includes metadata about the tool that produced them.

    This wrapper allows for standardized handling of results from different tools,
    while maintaining type information about the specific result type.

    Attributes:
        tool_name: The name of the tool that produced the results
        category: The category of the tool (e.g., 'linting', 'security')
        issues: The list of issues found by the tool
        metadata: Additional metadata about the tool run
    """

    def __init__(
        self,
        tool_name: str,
        issues: list[T],
        category: str = "general",
        metadata: dict[str, Any] = None,
    ):
        """
        Initialize a new tool result.
        Args:
            tool_name: The name of the tool that produced the results
            issues: The list of issues found by the tool
            category: The category of the tool (default: 'general')
            metadata: Additional metadata about the tool run (default: None)
        """
        self.tool_name = tool_name
        self.issues = issues
        self.category = category
        self.metadata = metadata or {}

    @property
    def count(self) -> int:
        """
        Get the number of issues.
        Returns:
            The number of issues in this result
        """
        return len(self.issues)

    def has_issues(self) -> bool:
        """
        Check if any issues were found.
        Returns:
            True if there are issues, False otherwise
        """
        return self.count > 0

    def __repr__(self) -> str:
        """
        Get a string representation of the result.

        Returns:
            A string representation of the result
        """
        return f"ToolResult(tool_name='{self.tool_name}', count={self.count}, category='{self.category}')"
