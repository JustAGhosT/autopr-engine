from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, get_args

# Change the bound to Any to allow TypedDict
TConfig = TypeVar("TConfig", bound=Any)
TIssue = TypeVar("TIssue")


class Tool(ABC, Generic[TConfig, TIssue]):
    """Abstract base class for quality tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the tool."""

    @property
    @abstractmethod
    def description(self) -> str:
        """A brief description of what the tool does."""

    @property
    def category(self) -> str:
        """The category of the tool (e.g., 'linting', 'security', etc.)."""
        return "general"

    @property
    def result_type(self) -> type | None:
        """
        The type of results this tool produces.

        This is used for automatic result handler dispatch.
        By default, tries to infer from the generic type parameters.
        """
        try:
            # Try to extract the issue type from generic parameters
            args = get_args(self.__orig_bases__[0])
            if args and len(args) >= 2:
                return args[1]
        except (AttributeError, IndexError):
            pass

        return None

    @abstractmethod
    async def run(self, files: list[str], config: TConfig) -> dict[str, Any]:
        """
        Run the tool on a list of files.

        Args:
            files: The list of files to process.
            config: The configuration for the tool.

        Returns:
            A dictionary containing:
                - 'issues': List of issues found
                - 'files_with_issues': List of files that had issues
                - 'summary': A text summary of the results (optional)
        """
