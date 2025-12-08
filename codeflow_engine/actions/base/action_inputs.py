"""
ActionInputs base class for AutoPR.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ActionInputs:
    """
    Base class for action inputs.

    Actions should define their own input classes that inherit from this.
    """

    def to_dict(self) -> dict[str, Any]:
        """Convert inputs to dictionary."""
        return self.__dict__

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionInputs":
        """Create inputs from dictionary."""
        return cls(**data)
