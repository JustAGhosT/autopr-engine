from typing import Any, TypeVar

from .tool_base import Tool

TIssue = TypeVar("TIssue")
TConfig = TypeVar("TConfig")
TTool = TypeVar("TTool", bound=Tool)


class ToolRegistry:
    """Registry for quality tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self._tool_classes: dict[str, type[Tool]] = {}

    def register(self, tool_class: type[Tool]) -> type[Tool]:
        """
        Register a tool class with the registry.

        Args:
            tool_class: The tool class to register

        Returns:
            The registered tool class (for use as a decorator)
        """
        # Create an instance of the tool class
        tool = tool_class()

        self._tools[tool.name] = tool
        self._tool_classes[tool.name] = tool_class
        return tool_class

    def get_tool(self, name: str) -> Tool:
        """
        Get a tool by name.

        Args:
            name: The name of the tool

        Returns:
            The tool instance

        Raises:
            KeyError: If the tool is not registered
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered.")
        return self._tools[name]

    def get_tool_class(self, name: str) -> type[Tool]:
        """
        Get a tool class by name.

        Args:
            name: The name of the tool

        Returns:
            The tool class

        Raises:
            KeyError: If the tool is not registered
        """
        if name not in self._tool_classes:
            raise KeyError(f"Tool class '{name}' is not registered.")
        return self._tool_classes[name]

    def get_all_tools(self) -> list[Tool]:
        """
        Get all registered tools.

        Returns:
            List of all registered tool instances
        """
        return list(self._tools.values())

    def get_tool_classes(self) -> list[type[Tool]]:
        """
        Get all registered tool classes.

        Returns:
            List of all registered tool classes
        """
        return list(self._tool_classes.values())

    def get_tools_by_category(self, category: str) -> list[Tool]:
        """
        Get all tools in a specific category.

        Args:
            category: The category to filter by

        Returns:
            List of tools in the specified category
        """
        return [tool for tool in self._tools.values() if tool.category == category]

    def instantiate_tool(self, name: str, *args: Any, **kwargs: Any) -> Tool:
        """
        Instantiate a new instance of a tool class.

        Args:
            name: The name of the tool class
            *args: Positional arguments to pass to the constructor
            **kwargs: Keyword arguments to pass to the constructor

        Returns:
            A new instance of the tool

        Raises:
            KeyError: If the tool class is not registered
        """
        tool_class = self.get_tool_class(name)
        return tool_class(*args, **kwargs)


# Create a global registry instance
registry = ToolRegistry()


def register_tool(tool_class: type[TTool]) -> type[TTool]:
    """
    Decorator to register a tool with the registry.

    Args:
        tool_class: The tool class to register

    Returns:
        The registered tool class

    Example:
        @register_tool
        class MyTool(Tool[MyConfig, LintIssue]):
            pass
    """
    registry.register(tool_class)
    return tool_class
