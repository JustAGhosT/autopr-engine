from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TResult = TypeVar("TResult")


class Handler(Generic[TResult], ABC):
    """
    Abstract base class for handlers that process tool results.

    A handler defines how specific types of results from tools should be processed,
    displayed, or used to take further action.

    Attributes:
        result_type (Type[TResult]): The type of result this handler can process.
    """

    @abstractmethod
    def handle(self, results: list[TResult]) -> None:
        """
        Process a list of tool results.

        Args:
            results: The results to process.
        """
