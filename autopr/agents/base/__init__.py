"""
Base classes for AutoPR agents.

This module contains the base classes and utilities for all AutoPR agents.
"""

from .agent import BaseAgent
from .volume_config import VolumeConfig

__all__ = [
    "BaseAgent",
    "VolumeConfig",
]
