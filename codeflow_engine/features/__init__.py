"""
AutoPR Features Module

This module contains POC implementations of advanced features for AutoPR Engine.

Features:
- Real-time collaboration dashboard (WebSocket)
- No-code workflow builder (visual editor)
- AI-powered learning system (ML feedback loop)

All features are implemented as comprehensive POCs with TODO comments
for production finalization.
"""

# Conditional imports to avoid dependency errors
try:
    from codeflow_engine.features.ai_learning_system import (
        AILearningSystem,
        CodeIssue,
        IssueSeverity,
        ReviewFeedback,
        ReviewFeedbackType,
        ReviewSession,
    )
except ImportError as e:
    import warnings
    warnings.warn(f"Could not import AI Learning System: {e}")
    AILearningSystem = None  # type: ignore
    CodeIssue = None  # type: ignore
    IssueSeverity = None  # type: ignore
    ReviewFeedback = None  # type: ignore
    ReviewFeedbackType = None  # type: ignore
    ReviewSession = None  # type: ignore

try:
    from codeflow_engine.features.realtime_dashboard import RealtimeDashboard
except ImportError as e:
    import warnings
    warnings.warn(f"Could not import Realtime Dashboard (requires flask-socketio): {e}")
    RealtimeDashboard = None  # type: ignore

try:
    from codeflow_engine.features.workflow_builder import (
        ActionType,
        NodeType,
        TriggerType,
        Workflow,
        WorkflowBuilder,
        WorkflowEdge,
        WorkflowNode,
    )
except ImportError as e:
    import warnings
    warnings.warn(f"Could not import Workflow Builder: {e}")
    WorkflowBuilder = None  # type: ignore
    Workflow = None  # type: ignore
    WorkflowNode = None  # type: ignore
    WorkflowEdge = None  # type: ignore
    NodeType = None  # type: ignore
    TriggerType = None  # type: ignore
    ActionType = None  # type: ignore

__all__ = [
    # Real-time Dashboard
    "RealtimeDashboard",
    # Workflow Builder
    "WorkflowBuilder",
    "Workflow",
    "WorkflowNode",
    "WorkflowEdge",
    "NodeType",
    "TriggerType",
    "ActionType",
    # AI Learning System
    "AILearningSystem",
    "ReviewSession",
    "CodeIssue",
    "ReviewFeedback",
    "ReviewFeedbackType",
    "IssueSeverity",
]
