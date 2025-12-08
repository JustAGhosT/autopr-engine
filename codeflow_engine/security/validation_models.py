from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ValidationResult(BaseModel):
    """Result of input validation."""

    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    sanitized_data: dict[str, Any] | None = None
    severity: ValidationSeverity = ValidationSeverity.LOW
