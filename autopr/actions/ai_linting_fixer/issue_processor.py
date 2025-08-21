"""
Issue Processing Module

This module handles the processing of linting issues through the AI fixer pipeline.
"""

import logging
from typing import Any, Dict, List, Optional

from autopr.actions.ai_linting_fixer.agents import specialist_manager
from autopr.actions.ai_linting_fixer.database import IssueQueueManager
from autopr.actions.ai_linting_fixer.metrics import MetricsCollector
from autopr.actions.ai_linting_fixer.models import LintingIssue
from autopr.actions.ai_linting_fixer.ai_fix_applier import AIFixApplier


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

    def process_issues(
        self,
        issues: List[Dict[str, Any]],
        max_fixes_per_run: int,
        filter_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Process a batch of issues through the AI fixer pipeline."""
        total_processed = 0
        total_fixed = 0
        modified_files = []

        for i, issue_data in enumerate(issues):
            try:
                self.metrics.start_operation(f"fix_issue_{i}")

                # Apply AI fix
                success = self._apply_ai_fix(issue_data)

                if success:
                    total_fixed += 1
                    modified_files.append(issue_data.get("file_path", "unknown"))

                    # Update database
                    self.queue_manager.update_issue_status(
                        issue_data["id"],
                        "completed",
                        fix_result={"fix_successful": True, "confidence_score": 0.85},
                    )

                    self.metrics.record_fix_attempt(success=True, confidence=0.85)
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

    def _apply_ai_fix(self, issue_data: Dict[str, Any]) -> bool:
        """Apply AI fix to a single issue."""
        try:
            file_path = issue_data.get("file_path")
            error_code = issue_data.get("error_code", "")
            line_number = issue_data.get("line_number", 0)
            message = issue_data.get("message", "")

            if not file_path or not self._file_exists(file_path):
                return False

            # Read the file content
            content = self._read_file_content(file_path)
            if content is None:
                return False

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
                return False

            # Apply the fix using the specialist agent with real AI integration
            fix_result = self.ai_fix_applier.apply_specialist_fix(
                agent, file_path, content, [issue]
            )

            if fix_result["success"]:
                # Apply the fix to the file
                return self._apply_fix_to_file(file_path, fix_result["fixed_content"])
            else:
                logger.warning(
                    f"AI fix failed for {file_path}: {fix_result.get('error', 'Unknown error')}"
                )
                return False

        except Exception as e:
            logger.exception(f"Error applying AI fix: {e}")
            return False

    def _file_exists(self, file_path: str) -> bool:
        """Check if a file exists."""
        from pathlib import Path

        return Path(file_path).exists()

    def _read_file_content(self, file_path: str) -> Optional[str]:
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
            logger.error(f"Error applying fix to {file_path}: {e}")
            return False

    def get_next_issues(
        self, limit: int = 50, filter_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get the next batch of issues to process."""
        return self.queue_manager.get_next_issues(
            limit=limit, worker_id=f"worker_{id(self)}", filter_types=filter_types
        )

    def queue_issues(self, issues: List[Dict[str, Any]]) -> int:
        """Queue issues for processing."""
        return self.queue_manager.queue_issues(self.session_id, issues)
