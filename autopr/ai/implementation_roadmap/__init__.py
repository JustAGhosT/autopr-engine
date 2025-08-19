"""
AutoPR Phase 1 Extensions Implementation Roadmap - Modular Architecture
Automated setup script for production-grade enhancements with clean separation of concerns
Implementation Roadmap Modular Package
"""

from .implementor import (
    Phase1ExtensionImplementor,
    get_phase1_implementor,
    reset_global_implementor,
)
from .phase_manager import PhaseExecution, PhaseManager
from .report_generator import ReportGenerator
from .task_definitions import ImplementationPhases, Phase, Task, TaskRegistry
from .task_executor import TaskExecution, TaskExecutor

__all__ = [
    "ImplementationPhases",
    # Phase system
    "Phase",
    # Main orchestrator
    "Phase1ExtensionImplementor",
    "PhaseExecution",
    "PhaseManager",
    # Reporting
    "ReportGenerator",
    # Task system
    "Task",
    "TaskExecution",
    "TaskExecutor",
    "TaskRegistry",
    "get_phase1_implementor",
    "reset_global_implementor",
]

# Package metadata
__version__ = "1.0.0"
__author__ = "AutoPR Team"
__description__ = "Modular implementation roadmap system for AutoPR Phase 1 extensions"


# Convenience functions for common operations
def create_implementor() -> Phase1ExtensionImplementor:
    """Create a new Phase1ExtensionImplementor instance"""
    return Phase1ExtensionImplementor()


def get_default_task_registry() -> TaskRegistry:
    """Get the default task registry with all predefined tasks"""
    return TaskRegistry()


def get_implementation_phases() -> ImplementationPhases:
    """Get the default implementation phases configuration"""
    return ImplementationPhases()
