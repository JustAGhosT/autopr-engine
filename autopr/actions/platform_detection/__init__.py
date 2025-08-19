"""
Platform Detection Package

Modular platform detection system for AutoPR.
"""

from .config import PlatformConfigManager
from .detector import PlatformDetector, PlatformDetectorInputs, PlatformDetectorOutputs
from .file_analyzer import FileAnalyzer
from .scoring import PlatformScoringEngine

__all__ = [
    "FileAnalyzer",
    "PlatformConfigManager",
    "PlatformDetector",
    "PlatformDetectorInputs",
    "PlatformDetectorOutputs",
    "PlatformScoringEngine",
]
