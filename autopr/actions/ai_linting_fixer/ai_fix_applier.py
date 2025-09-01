"""
AI Linting Fixer - Main Application Logic

Core application logic for AI-powered code fixing.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from autopr.actions.ai_linting_fixer.backup_manager import BackupManager
from autopr.actions.ai_linting_fixer.file_splitter import SplitConfig
from autopr.actions.ai_linting_fixer.models import (LintingFixResult,
                                                    LintingIssue)
from autopr.actions.ai_linting_fixer.validation_manager import ValidationConfig
from autopr.actions.base.action import Action
from autopr.ai.core.providers.manager import LLMProviderManager

logger = logging.getLogger(__name__)


class AIFixApplier:
    """Simplified AI fix applier following SOLID principles."""

    def __init__(
        self,
        llm_manager: LLMProviderManager,
        backup_manager: BackupManager | None = None,
        validation_config: ValidationConfig | None = None,
    ):
        """Initialize the modular AI fix applier.

        Args:
            llm_manager: Required LLM provider manager for AI operations
            backup_manager: Optional backup manager for file operations
            validation_config: Optional validation configuration

        Raises:
            ValueError: If llm_manager is None
        """
        if llm_manager is None:
            msg = (
                "llm_manager is required and cannot be None. "
                "AIFixApplier requires an LLMProviderManager to perform AI operations."
            )
            raise ValueError(msg)

        # Initialize core components following Dependency Injection
        self.llm_client = LLMClient(llm_manager)
        self.response_parser = ResponseParser()
        self.persistence_manager = FilePersistenceManager(backup_manager)
        self.validation_manager = ValidationManager(validation_config or ValidationConfig())

        # Initialize strategy selector
        self.strategy_selector = StrategySelector(
            self.llm_client,
            self.response_parser,
            self.persistence_manager,
            self.validation_manager,
        )

        self.session_id = None

    async def apply_specialist_fix_with_validation(
        self,
        agent: Any,
        file_path: str,
        content: str,
        issues: list[LintingIssue],
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Apply fix with validation using the validation strategy.

        This method maintains compatibility with the original interface while
        delegating to the modular strategy system.

        Args:
            agent: AI agent for generating prompts
            file_path: Path to file being fixed
            content: Current file content
            issues: List of issues to fix
            session_id: Session ID for backup management

        Returns:
            Fix result dictionary with validation and persistence info
        """
        strategy = self.strategy_selector.get_strategy("validation")
        return await strategy.apply_fix(agent, file_path, content, issues, session_id)

    async def apply_specialist_fix(
        self,
        agent: Any,
        file_path: str,
        content: str,
        issues: list[LintingIssue],
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Apply fix using basic strategy without validation.

        This method maintains compatibility with the original interface.

        Args:
            agent: AI agent for generating prompts
            file_path: Path to file being fixed
            content: Current file content
            issues: List of issues to fix
            session_id: Session ID for backup management

        Returns:
            Fix result dictionary
        """
        strategy = self.strategy_selector.get_strategy("basic")
        return await strategy.apply_fix(agent, file_path, content, issues, session_id)

    async def apply_fix_with_strategy(
        self,
        strategy_name: str,
        agent: Any,
        file_path: str,
        content: str,
        issues: list[LintingIssue],
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Apply fix using a specific strategy.

        Args:
            strategy_name: Name of strategy to use ("basic", "validation")
            agent: AI agent for generating prompts
            file_path: Path to file being fixed
            content: Current file content
            issues: List of issues to fix
            session_id: Session ID for backup management

        Returns:
            Fix result dictionary
        """
        strategy = self.strategy_selector.get_strategy(strategy_name)
        return await strategy.apply_fix(agent, file_path, content, issues, session_id)

    # Utility methods for backward compatibility
    def set_session_id(self, session_id: str) -> None:
        """Set the session ID for backup management."""
        self.session_id = session_id

    def get_response_parser(self):
        """Get the response parser instance."""
        return None

    def get_llm_client(self):
        """Get the LLM client instance."""
        return None

    def get_persistence_manager(self):
        """Get the file persistence manager instance."""
        return None

    def get_validation_manager(self):
        """Get the validation manager instance."""
        return None
