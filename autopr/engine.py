"""
AutoPR Engine - Core Engine Implementation

Main engine class that orchestrates AutoPR operations.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from autopr.actions.registry import ActionRegistry
# from autopr.agents.agents import AgentManager  # Not implemented yet
from autopr.ai.core.providers.manager import LLMProviderManager
from autopr.config import AutoPRConfig
from autopr.exceptions import AutoPRException, ConfigurationError
from autopr.integrations.registry import IntegrationRegistry
from autopr.quality.metrics_collector import MetricsCollector
from autopr.workflows.engine import WorkflowEngine
# from autopr.workflows.workflow_manager import WorkflowManager  # Not implemented yet

logger = logging.getLogger(__name__)


def handle_operation_error(
    operation_name: str,
    exception: Exception,
    error_class: type[AutoPRException] = AutoPRException,
    *,
    reraise: bool = True,
) -> None:
    """
    Standardized error handling helper for engine operations.
    
    Args:
        operation_name: Name of the operation that failed
        exception: The exception that was raised
        error_class: Exception class to raise (default: AutoPRException)
        log_level: Logging level to use ('exception', 'error', 'warning')
        reraise: Whether to reraise the exception after logging
        
    Raises:
        error_class: The specified exception class with formatted message
    """
    error_msg = f"{operation_name} failed: {exception}"
    logger.exception(error_msg)
    
    if reraise:
        raise error_class(error_msg) from exception


class AutoPREngine:
    """
    Main AutoPR Engine class that coordinates all automation activities.

    This class serves as the central orchestrator for:
    - Workflow execution
    - Action processing
    - Integration management
    - AI/LLM provider coordination
    """

    def __init__(self, config: AutoPRConfig | None = None):
        """
        Initialize the AutoPR Engine.

        Args:
            config: Configuration object. If None, loads default config.
        """
        self.config = config or AutoPRConfig()
        self.workflow_engine = WorkflowEngine(self.config)
        self.action_registry: ActionRegistry = ActionRegistry()
        self.integration_registry = IntegrationRegistry()
        self.llm_manager = LLMProviderManager(self.config)

        logger.info("AutoPR Engine initialized successfully")

    async def __aenter__(self) -> "AutoPREngine":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.stop()

    async def start(self) -> None:
        """Start the AutoPR Engine and initialize all components."""
        try:
            # Validate configuration before starting
            if not self.config.validate():
                msg = "Invalid configuration: Missing required authentication or LLM provider keys"
                logger.error(msg)
                raise ConfigurationError(msg)
            
            await self.workflow_engine.start()
            await self.integration_registry.initialize()
            await self.llm_manager.initialize()
            logger.info("AutoPR Engine started successfully")
        except ConfigurationError:
            raise
        except Exception as e:
            handle_operation_error("Engine startup", e, AutoPRException)

    async def stop(self) -> None:
        """Stop the AutoPR Engine and cleanup resources."""
        try:
            await self.workflow_engine.stop()
            await self.integration_registry.cleanup()
            await self.llm_manager.cleanup()
            logger.info("AutoPR Engine stopped successfully")
        except Exception as e:
            handle_operation_error("Engine shutdown", e, AutoPRException)

    async def process_event(
        self, event_type: str, event_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Process an incoming event through the workflow engine.

        Args:
            event_type: Type of event (e.g., 'pull_request', 'issue', 'push')
            event_data: Event payload data

        Returns:
            Processing result dictionary
        """
        try:
            result = await self.workflow_engine.process_event(event_type, event_data)
            logger.info(f"Successfully processed {event_type} event")
            return result
        except Exception as e:
            handle_operation_error("Event processing", e, AutoPRException)

    def get_status(self) -> dict[str, Any]:
        """
        Get the current status of the AutoPR Engine.

        Returns:
            Status dictionary with component information
        """
        return {
            "engine": "running",
            "workflow_engine": self.workflow_engine.get_status(),
            "actions": len(self.action_registry.get_all_actions()),
            "integrations": len(self.integration_registry.get_all_integrations()),
            "llm_providers": len(self.llm_manager.get_available_providers()),
            "config": self.config.to_dict(),
        }

