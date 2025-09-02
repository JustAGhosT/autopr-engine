"""
Split Models for AI Linting Fixer

Data models for file splitting operations.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


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
