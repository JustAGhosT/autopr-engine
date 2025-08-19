"""
AutoPR Action Base Classes

Base classes and interfaces for action implementation.
"""

from autopr.actions.base.action import Action
from autopr.actions.base.action_inputs import ActionInputs
from autopr.actions.base.action_outputs import ActionOutputs
from autopr.actions.base.github_action import GitHubAction
from autopr.actions.base.llm_action import LLMAction

__all__ = ["Action", "ActionInputs", "ActionOutputs", "GitHubAction", "LLMAction"]
