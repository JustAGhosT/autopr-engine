"""
Artifacts Module

This module contains data models for various artifacts used in the AutoPR system.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class EnhancementType(StrEnum):
    """Types of enhancements that can be applied to a prototype."""

    PRODUCTION = "production"
    TESTING = "testing"
    SECURITY = "security"


@dataclass
class PrototypeEnhancerInputs:
    """Input model for the PrototypeEnhancer."""

    platform: str
    enhancement_type: "EnhancementType"
    project_path: str
    config: dict[str, Any] | None = None
    dry_run: bool = False


@dataclass
class PrototypeEnhancerOutputs:
    """Output model for the PrototypeEnhancer."""

    success: bool
    message: str
    generated_files: list[str]
    modified_files: list[str]
    next_steps: list[str]
    metadata: dict[str, Any] | None = None
