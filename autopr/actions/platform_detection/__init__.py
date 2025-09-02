"""
Platform Detection Module

Detects and analyzes rapid prototyping platforms.
"""

from .config import PlatformConfigManager
from .detector import PlatformDetector
from .file_analyzer import FileAnalyzer
from .models import PlatformDetectorInputs, PlatformDetectorOutputs
from .patterns import PlatformPatterns
from .scoring import PlatformScoringEngine
from .utils import calculate_confidence_score, get_confidence_level

__all__ = [
    "PlatformDetector",
    "FileAnalyzer",
    "PlatformConfigManager", 
    "PlatformScoringEngine",
    "PlatformDetectorInputs", 
    "PlatformDetectorOutputs",
    "PlatformPatterns",
    "calculate_confidence_score",
    "get_confidence_level"
]
