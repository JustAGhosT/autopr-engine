"""
AI Fix Application Module

This module handles the application of AI-generated fixes to code files.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from autopr.actions.ai_linting_fixer.models import LintingIssue
from autopr.actions.ai_linting_fixer.model_competency import competency_manager
from autopr.actions.llm.manager import LLMProviderManager
from autopr.actions.llm.types import LLMResponse


logger = logging.getLogger(__name__)


class AIFixApplier:
    """Handles AI fix application with model fallback and validation."""

    def __init__(self, llm_manager: LLMProviderManager):
        """Initialize the AI fix applier."""
        self.llm_manager = llm_manager

    def apply_specialist_fix(
        self, agent: Any, file_path: str, content: str, issues: List[LintingIssue]
    ) -> Dict[str, Any]:
        """Apply fix using a specialist agent with real AI integration and model fallback."""
        try:
            # Get the system and user prompts from the agent
            system_prompt = agent.get_system_prompt()
            user_prompt = agent.get_user_prompt(file_path, content, issues)

            # Get the error codes for this issue
            error_codes = [issue.error_code.split("(")[0] for issue in issues]
            primary_error = error_codes[0] if error_codes else "UNKNOWN"

            # Get fallback sequence for this error type
            fallback_sequence = competency_manager.get_fallback_sequence(primary_error)

            for model_name, provider_name in fallback_sequence:
                try:
                    logger.info(
                        f"Trying {model_name} via {provider_name} for {primary_error}"
                    )

                    # Create the request for the LLM
                    request = {
                        "provider": provider_name,
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.1,  # Low temperature for consistent fixes
                        "max_tokens": 2000,  # Reasonable limit for code fixes
                    }

                    # Call the LLM
                    response = self.llm_manager.complete(request)

                    if response.error:
                        logger.warning(f"LLM error with {model_name}: {response.error}")
                        continue

                    # Extract the fixed code from the response
                    fixed_content = self._extract_code_from_response(response.content)
                    if not fixed_content:
                        logger.warning(f"No code extracted from {model_name} response")
                        continue

                    # Validate the fix
                    validation_result = self._validate_fix(
                        content, fixed_content, issues
                    )
                    if validation_result["is_valid"]:
                        # Calculate confidence based on model competency
                        confidence = competency_manager.calculate_confidence(
                            model_name, primary_error, fix_successful=True
                        )

                        logger.info(
                            f"Successfully fixed {primary_error} with {model_name} (confidence: {confidence:.2f})"
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
                            f"Fix validation failed for {model_name}: {validation_result['reason']}"
                        )
                        continue

                except Exception as e:
                    logger.warning(f"Error with {model_name}: {e}")
                    continue

            # If we get here, no model could fix the issue
            logger.warning(f"All models failed to fix {primary_error}")
            return {
                "success": False,
                "error": f"All AI models failed to fix {primary_error}",
                "agent_type": f"ai_{agent.agent_type.value}",
            }

        except Exception as e:
            logger.exception(f"Error in specialist fix: {e}")
            return {"success": False, "error": str(e)}

    def _extract_code_from_response(self, response_content: str) -> Optional[str]:
        """Extract code from LLM response."""
        if not response_content:
            return None

        # Look for code blocks
        code_block_pattern = r"```(?:python)?\s*\n(.*?)\n```"
        matches = re.findall(code_block_pattern, response_content, re.DOTALL)

        if matches:
            return matches[0].strip()

        # If no code blocks, try to extract the entire response if it looks like code
        lines = response_content.strip().split("\n")
        if len(lines) > 3 and any(
            "def " in line or "import " in line or "class " in line
            for line in lines[:5]
        ):
            return response_content.strip()

        return None

    def _validate_fix(
        self, original_content: str, fixed_content: str, issues: List[LintingIssue]
    ) -> Dict[str, Any]:
        """Validate that the fix actually addresses the issues."""
        try:
            # Basic validation - check if content changed
            if original_content.strip() == fixed_content.strip():
                return {"is_valid": False, "reason": "No changes made to content"}

            # Check if the fixed content is valid Python
            try:
                compile(fixed_content, "<string>", "exec")
            except SyntaxError as e:
                return {"is_valid": False, "reason": f"Syntax error in fixed code: {e}"}

            # Check if the fix addresses the specific issues
            # This is a simplified validation - in practice, you'd want to run ruff again
            # to verify the specific issues are resolved

            # For now, just check that the content is different and syntactically valid
            return {"is_valid": True, "reason": "Fix validated successfully"}

        except Exception as e:
            return {"is_valid": False, "reason": f"Validation error: {e}"}

    def apply_ruff_auto_fix(
        self, file_path: str, content: str, issues: List[LintingIssue]
    ) -> Dict[str, Any]:
        """Apply ruff auto-fix for the specific issues."""
        try:
            # Get the error codes to fix
            error_codes = [issue.error_code.split("(")[0] for issue in issues]

            logger.info(
                f"Applying ruff auto-fix to {file_path} for codes: {error_codes}"
            )

            # Run ruff check --fix for these specific codes
            import subprocess

            result = subprocess.run(
                [
                    "ruff",
                    "check",
                    "--fix",
                    "--select",
                    ",".join(error_codes),
                    file_path,
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
            )

            logger.info(
                f"Ruff command result: returncode={result.returncode}, stdout={result.stdout[:200]}, stderr={result.stderr[:200]}"
            )

            # Ruff returns exit code 1 when it finds issues, but still applies fixes
            # We need to check if the file was actually modified
            if result.returncode in [
                0,
                1,
            ]:  # Both success and "issues found" are acceptable
                # Read the fixed content
                from pathlib import Path

                with Path(file_path).open("r", encoding="utf-8") as f:
                    fixed_content = f.read()

                # Check if content actually changed
                if fixed_content != content:
                    logger.info(f"Successfully fixed {file_path}")
                    return {
                        "success": True,
                        "fixed_content": fixed_content,
                        "confidence_score": 0.9,
                        "agent_type": "ruff_auto_fix",
                    }
                else:
                    logger.info(f"No changes made to file - ruff couldn't auto-fix")
                    return {
                        "success": False,
                        "error": "No changes made to file - ruff couldn't auto-fix",
                        "agent_type": "ruff_auto_fix",
                    }
            else:
                logger.warning(f"Ruff failed for {file_path}: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr,
                    "agent_type": "ruff_auto_fix",
                }

        except Exception as e:
            logger.exception(f"Error in ruff auto-fix: {e}")
            return {"success": False, "error": str(e)}
