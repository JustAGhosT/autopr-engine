"""
Base agent class for AutoPR agents.

This module provides the BaseAgent class which serves as the foundation for all
AutoPR agents. It handles common functionality like initialization, logging, and
volume-based configuration.
"""

import logging
from typing import Any, TypeVar

# Optional dependency: provide a lightweight fallback when crewai is unavailable
try:  # pragma: no cover - runtime optional import
    from crewai import Agent as CrewAgent  # type: ignore[import-not-found,import-untyped]
except Exception:  # pragma: no cover

    class CrewAgent:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs) -> None:
            # Minimal stub to satisfy tests without crewai installed
            for key, value in kwargs.items():
                setattr(self, key, value)


from autopr.actions.llm import get_llm_provider_manager
from autopr.agents.base.volume_config import VolumeConfig

# Set up logger
logger = logging.getLogger(__name__)


# Define generic type variables for input/output types
InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class BaseAgent[InputT, OutputT]:
    """Base class for all AutoPR agents.

    This class provides common functionality for all agents, including:
    - Initialization with LLM provider and volume configuration
    - Logging and error handling
    - Template method pattern for agent execution

    Subclasses should implement the `_execute` method with agent-specific logic.

    Attributes:
        name: The name of the agent
        role: The role description of the agent
        backstory: Background information about the agent
        volume_config: Configuration based on volume level (0-1000)
        llm_provider: The LLM provider to use for this agent
        verbose: Whether to enable verbose logging
        allow_delegation: Whether to allow task delegation
        max_iter: Maximum number of iterations for the agent
        max_rpm: Maximum requests per minute for the agent
        default_volume: Default volume level (0-1000)
    """

    def __init__(
        self,
        name: str,
        role: str,
        backstory: str,
        volume: int = 500,  # Default to moderate level (500/1000)
        verbose: bool = False,
        allow_delegation: bool = False,
        max_iter: int = 5,
        max_rpm: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the base agent.

        Args:
            name: The name of the agent
            role: The role description of the agent
            backstory: Background information about the agent
            volume: Volume level (0-1000) for quality control
            verbose: Whether to enable verbose logging
            allow_delegation: Whether to allow task delegation
            max_iter: Maximum number of iterations for the agent
            max_rpm: Maximum requests per minute for the agent
            **kwargs: Additional keyword arguments passed to the base class
        """
        self.name = name
        self.role = role
        self.backstory = backstory
        self.verbose = verbose
        self.allow_delegation = allow_delegation
        self.max_iter = max_iter
        self.max_rpm = max_rpm

        # Initialize volume-based configuration
        self.volume_config = VolumeConfig(volume=volume)

        # Augment backstory with volume context for visibility in tests
        try:
            from autopr.utils.volume_utils import get_volume_level_name

            level_name = get_volume_level_name(self.volume_config.volume)
            self.backstory = f"{self.backstory}\nYou are currently operating at volume level {self.volume_config.volume} ({level_name})."
        except Exception:
            pass

        # Get the LLM provider manager
        self.llm_provider = get_llm_provider_manager()

        # Initialize the base CrewAI agent
        self._initialize_agent(**kwargs)

    def _initialize_agent(self, **kwargs: Any) -> None:
        """Initialize the underlying CrewAI agent.

        This method creates a CrewAI agent with the specified configuration.
        Subclasses can override this method to customize agent initialization.

        Args:
            **kwargs: Additional keyword arguments passed to the CrewAI agent
        """
        # CrewAI Agent requires a 'goal' field. Default it to the role when not provided.
        goal_value: str = kwargs.pop("goal", self.role)

        self.agent = CrewAgent(
            name=self.name,
            role=self.role,
            goal=goal_value,
            backstory=self.backstory,
            verbose=self.verbose,
            allow_delegation=self.allow_delegation,
            max_iter=self.max_iter,
            max_rpm=self.max_rpm,
            **kwargs,
        )

    async def execute(self, inputs: InputT) -> OutputT:
        """Execute the agent with the given inputs.

        This is the main entry point for agent execution. It handles common
        setup and teardown tasks and delegates to the `_execute` method for
        agent-specific logic.

        Args:
            inputs: The input data for the agent

        Returns:
            The output of the agent execution

        Raises:
            Exception: If an error occurs during execution
        """
        try:
            # Log the start of execution
            logger.debug("Starting execution of %s with inputs: %s", self.name, inputs)

            # Delegate to the agent-specific implementation
            result = await self._execute(inputs)

            # Log the completion of execution
            logger.debug("Completed execution of %s", self.name)

            return result

        except Exception as e:
            # Log the error with full context
            logger.error("Error in %s: %s", self.name, str(e), exc_info=True)

            # Preserve the original exception type and attributes
            if not str(e):
                # If the original exception has no message, use our custom one
                e.args = (f"Error in {self.name}", *e.args[1:])
            elif not any(
                self.name in str(arg) for arg in e.args if isinstance(arg, str)
            ):
                # If the error message doesn't already contain the agent name, prepend it
                e.args = (f"Error in {self.name}: {e!s}", *e.args[1:])

            # Re-raise the original exception with preserved type and attributes
            raise

    async def _execute(self, inputs: InputT) -> OutputT:
        """Execute the agent with the given inputs.

        Subclasses must implement this method with agent-specific logic.

        Args:
            inputs: The input data for the agent

        Returns:
            The output of the agent execution

        Raises:
            NotImplementedError: If the method is not implemented by a subclass
        """
        msg = "Subclasses must implement _execute method"
        raise NotImplementedError(msg)
