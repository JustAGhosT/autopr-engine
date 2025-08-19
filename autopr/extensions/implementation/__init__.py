"""
Implementation Roadmap Package

Modular implementation system for AutoPR extension roadmap.
"""

from implementation.implementor import Phase1ExtensionImplementor
from implementation.phase_manager import PhaseExecution, PhaseManager
from implementation.report_generator import ReportGenerator
from implementation.task_definitions import Task, TaskRegistry
from implementation.task_executor import TaskExecution, TaskExecutor

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
