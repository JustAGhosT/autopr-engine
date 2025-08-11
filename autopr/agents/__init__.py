"""
AutoPR Agent Framework

This module provides agent-based orchestration for code quality analysis using CrewAI.

## Agents

### Base Classes
- `BaseAgent`: Base class for all AutoPR agents
- `VolumeConfig`: Configuration for volume-based quality control

### Concrete Agents
- `CodeQualityAgent`: Analyzes and improves code quality
- `PlatformAnalysisAgent`: Detects platforms and technologies in a codebase
- `LintingAgent`: Identifies and fixes code style and quality issues

### Crew Orchestration
- `AutoPRCrew`: Main orchestrator for code analysis agents

Note: This is the updated agent framework. Legacy agent imports have been removed.
"""

import warnings

from autopr.agents.agents import (
    BaseAgent,
    CodeQualityAgent,
    LintingAgent,
    PlatformAnalysisAgent,
    VolumeConfig,
)

# Import models
from autopr.agents.models import (
    CodeAnalysisReport,
    CodeIssue,
    IssueSeverity,
    PlatformAnalysis,
    PlatformComponent,
)

# Import modular agent IO types
from .code_quality_agent import CodeQualityInputs, CodeQualityOutputs

# Import crew from the crew module
from .crew.main import AutoPRCrew
from .linting_agent import LintingInputs, LintingOutputs
from .platform_analysis_agent import PlatformAnalysisInputs, PlatformAnalysisOutputs

# Show deprecation warning for old import path
warnings.warn(
    "The 'agents.agents' module is deprecated. Import directly from 'agents' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    # Base classes
    "BaseAgent",
    "VolumeConfig",
    # Models
    "IssueSeverity",
    "CodeIssue",
    "PlatformComponent",
    "PlatformAnalysis",
    "CodeAnalysisReport",
    # Agents
    "CodeQualityAgent",
    "CodeQualityInputs",
    "CodeQualityOutputs",
    "PlatformAnalysisAgent",
    "PlatformAnalysisInputs",
    "PlatformAnalysisOutputs",
    "LintingAgent",
    "LintingInputs",
    "LintingOutputs",
    # Crew
    "AutoPRCrew",
]
