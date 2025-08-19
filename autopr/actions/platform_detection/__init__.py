"""
Platform Detection Package

Modular platform detection system for AutoPR.
"""

from autopr.actions.platform_detection.config import PlatformConfigManager
from autopr.actions.platform_detection.detector import (
    PlatformDetector,
    PlatformDetectorInputs,
    PlatformDetectorOutputs,
)
from autopr.actions.platform_detection.file_analyzer import FileAnalyzer
from autopr.actions.platform_detection.scoring import PlatformScoringEngine


__all__ = [
    "FileAnalyzer",
    "PlatformConfigManager",
    "PlatformDetector",
    "PlatformDetectorInputs",
    "PlatformDetectorOutputs",
    "PlatformScoringEngine",
]
