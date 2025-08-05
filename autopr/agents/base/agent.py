"""
Base agent class for AutoPR agents.

This module provides the BaseAgent class which serves as the foundation for all
AutoPR agents. It handles common functionality like initialization, logging, and
volume-based configuration.
"""
from typing import Any, Dict, Optional, TypeVar, Generic, Type
from dataclasses import dataclass
from crewai import Agent as CrewAgent
from autopr.actions.llm import get_llm_provider_manager
from autopr.agents.base.volume_config import VolumeConfig


# Define generic type variables for input/output types
InputT = TypeVar('InputT')
OutputT = TypeVar('OutputT')


class BaseAgent(Generic[InputT, OutputT]):
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
        max_rpm: Optional[int] = None,
        **kwargs: Any
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
        self.agent = CrewAgent(
            name=self.name,
            role=self.role,
            backstory=self.backstory,
            verbose=self.verbose,
            allow_delegation=self.allow_delegation,
            max_iter=self.max_iter,
            max_rpm=self.max_rpm,
            **kwargs
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
            if self.verbose:
                print(f"Starting execution of {self.name} with inputs: {inputs}")
            
            # Delegate to the agent-specific implementation
            result = await self._execute(inputs)
            
            # Log the completion of execution
            if self.verbose:
                print(f"Completed execution of {self.name}")
                
            return result
            
        except Exception as e:
            # Log the error and re-raise
            error_msg = f"Error in {self.name}: {str(e)}"
            if self.verbose:
                print(error_msg)
            raise type(e)(error_msg) from e
    
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
        raise NotImplementedError("Subclasses must implement _execute method")
