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
"""

import warnings
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Generic, Type

# Import base classes and models
from autopr.agents.base import BaseAgent
from autopr.agents.models import (
    IssueSeverity,
    CodeIssue,
    PlatformComponent,
    PlatformAnalysis,
    CodeAnalysisReport
)

# Import the new modular agent classes
from .code_quality_agent import (
    CodeQualityAgent,
    CodeQualityInputs,
    CodeQualityOutputs
)

from .platform_analysis_agent import (
    PlatformAnalysisAgent,
    PlatformAnalysisInputs,
    PlatformAnalysisOutputs
)

from .linting_agent import (
    LintingAgent,
    LintingInputs,
    LintingOutputs
)

from autopr.agents.agents import (
    CodeReviewAgent,
    DocumentationAgent,
    TestingAgent,
    SecurityAgent,
    PerformanceAgent,
    AccessibilityAgent,
    PlatformDetectionAgent,
    PlatformEnhancementAgent,
    VolumeConfig,
    AutoPRCrew,
    ModularAutoPRCrew,
)
from autopr.utils.volume_utils import (
    volume_to_quality_mode,
    get_volume_config,
    get_volume_level_name,
)

# Show deprecation warning for old import path
warnings.warn(
    "The 'agents.agents' module is deprecated. Import directly from 'agents' instead.",
    DeprecationWarning,
    stacklevel=2
)

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
    
    # Crew
    'AutoPRCrew',
    'ModularAutoPRCrew'  # New modular implementation
]
