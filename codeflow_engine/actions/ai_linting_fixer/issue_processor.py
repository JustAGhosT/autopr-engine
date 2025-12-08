"""
Issue Processing Module

This module handles the processing of linting issues through the AI fixer pipeline.
"""

import logging
from typing import Any

from codeflow_engine.actions.ai_linting_fixer.ai_fix_applier import AIFixApplier
from codeflow_engine.actions.ai_linting_fixer.metrics import MetricsCollector
from codeflow_engine.actions.ai_linting_fixer.models import LintingIssue
from codeflow_engine.actions.ai_linting_fixer.queue_manager import IssueQueueManager
from codeflow_engine.actions.ai_linting_fixer.specialists.specialist_manager import (
    specialist_manager,
)


logger = logging.getLogger(__name__)


class IssueProcessor:
    """Handles the processing of linting issues through the AI fixer pipeline."""

    def __init__(
        self,
        queue_manager: IssueQueueManager,
        metrics: MetricsCollector,
        ai_fix_applier: AIFixApplier,
        session_id: str,
    ):
        """Initialize the issue processor."""
        self.queue_manager = queue_manager
        self.metrics = metrics
        self.ai_fix_applier = ai_fix_applier
        self.session_id = session_id

    async def process_issues(
        self,
        issues: list[dict[str, Any]],
        max_fixes_per_run: int,
        filter_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Process a batch of issues through the AI fixer pipeline."""
        total_processed = 0
        total_fixed = 0
        modified_files = []

        for i, issue_data in enumerate(issues):
            try:
                self.metrics.start_operation(f"fix_issue_{i}")

                # Apply AI fix with comprehensive workflow
                success = await self._apply_ai_fix_with_comprehensive_workflow(
                    issue_data
                )

                if success:
                    total_fixed += 1
                    modified_files.append(issue_data.get("file_path", "unknown"))

                    # Extract actual confidence and success from the result
                    confidence_score = (
                        success.get("confidence_score", 0.85)
                        if isinstance(success, dict)
                        else 0.85
                    )
                    fix_successful = (
                        success.get("final_success", True)
                        if isinstance(success, dict)
                        else True
                    )

                    # Safely get issue ID and update database
                    issue_id = issue_data.get("id")
                    if issue_id:
                        try:
                            self.queue_manager.update_issue_status(
                                issue_id,
                                "completed",
                                fix_result={
                                    "fix_successful": fix_successful,
                                    "confidence_score": confidence_score,
                                },
                            )
                        except Exception as e:
                            logger.exception(
                                f"Failed to update issue status for ID {issue_id}: {e}"
                            )
                    else:
                        logger.warning(f"No issue ID found in issue_data: {issue_data}")

                    self.metrics.record_fix_attempt(
                        success=fix_successful, confidence=confidence_score
                    )
                else:
                    self.metrics.record_fix_attempt(success=False)

                total_processed += 1

                # Check if we've reached the limit
                if total_fixed >= max_fixes_per_run:
                    logger.info(f"Reached max fixes limit ({max_fixes_per_run})")
                    break

            except Exception as e:
                logger.exception(f"Error processing issue {i}: {e}")
                self.metrics.record_fix_attempt(success=False)
                total_processed += 1

        return {
            "total_processed": total_processed,
            "total_fixed": total_fixed,
            "modified_files": modified_files,
        }

    async def _apply_ai_fix_with_comprehensive_workflow(
        self, issue_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply AI fix using the comprehensive workflow with splitting, test generation, and validation."""
        try:
            file_path = issue_data.get("file_path")
            error_code = issue_data.get("error_code", "")
            line_number = issue_data.get("line_number", 0)
            message = issue_data.get("message", "")

            if not file_path or not self._file_exists(file_path):
                return {
                    "final_success": False,
                    "error": f"File not found or does not exist: {file_path}",
                    "error_type": "file_not_found",
                }

            # Read the file content
            content = self._read_file_content(file_path)
            if content is None:
                return {
                    "final_success": False,
                    "error": f"Failed to read file content: {file_path}",
                    "error_type": "file_read_error",
                }

            # Create LintingIssue object
            issue = LintingIssue(
                file_path=file_path,
                line_number=line_number,
                column_number=issue_data.get("column_number", 0),
                error_code=error_code,
                message=message,
            )

            # Get the appropriate specialist agent for this issue type
            agent = specialist_manager.get_specialist_for_issues([issue])
            if not agent:
                logger.warning(f"No suitable agent found for {error_code}")
                return {
                    "final_success": False,
                    "error": f"No suitable agent found for error code: {error_code}",
                    "error_type": "no_agent_found",
                    "error_code": error_code,
                }

            # Apply the fix using comprehensive workflow
            result = await self.ai_fix_applier.apply_specialist_fix_with_comprehensive_workflow(
                agent, file_path, content, [issue], self.session_id
            )

            # Log comprehensive results
            if result.get("final_success", False):
                # Log detailed success information
                strategy = result.get("strategy_used", "unknown")
                file_split = result.get("file_split_performed", False)
                tests_generated = result.get("tests_generated", False)
                validation_passed = result.get("validation_passed", False)

                logger.info(
                    f"✅ Comprehensive fix successful for {error_code} in {file_path}\n"
                    f"   Strategy: {strategy}\n"
                    f"   File split: {file_split}\n"
                    f"   Tests generated: {tests_generated}\n"
                    f"   Validation passed: {validation_passed}"
                )

                return result
            else:
                # Log detailed failure information
                error = result.get("error", "Unknown error")
                rollback_performed = result.get("rollback_performed", False)
                validation_passed = result.get("validation_passed", False)

                logger.warning(
                    f"❌ Comprehensive fix failed for {error_code} in {file_path}\n"
                    f"   Error: {error}\n"
                    f"   Rollback performed: {rollback_performed}\n"
                    f"   Validation passed: {validation_passed}"
                )

                return result

        except Exception as e:
            logger.exception(f"Error applying comprehensive AI fix: {e}")
            return {"final_success": False, "error": str(e)}

    def _file_exists(self, file_path: str) -> bool:
        """Check if a file exists."""
        from pathlib import Path

        return Path(file_path).exists()

    def _read_file_content(self, file_path: str) -> str | None:
        """Read file content with error handling."""
        try:
            from pathlib import Path

            with Path(file_path).open("r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Error reading file {file_path}: {e}")
            return None

    def _apply_fix_to_file(self, file_path: str, fixed_content: str) -> bool:
        """Apply the fixed content to the file."""
        try:
            from pathlib import Path

            with Path(file_path).open("w", encoding="utf-8") as f:
                f.write(fixed_content)
            logger.info(f"Successfully applied fix to {file_path}")
            return True
        except Exception as e:
            logger.exception(f"Error applying fix to {file_path}: {e}")
            return False

    def get_next_issues(
        self, limit: int = 50, filter_types: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Get the next batch of issues to process."""
        return self.queue_manager.get_next_issues(
            limit=limit, worker_id=f"worker_{id(self)}", filter_types=filter_types
        )

    def queue_issues(self, issues: list[dict[str, Any]]) -> int:
        """Queue issues for processing."""
        return self.queue_manager.queue_issues(self.session_id, issues)
