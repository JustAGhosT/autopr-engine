from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


class HandlerRegistry:
    def __init__(self) -> None:
        self._handlers: dict[type[Any], Callable[[list[Any]], None]] = {}

    def register(self, result_type: type[T]):
        """
        Register a handler function for a specific result type.

        Args:
            result_type: The type of result this handler handles.

        Returns:
            A decorator function that registers the handler.
        """

        def decorator(func: Callable[[list[T]], None]):
            self._handlers[result_type] = func
            return func

        return decorator

    def dispatch(self, results: list[Any], result_type: type[T]) -> None:
        """
        Dispatch results to the appropriate handler.

        Args:
            results: The results to process.
            result_type: The type of the results.

        Raises:
            ValueError: If no handler is registered for the result type.
        """
        handler = self._handlers.get(result_type)
        if not handler:
            raise ValueError(f"No handler registered for {result_type.__name__}.")
        handler(results)
