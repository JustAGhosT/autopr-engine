"""
Prototype Enhancement Package

Modular prototype enhancement system that provides platform-specific enhancements
for production readiness, testing, and security.

This package replaces the monolithic PrototypeEnhancer class with a modular architecture
while maintaining backward compatibility.
"""

from .enhancement_strategies import (
    BoltEnhancementStrategy,
    EnhancementStrategy,
    EnhancementStrategyFactory,
    LovableEnhancementStrategy,
    ReplitEnhancementStrategy,
)
from .enhancer import PrototypeEnhancer
from .file_generators import FileGenerator
from .platform_configs import PlatformConfig, PlatformRegistry

__version__ = "2.0.0"
__author__ = "AutoPR Team"

# Main exports for backward compatibility
__all__ = [
    "BoltEnhancementStrategy",
    "EnhancementStrategy",
    "EnhancementStrategyFactory",
    "FileGenerator",
    "LovableEnhancementStrategy",
    "PlatformConfig",
    "PlatformRegistry",
    "PrototypeEnhancer",
    "ReplitEnhancementStrategy",
]

# Package metadata
SUPPORTED_PLATFORMS = ["replit", "lovable", "bolt", "same", "emergent"]
ENHANCEMENT_TYPES = ["production_ready", "testing", "security"]


def get_version() -> str:
    """Get the package version."""
    return __version__


def get_supported_platforms() -> list:
    """Get list of supported platforms."""
    return SUPPORTED_PLATFORMS.copy()


def get_enhancement_types() -> list:
    """Get list of supported enhancement types."""
    return ENHANCEMENT_TYPES.copy()
