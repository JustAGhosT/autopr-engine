"""
AutoPR Engine Actions.

Core automation actions for GitHub PR processing
"""

# mypy: disable-error-code=unused-ignore
# mypy: ignore-errors

from typing import Any

# Import action classes with error handling for optional dependencies
PlatformDetector: type[Any] | None = None
try:
    from .platform_detector_enhanced import PlatformDetector as _RealPlatformDetector

    PlatformDetector = _RealPlatformDetector
except ImportError:
    pass

PrototypeEnhancer: type[Any] | None = None
try:
    from .prototype_enhancer import PrototypeEnhancer as _RealPrototypeEnhancer

    PrototypeEnhancer = _RealPrototypeEnhancer
except ImportError:
    pass

PlatformDetector: type[Any] | None = None
try:
    from .platform_detector import PlatformDetector as _RealPlatformDetector

    PlatformDetector = _RealPlatformDetector
except ImportError:
    pass

AutoGenImplementation: type[Any] | None = None
try:
    from .autogen_implementation import (
        AutoGenImplementation as _RealAutoGenImplementation,
    )

    AutoGenImplementation = _RealAutoGenImplementation
except ImportError:
    pass

IssueCreator: type[Any] | None = None
try:
    from .issue_creator import IssueCreator as _RealIssueCreator

    IssueCreator = _RealIssueCreator
except ImportError:
    pass

LLMProviderManager: type[Any] | None = None
try:
    from .llm import LLMProviderManager as _RealLLMProviderManager

    LLMProviderManager = _RealLLMProviderManager
except ImportError:
    pass

AutoGenAgentSystem: type[Any] | None = None
try:
    from .autogen_multi_agent import AutoGenAgentSystem as _RealAutoGenAgentSystem

    AutoGenAgentSystem = _RealAutoGenAgentSystem
except ImportError:
    pass

Mem0MemoryManager: type[Any] | None = None
try:
    from .mem0_memory_integration import Mem0MemoryManager as _RealMem0MemoryManager

    Mem0MemoryManager = _RealMem0MemoryManager
except ImportError:
    pass

QualityGates: type[Any] | None = None
try:
    from .quality_gates import QualityGates as _RealQualityGates

    QualityGates = _RealQualityGates
except ImportError:
    pass

LearningMemorySystem: type[Any] | None = None
try:
    from .learning_memory_system import (
        LearningMemorySystem as _RealLearningMemorySystem,
    )

    LearningMemorySystem = _RealLearningMemorySystem
except ImportError:
    pass

MultiPlatformIntegrator: type[Any] | None = None
try:
    from .multi_platform_integrator import (
        MultiPlatformIntegrator as _RealMultiPlatformIntegrator,
    )

    MultiPlatformIntegrator = _RealMultiPlatformIntegrator
except ImportError:
    pass

AICommentAnalyzer: type[Any] | None = None
try:
    from .ai_comment_analyzer import AICommentAnalyzer as _RealAICommentAnalyzer

    AICommentAnalyzer = _RealAICommentAnalyzer
except ImportError:
    pass

PRCommentHandler: type[Any] | None = None
try:
    from .handle_pr_comment import PRCommentHandler as _RealPRCommentHandler

    PRCommentHandler = _RealPRCommentHandler
except ImportError:
    pass

# Utility actions
LabelPR: type[Any] | None = None
try:
    from .label_pr import LabelPR as _RealLabelPR

    LabelPR = _RealLabelPR
except ImportError:
    pass

PostComment: type[Any] | None = None
try:
    from .post_comment import PostComment as _RealPostComment

    PostComment = _RealPostComment
except ImportError:
    pass

CreateOrUpdateIssue: type[Any] | None = None
try:
    from .create_or_update_issue import CreateOrUpdateIssue as _RealCreateOrUpdateIssue

    CreateOrUpdateIssue = _RealCreateOrUpdateIssue
except ImportError:
    pass

ApplyGitPatch: type[Any] | None = None
try:
    from .apply_git_patch import ApplyGitPatch as _RealApplyGitPatch

    ApplyGitPatch = _RealApplyGitPatch
except ImportError:
    pass

RunSecurityAudit: type[Any] | None = None
try:
    from .run_security_audit import RunSecurityAudit as _RealRunSecurityAudit

    RunSecurityAudit = _RealRunSecurityAudit
except ImportError:
    pass

CheckPerformanceBudget: type[Any] | None = None
try:
    from .check_performance_budget import (
        CheckPerformanceBudget as _RealCheckPerformanceBudget,
    )

    CheckPerformanceBudget = _RealCheckPerformanceBudget
except ImportError:
    pass

VisualRegressionTest: type[Any] | None = None
try:
    from .visual_regression_test import (
        VisualRegressionTest as _RealVisualRegressionTest,
    )

    VisualRegressionTest = _RealVisualRegressionTest
except ImportError:
    pass

GenerateReleaseNotes: type[Any] | None = None
try:
    from .generate_release_notes import (
        GenerateReleaseNotes as _RealGenerateReleaseNotes,
    )

    GenerateReleaseNotes = _RealGenerateReleaseNotes
except ImportError:
    pass

AIImplementationRoadmap: type[Any] | None = None
try:
    from .ai_implementation_roadmap import AIImplementationRoadmap
except ImportError:
    AIImplementationRoadmap = None

# All available actions
__all__ = [
    "AICommentAnalyzer",
    "AIImplementationRoadmap",
    "ApplyGitPatch",
    "AutoGenAgentSystem",
    "AutoGenImplementation",
    "CheckPerformanceBudget",
    "CreateOrUpdateIssue",
    "GenerateReleaseNotes",
    "IssueCreator",
    "LLMProviderManager",
    # Utility actions
    "LabelPR",
    "LearningMemorySystem",
    "Mem0MemoryManager",
    "MultiPlatformIntegrator",
    "PRCommentHandler",
    # Core AI-powered actions
    "PlatformDetector",
    "PlatformDetector",
    "PostComment",
    "PrototypeEnhancer",
    "QualityGates",
    "RunSecurityAudit",
    "VisualRegressionTest",
]
