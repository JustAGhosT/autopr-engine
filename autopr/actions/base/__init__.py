"""
AutoPR Action Base Classes

Base classes and interfaces for action implementation.
"""

from .action import Action
from .action_inputs import ActionInputs
from .action_outputs import ActionOutputs
from .github_action import GitHubAction
from .llm_action import LLMAction

__all__ = ["Action", "ActionInputs", "ActionOutputs", "GitHubAction", "LLMAction"]
