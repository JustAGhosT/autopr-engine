"""
Split Models for AI Linting Fixer

Data models for file splitting operations.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SplitComponent:
    """Represents a component that can be split from a file."""

    name: str
    component_type: str  # 'function', 'class', 'section', 'module'
    start_line: int
    end_line: int
    content: str
    complexity_score: float
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate runtime invariants and perform lightweight normalization."""
        # Validate and normalize name
        if not isinstance(self.name, str):
            msg = f"name must be a string, got {type(self.name).__name__}"
            raise TypeError(msg)
        self.name = self.name.strip()
        if not self.name:
            msg = "name cannot be empty after stripping whitespace"
            raise ValueError(msg)

        # Validate start_line and end_line
        if not isinstance(self.start_line, int):
            msg = f"start_line must be an integer, got {type(self.start_line).__name__}"
            raise TypeError(msg)
        if not isinstance(self.end_line, int):
            msg = f"end_line must be an integer, got {type(self.end_line).__name__}"
            raise TypeError(msg)
        if self.start_line < 1:
            msg = f"start_line must be >= 1, got {self.start_line}"
            raise ValueError(msg)
        if self.end_line < self.start_line:
            msg = (f"end_line ({self.end_line}) must be >= start_line "
                   f"({self.start_line})")
            raise ValueError(msg)

        # Validate complexity_score
        if not isinstance(self.complexity_score, int | float):
            msg = (f"complexity_score must be numeric, got "
                   f"{type(self.complexity_score).__name__}")
            raise TypeError(msg)
        if self.complexity_score < 0:
            msg = f"complexity_score must be >= 0, got {self.complexity_score}"
            raise ValueError(msg)

        # Validate dependencies
        if not isinstance(self.dependencies, list):
            msg = f"dependencies must be a list, got {type(self.dependencies).__name__}"
            raise TypeError(msg)

        # Validate metadata
        if not isinstance(self.metadata, dict):
            msg = f"metadata must be a dict, got {type(self.metadata).__name__}"
            raise TypeError(msg)


@dataclass
class SplitConfig:
    """Configuration for file splitting operations."""

    max_lines: int = 100
    max_functions: int = 10
    max_classes: int = 5
    max_complexity: float = 10.0
    enable_ai_analysis: bool = True
    enable_caching: bool = True
    enable_parallel_processing: bool = True
    enable_memory_optimization: bool = True
    cache_ttl: int = 3600  # 1 hour
    max_parallel_workers: int = 4
    memory_limit_mb: int = 512
    performance_monitoring: bool = True
    line_overlap: int = 50  # Lines of overlap between chunks for parallel processing


@dataclass
class SplitResult:
    """Result of a file splitting operation."""

    success: bool
    components: list[SplitComponent]
    processing_time: float
    cache_hits: int = 0
    cache_misses: int = 0
    memory_usage_mb: float = 0.0
    performance_metrics: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
