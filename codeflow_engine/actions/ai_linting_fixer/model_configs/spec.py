"""
Shared Model Specification

Common dataclass definitions for AI model configurations used across
the AI linting fixer system.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass
class ModelSpec:
    """Model specification with availability and performance characteristics."""

    name: str
    provider: str
    release_date: str
    vram_required: str
    performance_tier: str
    availability: bool
    endpoint_available: bool = False
    competency_ratings: Mapping[str, float] | None = None
    recommended_use_cases: list[Any] | None = None
