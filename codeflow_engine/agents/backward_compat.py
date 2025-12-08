"""
Backward compatibility layer for the agents module.

This module provides backward compatibility for code that imports agents from the old
monolithic agents.py file. It re-exports the new modular agent classes from their
new locations.
"""

import warnings


# Show deprecation warning
warnings.warn(
    "The 'agents.agents' module is deprecated. Import directly from 'agents' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export models from the models module
# Re-export the new agent classes from their new locations
from codeflow_engine.agents.base import BaseAgent, VolumeConfig
from codeflow_engine.agents.code_quality_agent import (
    CodeQualityAgent,
    CodeQualityInputs,
    CodeQualityOutputs,
)
from codeflow_engine.agents.linting_agent import LintingAgent, LintingInputs, LintingOutputs
from codeflow_engine.agents.models import (
    CodeAnalysisReport,
    CodeIssue,
    IssueSeverity,
    PlatformAnalysis,
    PlatformComponent,
)
from codeflow_engine.agents.platform_analysis_agent import (
    PlatformAnalysisAgent,
    PlatformAnalysisInputs,
    PlatformAnalysisOutputs,
)


# For backward compatibility with existing code
__all__ = [
    # Base classes
    "BaseAgent",
    "CodeAnalysisReport",
    "CodeIssue",
    # Agents
    "CodeQualityAgent",
    "CodeQualityInputs",
    "CodeQualityOutputs",
    # Models
    "IssueSeverity",
    "LintingAgent",
    "LintingInputs",
    "LintingOutputs",
    "PlatformAnalysis",
    "PlatformAnalysisAgent",
    "PlatformAnalysisInputs",
    "PlatformAnalysisOutputs",
    "PlatformComponent",
    "VolumeConfig",
]
