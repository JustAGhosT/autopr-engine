"""
Platform Detection Module

Detects and analyzes rapid prototyping platforms.
"""

from .detector import PlatformDetector
from .models import PlatformDetectorInputs, PlatformDetectorOutputs
from .patterns import PlatformPatterns
from .utils import calculate_confidence_score, get_confidence_level

__all__ = [
    "PlatformDetector",
    "PlatformDetectorInputs", 
    "PlatformDetectorOutputs",
    "PlatformPatterns",
    "calculate_confidence_score",
    "get_confidence_level"
]
