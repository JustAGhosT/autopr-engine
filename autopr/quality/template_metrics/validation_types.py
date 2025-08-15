"""Local validation types for quality template metrics.

Provides minimal replacements for validation constructs used by quality scoring
to avoid depending on external template validator modules.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    category: str
    severity: ValidationSeverity
    message: str
    line: int | None = None
    metadata: dict[str, Any] | None = None
