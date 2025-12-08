"""
ActionOutputs base class for AutoPR.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ActionOutputs:
    """
    Base class for action outputs.

    Actions should define their own output classes that inherit from this.
    """

    success: bool = True
    message: str = ""
    data: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.data is None:
            self.data = {}

    def to_dict(self) -> dict[str, Any]:
        """Convert outputs to dictionary."""
        return {"success": self.success, "message": self.message, "data": self.data}
