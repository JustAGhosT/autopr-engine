"""
Backward compatibility layer for the agents module.

This module provides backward compatibility for code that imports agents from the old
monolithic agents.py file. It re-exports the new modular agent classes from their
new locations.
"""
import warnings
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Generic, Type

# Show deprecation warning
warnings.warn(
    "The 'agents.agents' module is deprecated. Import directly from 'agents' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export models from the models module
from ..models import (
    IssueSeverity,
    CodeIssue,
    PlatformComponent,
    PlatformAnalysis,
    CodeAnalysisReport
)

# Re-export the new agent classes from their new locations
from .base import BaseAgent, VolumeConfig
from .code_quality_agent import CodeQualityAgent, CodeQualityInputs, CodeQualityOutputs
from .platform_analysis_agent import PlatformAnalysisAgent, PlatformAnalysisInputs, PlatformAnalysisOutputs
from .linting_agent import LintingAgent, LintingInputs, LintingOutputs

# For backward compatibility with existing code
__all__ = [
    # Base classes
    'BaseAgent',
    'VolumeConfig',
    
    # Models
    'IssueSeverity',
    'CodeIssue',
    'PlatformComponent',
    'PlatformAnalysis',
    'CodeAnalysisReport',
    
    # Agents
    'CodeQualityAgent',
    'CodeQualityInputs',
    'CodeQualityOutputs',
    'PlatformAnalysisAgent',
    'PlatformAnalysisInputs',
    'PlatformAnalysisOutputs',
    'LintingAgent',
    'LintingInputs',
    'LintingOutputs',
]
