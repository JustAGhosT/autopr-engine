"""
Quality Engine package.

A modular system for running code quality tools and handling their results.
"""

# Version information
__version__ = "1.0.0"

# Import main classes for easy access from the package root
from .engine import QualityEngine, QualityInputs, QualityMode, QualityOutputs
from .handler_base import Handler
from .tools.tool_base import Tool

# Optional DI imports (avoid hard dependency on config parsers like toml/yaml at import time)
try:  # pragma: no cover - optional dependency wiring
    from .di import container, get_engine  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    container = None  # type: ignore[assignment]

    def get_engine() -> QualityEngine:  # type: ignore[misc]
        msg = "QualityEngine DI container is unavailable. Optional dependencies may be missing (e.g., toml/yaml)."
        raise RuntimeError(msg)


__all__ = [
    "Handler",
    "QualityEngine",
    "QualityInputs",
    "QualityMode",
    "QualityOutputs",
    "Tool",
    "container",
    "get_engine",
]
