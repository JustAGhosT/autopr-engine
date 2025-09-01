"""
Implementation Roadmap Package

Modular implementation system for AutoPR extension roadmap.
"""

from .implementor import Phase1ExtensionImplementor
from .phase_manager import PhaseExecution, PhaseManager
from .report_generator import ReportGenerator
from .task_definitions import Task, TaskRegistry
from .task_executor import TaskExecution, TaskExecutor

__all__ = [
    "Phase1ExtensionImplementor",
    "PhaseExecution",
    "PhaseManager",
    "ReportGenerator",
    "Task",
    "TaskExecution",
    "TaskExecutor",
    "TaskRegistry",
]

__version__ = "1.0.0"
