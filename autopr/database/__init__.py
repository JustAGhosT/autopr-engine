"""
Database Module

This module provides database connection management, session handling,
and model imports for the AutoPR Engine.

Usage:
    from autopr.database import get_db, Base, Workflow

    # Get database session
    db = next(get_db())

    # Query models
    workflows = db.query(Workflow).filter(Workflow.status == 'active').all()
"""

from autopr.database.config import Base, SessionLocal, engine, get_db
from autopr.database.models import (
    ExecutionLog,
    Integration,
    IntegrationEvent,
    Workflow,
    WorkflowAction,
    WorkflowExecution,
    WorkflowTrigger,
)

__all__ = [
    # Configuration
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    # Models
    "Workflow",
    "WorkflowExecution",
    "WorkflowAction",
    "ExecutionLog",
    "Integration",
    "IntegrationEvent",
    "WorkflowTrigger",
]
