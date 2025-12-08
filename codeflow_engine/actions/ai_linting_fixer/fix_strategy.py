"""
Fix Strategy Module

Coordinates different fix application strategies following the Strategy Pattern.
"""

import logging
from typing import Any

from codeflow_engine.actions.ai_linting_fixer.file_persistence import FilePersistenceManager
from codeflow_engine.actions.ai_linting_fixer.llm_client import LLMClient
from codeflow_engine.actions.ai_linting_fixer.models import LintingIssue
from codeflow_engine.actions.ai_linting_fixer.response_parser import ResponseParser
from codeflow_engine.actions.ai_linting_fixer.validation_manager import ValidationManager


logger = logging.getLogger(__name__)


class FixStrategy:
    """Base class for fix application strategies."""

    def __init__(
        self,
        llm_client: LLMClient,
        response_parser: ResponseParser,
        persistence_manager: FilePersistenceManager,
        validation_manager: ValidationManager,
    ):
        """Initialize the fix strategy.
        
        Args:
            llm_client: LLM client for AI operations
            response_parser: Parser for LLM responses
            persistence_manager: File persistence manager
            validation_manager: Fix validation manager
        """
        self.llm_client = llm_client
        self.response_parser = response_parser
        self.persistence_manager = persistence_manager
        self.validation_manager = validation_manager

    async def apply_fix(
        self,
        agent: Any,
        file_path: str,
        content: str,
        issues: list[LintingIssue],
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Apply fix using this strategy.
        
        Args:
            agent: AI agent for generating prompts
            file_path: Path to file being fixed
            content: Current file content
            issues: List of issues to fix
            session_id: Session ID for backup management
            
        Returns:
            Fix result dictionary
        """
        raise NotImplementedError("Subclasses must implement apply_fix")


class BasicFixStrategy(FixStrategy):
    """Basic fix strategy with model fallback."""

    async def apply_fix(
        self,
        agent: Any,
        file_path: str,
        content: str,
        issues: list[LintingIssue],
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Apply basic fix with model fallback."""
        from codeflow_engine.actions.ai_linting_fixer.model_competency import competency_manager

        try:
            # Get prompts from agent
            system_prompt = agent.get_system_prompt()
            user_prompt = agent.get_user_prompt(file_path, content, issues)

            # Get error codes and fallback sequence
            error_codes = [issue.error_code.split("(")[0] for issue in issues]
            primary_error = error_codes[0] if error_codes else "UNKNOWN"
            fallback_sequence = competency_manager.get_fallback_sequence(primary_error)

            # Try each model in fallback sequence
            for model_name, provider_name in fallback_sequence:
                try:
                    logger.info("Trying %s via %s for %s", model_name, provider_name, primary_error)

                    # Create request
                    request = self.llm_client.create_request(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        provider=provider_name,
                        model=model_name,
                        temperature=0.1,
                        max_tokens=2000,
                    )

                    # Call LLM
                    response = await self.llm_client.complete(request)

                    if not response:
                        logger.warning("LLM error with %s: No response received", model_name)
                        continue

                    # Extract fixed code
                    fixed_content = self.response_parser.extract_code_from_response(response.content)
                    if not fixed_content:
                        logger.warning("No code extracted from %s response", model_name)
                        continue

                    # Validate the fix
                    validation_result = self._validate_fix(content, fixed_content, issues)
                    if validation_result["is_valid"]:
                        # Calculate confidence
                        confidence = competency_manager.calculate_confidence(
                            model_name, primary_error, fix_successful=True
                        )

                        logger.info(
                            "Successfully fixed %s with %s (confidence: %.2f)",
                            primary_error, model_name, confidence
                        )

                        return {
                            "success": True,
                            "fixed_content": fixed_content,
                            "confidence_score": confidence,
                            "agent_type": f"ai_{agent.agent_type.value}",
                            "model_used": model_name,
                            "provider_used": provider_name,
                        }
                    else:
                        logger.warning(
                            "Fix validation failed for %s: %s",
                            model_name, validation_result['reason']
                        )
                        continue

                except Exception as e:
                    logger.warning("Error with %s: %s", model_name, e)
                    continue

            # All models failed
            logger.warning("All models failed to fix %s", primary_error)
            return {
                "success": False,
                "error": f"All AI models failed to fix {primary_error}",
                "agent_type": f"ai_{agent.agent_type.value}",
            }

        except Exception as e:
            logger.exception("Error in basic fix strategy: %s", e)
            return {"success": False, "error": str(e)}

    def _validate_fix(self, original: str, fixed: str, issues: list[LintingIssue]) -> dict[str, Any]:
        """Validate a fix attempt."""
        try:
            # Basic validation checks
            if not fixed or not fixed.strip():
                return {"is_valid": False, "reason": "Empty or whitespace-only fix"}

            if fixed == original:
                return {"is_valid": False, "reason": "No changes detected"}

            # Check for Python syntax validity
            try:
                compile(fixed, '<string>', 'exec')
            except SyntaxError as e:
                return {"is_valid": False, "reason": f"Syntax error: {e}"}

            # More sophisticated validation would go here
            # For now, basic checks are sufficient
            return {"is_valid": True, "reason": "Basic validation passed"}

        except Exception as e:
            return {"is_valid": False, "reason": f"Validation error: {e}"}


class ValidationStrategy(FixStrategy):
    """Strategy that includes validation and persistence."""

    async def apply_fix(
        self,
        agent: Any,
        file_path: str,
        content: str,
        issues: list[LintingIssue],
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Apply fix with validation and persistence."""
        # First apply basic fix
        basic_strategy = BasicFixStrategy(
            self.llm_client,
            self.response_parser,
            self.persistence_manager,
            self.validation_manager,
        )

        fix_result = await basic_strategy.apply_fix(agent, file_path, content, issues, session_id)

        if not fix_result.get("success", False):
            return fix_result

        # Validate the fix
        should_keep_fix = True
        validation_checks = []

        try:
            error_codes = [issue.error_code.split("(")[0] for issue in issues]
            should_keep_fix, validation_checks = (
                self.validation_manager.validate_file_fix(
                    file_path,
                    content,
                    fix_result.get("fixed_content", ""),
                    error_codes,
                )
            )
        except Exception as e:
            logger.exception("Validation failed for %s: %s", file_path, e)
            should_keep_fix = False
            validation_checks = []

        # Persist or rollback based on validation
        if should_keep_fix and fix_result.get("fixed_content"):
            persistence_result = await self.persistence_manager.persist_fix(
                file_path,
                fix_result["fixed_content"],
                session_id,
                create_backup=True,
            )
        else:
            # Rollback if validation failed
            persistence_result = {"write_success": False, "backup_created": False, "rollback_performed": False}
            if not should_keep_fix:
                rollback_success = self.persistence_manager.rollback_if_needed(
                    file_path, True, session_id
                )
                persistence_result["rollback_performed"] = rollback_success

        # Update result with validation and persistence info
        fix_result.update({
            "validation_performed": True,
            "validation_passed": should_keep_fix,
            "validation_checks": [
                {
                    "name": check.check_name,
                    "result": check.result.value,
                    "message": check.message,
                    "execution_time": check.execution_time,
                }
                for check in validation_checks
            ],
            **persistence_result,
            "final_success": (
                fix_result.get("success", False)
                and should_keep_fix
                and persistence_result.get("write_success", False)
            ),
        })

        return fix_result


class StrategySelector:
    """Selects appropriate fix strategy based on context."""

    def __init__(
        self,
        llm_client: LLMClient,
        response_parser: ResponseParser,
        persistence_manager: FilePersistenceManager,
        validation_manager: ValidationManager,
    ):
        """Initialize the strategy selector."""
        self.llm_client = llm_client
        self.response_parser = response_parser
        self.persistence_manager = persistence_manager
        self.validation_manager = validation_manager

    def get_strategy(self, strategy_name: str = "validation") -> FixStrategy:
        """Get a fix strategy by name.
        
        Args:
            strategy_name: Name of strategy ("basic", "validation")
            
        Returns:
            Appropriate fix strategy instance
        """
        if strategy_name == "basic":
            return BasicFixStrategy(
                self.llm_client,
                self.response_parser,
                self.persistence_manager,
                self.validation_manager,
            )
        elif strategy_name == "validation":
            return ValidationStrategy(
                self.llm_client,
                self.response_parser,
                self.persistence_manager,
                self.validation_manager,
            )
        else:
            # Default to validation strategy
            return ValidationStrategy(
                self.llm_client,
                self.response_parser,
                self.persistence_manager,
                self.validation_manager,
            )
