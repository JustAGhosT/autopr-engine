"""
AutoPR Agent Framework

This module provides agent-based orchestration for code quality analysis using CrewAI.

## Agents

### Base Classes
- `BaseAgent`: Base class for all AutoPR agents
- `VolumeConfig`: Configuration for volume-based quality control

### Concrete Agents
- `LintingAgent`: Identifies and fixes code style and quality issues

### Crew Orchestration
- `AutoPRCrew`: Main orchestrator for code analysis agents

Note: This is the updated agent framework. Legacy agent imports have been removed.
"""

import warnings

from autopr.agents.agents import BaseAgent, LintingAgent, VolumeConfig

# Import modular agent IO types
from autopr.agents.code_quality_agent import CodeQualityInputs, CodeQualityOutputs

# Import crew from the crew module
from autopr.agents.crew.main import AutoPRCrew
from autopr.agents.linting_agent import LintingInputs, LintingOutputs

# Import models
from autopr.agents.models import (
                                              CodeAnalysisReport,
                                              CodeIssue,
                                              IssueSeverity,
                                              PlatformAnalysis,
                                              PlatformComponent,
)
from autopr.agents.platform_analysis_agent import PlatformAnalysisInputs, PlatformAnalysisOutputs

# Show deprecation warning for old import path
warnings.warn(
    "The 'agents.agents' module is deprecated. Import directly from 'agents' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    # Crew
    "AutoPRCrew",
    # Base classes
    "BaseAgent",
    "CodeAnalysisReport",
    "CodeIssue",
    # Agents
    "CodeQualityInputs",
    "CodeQualityOutputs",
    # Models
    "IssueSeverity",
    "LintingAgent",
    "LintingInputs",
    "LintingOutputs",
    "PlatformAnalysis",
    "PlatformAnalysisInputs",
    "PlatformAnalysisOutputs",
    "PlatformComponent",
    "VolumeConfig",
]
