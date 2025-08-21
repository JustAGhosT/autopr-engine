"""
AI Fix Application Module

This module handles the application of AI-generated fixes to code files.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from autopr.actions.ai_linting_fixer.models import LintingIssue
from autopr.actions.ai_linting_fixer.model_competency import competency_manager
from autopr.actions.ai_linting_fixer.backup_manager import BackupManager
from autopr.actions.ai_linting_fixer.validation_manager import (
    ValidationManager,
    ValidationConfig,
)
from autopr.actions.llm.manager import LLMProviderManager
from autopr.actions.llm.types import LLMResponse


logger = logging.getLogger(__name__)


class AIFixApplier:
    """Handles AI fix application with model fallback and validation."""

    def __init__(
        self,
        llm_manager: LLMProviderManager,
        backup_manager: Optional[BackupManager] = None,
        validation_config: Optional[ValidationConfig] = None,
    ):
        """Initialize the AI fix applier."""
        self.llm_manager = llm_manager
        self.backup_manager = backup_manager or BackupManager()
        self.validation_manager = ValidationManager(
            validation_config or ValidationConfig()
        )
        self.enable_validation = True
        self.enable_backup = True

    def apply_specialist_fix_with_validation(
        self,
        agent: Any,
        file_path: str,
        content: str,
        issues: List[LintingIssue],
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Apply fix with backup, validation, and rollback capability."""
        # 1. Create backup if enabled
        backup = None
        if self.enable_backup:
            backup = self.backup_manager.backup_file(file_path, session_id)
            if not backup:
                logger.error(f"Failed to create backup for {file_path}")
                return {
                    "success": False,
                    "error": "Backup creation failed",
                    "rollback_performed": False,
                }

        # 2. Apply the fix
        fix_result = self.apply_specialist_fix(agent, file_path, content, issues)

        if not fix_result.get("success", False):
            return fix_result

        # 3. Validate the fix if enabled
        should_keep_fix = True
        validation_checks = []

        if self.enable_validation:
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
                logger.error(f"Validation failed for {file_path}: {e}")
                should_keep_fix = False
                validation_checks = []

        # 4. Apply rollback if validation failed
        rollback_performed = False
        if not should_keep_fix and backup:
            logger.info(f"Validation failed, rolling back {file_path}")
            rollback_success = self.backup_manager.restore_file(file_path, session_id)
            rollback_performed = rollback_success

            if not rollback_success:
                logger.error(f"Rollback failed for {file_path}")

        # 5. Update result with validation info
        fix_result.update(
            {
                "validation_performed": self.enable_validation,
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
                "backup_created": backup is not None,
                "rollback_performed": rollback_performed,
                "final_success": fix_result.get("success", False) and should_keep_fix,
            }
        )

        return fix_result

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
        """Extract code from LLM response with intelligent patching."""
        if not response_content:
            return None

        # Look for code blocks first
        code_block_pattern = r"```(?:python)?\s*\n(.*?)\n```"
        matches = re.findall(code_block_pattern, response_content, re.DOTALL)

        if matches:
            extracted_code = matches[0].strip()
            # Check if this looks like a complete file or just a patch
            if self._is_complete_file(extracted_code):
                return extracted_code
            else:
                # This might be a partial fix - try to extract targeted changes
                return self._extract_targeted_changes(response_content, extracted_code)

        # Look for specific line changes in the response
        line_change_pattern = r"(?:Line \d+:|^\d+\.|^[+-])\s*(.+)"
        line_changes = re.findall(line_change_pattern, response_content, re.MULTILINE)

        if line_changes:
            # This suggests targeted line changes rather than full file replacement
            return "\n".join(line_changes)

        # If no code blocks, try to extract the entire response if it looks like code
        lines = response_content.strip().split("\n")
        if len(lines) > 3 and any(
            "def " in line or "import " in line or "class " in line
            for line in lines[:5]
        ):
            return response_content.strip()

        return None

    def _is_complete_file(self, code: str) -> bool:
        """Check if the extracted code represents a complete file."""
        lines = code.split("\n")

        # Heuristics for complete file:
        # 1. Has imports at the beginning
        # 2. Has class or function definitions
        # 3. Is longer than 10 lines
        # 4. Doesn't start with partial constructs

        has_imports = any(
            line.strip().startswith(("import ", "from ")) for line in lines[:10]
        )
        has_definitions = any("def " in line or "class " in line for line in lines)
        is_substantial = len(lines) > 10
        starts_cleanly = not any(
            lines[0].strip().startswith(prefix)
            for prefix in ["...", "# Fix:", "# Change:"]
        )

        return has_imports and has_definitions and is_substantial and starts_cleanly

    def _extract_targeted_changes(self, full_response: str, code_block: str) -> str:
        """Extract targeted changes from AI response instead of full file replacement."""
        # Look for specific change indicators in the response
        change_indicators = [
            r"(?:Change|Fix|Replace|Update) line (\d+)",
            r"Line (\d+):\s*(.+)",
            r"On line (\d+),?\s*(.+)",
            r"(\d+):\s*(.+)",
        ]

        changes = []
        for pattern in change_indicators:
            matches = re.findall(pattern, full_response, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if len(match) == 2:  # Line number and change
                    line_num, change = match
                    changes.append(f"Line {line_num}: {change}")
                elif len(match) == 1:  # Just line number, need to find the change
                    line_num = match[0]
                    # Look for the next non-empty line as the change
                    response_lines = full_response.split("\n")
                    for i, line in enumerate(response_lines):
                        if line_num in line:
                            if i + 1 < len(response_lines):
                                change_line = response_lines[i + 1].strip()
                                if change_line and not change_line.startswith(
                                    ("#", "//")
                                ):
                                    changes.append(f"Line {line_num}: {change_line}")
                            break

        if changes:
            return "\n".join(changes)

        # Fallback to original code block if no targeted changes found
        return code_block

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
