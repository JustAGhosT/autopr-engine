"""
Registry for handlers that process tool results.
"""

from collections.abc import Callable
from typing import TypeVar

from .handler_base import Handler

TResult = TypeVar("TResult")
THandler = TypeVar("THandler", bound=Handler)


class HandlerRegistry:
    """
    Registry for result handlers.

    This registry maps result types to appropriate handlers, enabling
    the correct handling of different result types returned by tools.
    """

    def __init__(self, handler_map: dict[type, Handler] | None = None):
        """
        Initialize the registry with an optional handler map.

        Args:
            handler_map: A dictionary mapping result types to handlers.
        """
        # Maps from result types to handlers
        self._handlers = handler_map or {}

        # Maps from tool class types to handlers
        self._tool_handlers = {}

    def register_for_result(
        self, result_type: type[TResult]
    ) -> Callable[[type[Handler[TResult]]], type[Handler[TResult]]]:
        """
        Register a handler for a specific result type.

        Usage:
            @registry.register_for_result(LintIssue)
            class MyLintHandler(Handler[LintIssue]):
                ...

        Args:
            result_type: The type of result this handler processes

        Returns:
            A decorator function that registers the handler
        """

        def decorator(handler_class: type[Handler[TResult]]) -> type[Handler[TResult]]:
            handler = handler_class()
            self._handlers[result_type] = handler
            return handler_class

        return decorator

    def register_handler(self, result_type: type[TResult], handler: Handler[TResult]) -> None:
        """
        Register an existing handler instance for a result type.

        Args:
            result_type: The type of result this handler processes
            handler: The handler instance
        """
        self._handlers[result_type] = handler

    def register_for_tool(self, tool_class: type) -> Callable[[type[Handler]], type[Handler]]:
        """
        Register a handler for a specific tool class.

        Usage:
            @registry.register_for_tool(MyPyTool)
            class MyPyHandler(Handler[LintIssue]):
                ...

        Args:
            tool_class: The tool class this handler is for

        Returns:
            A decorator function that registers the handler
        """

        def decorator(handler_class: type[Handler]) -> type[Handler]:
            handler = handler_class()
            self._tool_handlers[tool_class] = handler
            return handler_class

        return decorator

    def get_handler_for_result(self, result_type: type[TResult]) -> Handler[TResult]:
        """
        Get the handler for a specific result type.

        Args:
            result_type: The type of result to get a handler for

        Returns:
            The appropriate handler for the result type

        Raises:
            KeyError: If no handler is registered for the result type
        """
        if result_type not in self._handlers:
            raise KeyError(f"No handler registered for result type {result_type.__name__}")
        return self._handlers[result_type]

    def get_handler_for_tool(self, tool_class: type) -> Handler:
        """
        Get the handler for a specific tool class.

        Args:
            tool_class: The tool class to get a handler for

        Returns:
            The appropriate handler for the tool class

        Raises:
            KeyError: If no handler is registered for the tool class
        """
        if tool_class not in self._tool_handlers:
            raise KeyError(f"No handler registered for tool class {tool_class.__name__}")
        return self._tool_handlers[tool_class]

    def handle_results(self, results: list[TResult], result_type: type[TResult]) -> None:
        """
        Handle results of a specific type.

        Args:
            results: The results to handle
            result_type: The type of the results

        Raises:
            KeyError: If no handler is registered for the result type
        """
        handler = self.get_handler_for_result(result_type)
        handler.handle(results)


# Decorators to register handlers without directly using the registry instance
# These will be replaced by using the DI container in the real application


def register_for_result(
    result_type: type[TResult],
) -> Callable[[type[Handler[TResult]]], type[Handler[TResult]]]:
    """Placeholder for the DI-based decorator."""
    from .di import container

    registry = container.handler_registry.registry()
    return registry.register_for_result(result_type)


def register_for_tool(tool_class: type) -> Callable[[type[Handler]], type[Handler]]:
    """Placeholder for the DI-based decorator."""
    from .di import container

    registry = container.handler_registry.registry()
    return registry.register_for_tool(tool_class)
