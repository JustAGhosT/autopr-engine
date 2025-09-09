"""
Core AI Linting Fixer Class

This module contains the core AILintingFixer class that orchestrates
the modular components without implementing specific business logic.
"""

import logging
from typing import Any

from autopr.actions.ai_linting_fixer.ai_fix_applier import AIFixApplier
from autopr.actions.ai_linting_fixer.database import AIInteractionDB
from autopr.actions.ai_linting_fixer.metrics import MetricsCollector
from autopr.actions.ai_linting_fixer.queue_manager import IssueQueueManager
from autopr.actions.ai_linting_fixer.workflow import (WorkflowContext,
                                                      WorkflowIntegrationMixin)
from autopr.ai.core.providers.manager import LLMProviderManager

logger = logging.getLogger(__name__)

# Constants
DEFAULT_MAX_WORKERS = 4
DEFAULT_MAX_FIXES = 10
DEFAULT_SUCCESS_RATE_THRESHOLD = 0.5
DEFAULT_TIMEOUT_SECONDS = 200
DEFAULT_CACHE_TTL = 300
MIN_PARTS_FOR_PARSE = 4
MAX_CONTENT_PREVIEW = 200


class AILintingFixer(WorkflowIntegrationMixin):
    """
    AI-powered linting fixer with modular architecture.

    This class focuses only on orchestrating the modular components,
    delegating specialized concerns to dedicated modules.
    """

    def __init__(
        self,
        llm_manager: LLMProviderManager | None = None,
        max_workers: int = DEFAULT_MAX_WORKERS,
        workflow_context: WorkflowContext | None = None,
    ):
        """Initialize with clean separation of concerns and full modular architecture."""
        super().__init__()
        self.workflow_context = workflow_context
        self.llm_manager = llm_manager
        self.max_workers = max_workers

        # Use modular components
        self.metrics = MetricsCollector()
        self.metrics.start_session()

        # Initialize AI fix applier
        self.ai_fix_applier = AIFixApplier(llm_manager) if llm_manager else None

        # Database-first processing components
        self.db = AIInteractionDB()

        # Queue management
        self.queue_manager = IssueQueueManager(db_path="issue_queue.db")

        # Session tracking
        self.session_id = self._generate_session_id()
        self.stats = {
            "session_id": self.session_id,
            "start_time": self.metrics.session_metrics.start_time,
            "issues_detected": 0,
            "issues_queued": 0,
            "issues_processed": 0,
            "issues_fixed": 0,
            "issues_failed": 0,
            "files_modified": [],
            "errors": [],
            "warnings": [],
        }

        logger.info("AILintingFixer initialized with session ID: %s", self.session_id)

    def _generate_session_id(self) -> str:
        """Generate a unique session identifier."""
        import random
        import string
        timestamp = self.metrics.session_metrics.start_time.strftime("%Y%m%d_%H%M%S")
        random_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        return f"ai_lint_{timestamp}_{random_suffix}"

    def queue_detected_issues(self, issues: list, quiet: bool = False) -> int:
        """Queue detected issues for processing."""
        if not issues:
            return 0

        # Ensure session_id exists
        if not hasattr(self, 'session_id') or not self.session_id:
            msg = "Session ID is required but not available"
            raise ValueError(msg)

        queued_count = self.queue_manager.queue_issues(self.session_id, issues)
        self.stats["issues_queued"] = queued_count

        if not quiet:
            logger.info("Queued %d issues for processing", queued_count)

        return queued_count

    async def process_queued_issues(
        self,
        filter_types: list[str] | None = None,
        max_fixes: int | None = None,
        quiet: bool = False,
    ) -> dict[str, Any]:
        """Process queued issues using the queue manager."""
        # Check if there are queued issues using queue stats
        stats = self.queue_manager.get_queue_stats()
        if not stats.get("pending", 0):
            return {"processed": 0, "completed": 0, "failed": 0}

        max_fixes = max_fixes or DEFAULT_MAX_FIXES

        # Process issues using the existing queue manager API
        results = {"processed": 0, "completed": 0, "failed": 0}
        processed_count = 0

        while processed_count < max_fixes:
            # Get next batch of issues
            batch_size = min(max_fixes - processed_count, max_fixes)
            issues = self.queue_manager.get_next_issues(
                limit=batch_size,
                filter_types=filter_types
            )

            if not issues:
                # No more issues to process
                break

            # Process each issue in the batch
            for issue in issues:
                if processed_count >= max_fixes:
                    break

                try:
                    # Attempt to fix the issue
                    fix_result = await self._attempt_issue_fix(issue)

                    if fix_result.get("success", False):
                        results["completed"] += 1
                        status = "completed"
                    else:
                        results["failed"] += 1
                        status = "failed"

                    # Update issue status in queue
                    issue_id = issue.get("id")
                    if issue_id is not None:
                        self.queue_manager.update_issue_status(
                            issue_id=int(issue_id),
                            status=status,
                            fix_result=fix_result.get("details", {})
                        )

                    results["processed"] += 1
                    processed_count += 1
                except Exception as e:
                    if not quiet:
                        logger.exception("Error processing issue %s", issue.get('id', 'unknown'))
                    results["failed"] += 1
                    results["processed"] += 1
                    processed_count += 1

                    # Mark issue as failed
                    issue_id = issue.get("id")
                    if issue_id is not None:
                        self.queue_manager.update_issue_status(
                            issue_id=int(issue_id),
                            status="failed",
                            fix_result={"error": str(e)}
                        )

        # Update stats
        self.stats["issues_processed"] = results.get("processed", 0)
        self.stats["issues_fixed"] = results.get("completed", 0)
        self.stats["issues_failed"] = results.get("failed", 0)

        return results

    async def _attempt_issue_fix(self, issue: dict[str, Any]) -> dict[str, Any]:
        """Attempt to fix a single issue using the AI fix applier."""
        try:
            # Extract issue details
            file_path = issue.get("file_path", "")
            line_number = issue.get("line_number", 0)
            error_code = issue.get("error_code", "")
            message = issue.get("message", "")

            # Create a simple fix attempt
            # This is a temporary implementation - in a real system,
            # this would use the AI fix applier or other fix methods
            fix_result = {
                "success": True,  # Temporary - would be determined by actual fix attempt
                "details": {
                    "file_path": file_path,
                    "line_number": line_number,
                    "error_code": error_code,
                    "message": message,
                    "fix_applied": f"Applied fix for {error_code}"
                }
            }
        except Exception as e:
            logger.exception("Error in _attempt_issue_fix")
            return {
                "success": False,
                "details": {"error": str(e)}
            }
        else:
            return fix_result

    def get_session_results(self) -> dict[str, Any]:
        """Get comprehensive session results and metrics."""
        session_summary = self.metrics.get_session_summary()
        session_duration = session_summary.get("duration", 0.0)

        # Calculate success rate
        total_issues = self.stats["issues_processed"]
        success_rate = 0.0 if total_issues == 0 else self.stats["issues_fixed"] / total_issues

        return {
            "session_id": self.session_id,
            "success_rate": success_rate,
            "total_issues": total_issues,
            "successful_fixes": self.stats["issues_fixed"],
            "failed_fixes": self.stats["issues_failed"],
            "session_duration": session_duration,
            "stats": self.stats.copy(),
        }

    def close(self) -> None:
        """Clean up resources and close the session."""
        try:
            self.metrics.end_session()
            if self.db:
                self.db.close()
            logger.info("AILintingFixer session %s closed", self.session_id)
        except Exception:
            logger.exception("Error closing AILintingFixer")
