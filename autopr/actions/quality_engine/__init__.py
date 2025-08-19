"""
Quality Engine package.

A modular system for running code quality tools and handling their results.
"""

# Version information
__version__ = "1.0.0"

# Import main classes for easy access from the package root
from autopr.actions.quality_engine.engine import (QualityEngine, QualityInputs,
                                                  QualityMode, QualityOutputs)
from autopr.actions.quality_engine.handler_base import Handler
from autopr.actions.quality_engine.tools.tool_base import Tool

# Optional DI imports (avoid hard dependency on config parsers like toml/yaml at import time)
try:  # pragma: no cover - optional dependency wiring
    from autopr.actions.quality_engine.di import (  # type: ignore[import-not-found]
        container, get_engine)
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
