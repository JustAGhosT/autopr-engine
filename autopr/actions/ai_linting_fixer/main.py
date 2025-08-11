"""
Main AI Linting Fixer Module (Refactored)

This is the core module that orchestrates all the modular components
to provide AI-powered linting fixes. Much cleaner and focused!
"""

import logging
import random
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from autopr.actions.llm.manager import LLMProviderManager
from autopr.config.settings import AutoPRConfig  # type: ignore[attr-defined]

from .agents import AgentType, agent_manager
from .database import AIInteractionDB, IssueQueueManager
from .detection import issue_detector
from .display import DisplayConfig, OutputMode
from .display import display_provider_status as display_show_provider_status
from .display import get_display
from .display import print_feature_status as display_print_feature_status
from .file_ops import dry_run_ops, safe_file_ops
from .metrics import MetricsCollector
from .models import (
    AILintingFixerInputs,
    AILintingFixerOutputs,
    LintingFixResult,
    LintingIssue,
    create_empty_outputs,
)
from .workflow import WorkflowContext, WorkflowIntegrationMixin

# Optional Redis support
try:
    from .redis_queue import REDIS_AVAILABLE, RedisConfig, RedisQueueManager
except ImportError:
    REDIS_AVAILABLE = False
    # Do not assign RedisQueueManager = None here; just rely on REDIS_AVAILABLE

# Configure logging to suppress verbose provider warnings
logging.getLogger("autopr.actions.llm.manager").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

# Constants
DEFAULT_MAX_WORKERS = 4
DEFAULT_MAX_FIXES = 10
DEFAULT_SUCCESS_RATE_THRESHOLD = 0.5
DEFAULT_TIMEOUT_SECONDS = 200
DEFAULT_CACHE_TTL = 300
MIN_PARTS_FOR_PARSE = 4
MAX_CONTENT_PREVIEW = 200


# =============================================================================
# MAIN AI LINTING FIXER CLASS (Using Modular Architecture)
# =============================================================================


class AILintingFixer(WorkflowIntegrationMixin):
    """
    AI-powered linting fixer with modular architecture.

    This class now focuses only on the core AI fixing logic,
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

        # Use modular metrics collector
        self.metrics = MetricsCollector()
        self.metrics.start_session()

        # Database-first processing components
        self.db = AIInteractionDB()
        self.queue_manager = IssueQueueManager(self.db)
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        self.session_id = f"session_{timestamp}_{id(self)}"

        # Initialize modular components
        self.agent_manager = agent_manager
        self.issue_detector = issue_detector
        self.safe_file_ops = safe_file_ops
        self.dry_run_ops = dry_run_ops

        # Optional Redis support
        self.redis_manager = None
        if REDIS_AVAILABLE:
            try:
                self.redis_manager = RedisConfig.create_queue_manager()
            except Exception as e:
                logger.debug("Redis not available: %s", e)

        # Track processing statistics
        self.stats = {
            "issues_detected": 0,
            "issues_queued": 0,
            "issues_processed": 0,
            "issues_fixed": 0,
            "issues_failed": 0,
        }

    def run_flake8(self, target_path: str) -> list[LintingIssue]:
        """Run flake8 and parse issues (delegated to issue detection module in full version)."""
        self.metrics.start_operation("flake8")

        try:
            # Use the modular issue detector
            detected_issues = self.issue_detector.detect_issues(target_path)

            # Convert to the legacy LintingIssue format for compatibility
            issues = []
            for issue in detected_issues:
                legacy_issue = LintingIssue(
                    file_path=issue.file_path,
                    line_number=issue.line_number,
                    column_number=issue.column_number,
                    error_code=issue.error_code,
                    message=issue.message,
                    line_content=issue.line_content,
                )
                issues.append(legacy_issue)

        except (OSError, ValueError) as e:
            logger.warning("Failed to run flake8: %s", e)
            return []
        else:
            self.metrics.end_operation("flake8")
            return issues

    def _parse_flake8_standard_output(self, output: str) -> list[LintingIssue]:
        """Parse flake8 standard output format."""
        issues = []
        for line in output.strip().split("\n"):
            if not line.strip():
                continue
            try:
                # Parse format: file:line:col: code message
                parts = line.split(":", 3)
                if len(parts) >= MIN_PARTS_FOR_PARSE:
                    file_path = parts[0].strip()
                    line_num = int(parts[1].strip())
                    col_num = int(parts[2].strip())
                    code_msg = parts[3].strip()

                    # Extract error code
                    code_parts = code_msg.split(" ", 1)
                    error_code = code_parts[0]
                    message = code_parts[1] if len(code_parts) > 1 else ""

                    issues.append(
                        LintingIssue(
                            file_path=file_path,
                            line_number=line_num,
                            column_number=col_num,
                            error_code=error_code,
                            message=message,
                        )
                    )
            except (ValueError, IndexError) as e:
                logger.debug("Failed to parse flake8 line: %s - %s", line, e)
                continue

        return issues

    def select_specialized_agent(self, issues: list[LintingIssue]) -> Any:
        """Select the most appropriate specialized agent for a batch of issues."""
        if not issues:
            return self.agent_manager.get_agent_by_type(AgentType.GENERAL_FIXER)

        # Convert to the format expected by agent manager
        issue_dicts = [
            {
                "error_code": issue.error_code,
                "file_path": issue.file_path,
                "line_number": issue.line_number,
                "message": issue.message,
            }
            for issue in issues
        ]

        return self.agent_manager.select_agent_for_issues(issue_dicts)

    def apply_ai_fix(
        self,
        file_path: str,
        issues: list[LintingIssue],
        *,
        use_safe_ops: bool = True,
        _dry_run: bool = False,  # Unused parameter
    ) -> dict[str, Any]:
        """Apply an AI fix using the specified specialized agent."""
        try:
            # Read file content
            with Path(file_path).open(encoding="utf-8") as f:
                file_content = f.read()

            # Get appropriate agent for the issues
            agent = self.agent_manager.get_best_agent(issues)  # type: ignore[attr-defined]
            if not agent:
                return {
                    "success": False,
                    "error": "No suitable agent found for the issues",
                    "agent_type": "none",
                    "fixed_content": "",
                    "issues_addressed": 0,
                }

            # Apply the fix
            return self._simulate_agent_fix(
                file_path, file_content, agent, issues, use_safe_ops=use_safe_ops
            )

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent_type": "error",
                "fixed_content": "",
                "issues_addressed": 0,
            }

    def _simulate_agent_fix(
        self,
        file_path: str,
        file_content: str,
        agent: Any,
        issues: list[LintingIssue],
        *,
        use_safe_ops: bool,
    ) -> dict[str, Any]:
        """Simulate agent fix (placeholder for actual LLM integration)."""
        try:
            # Simulate AI processing
            agent_name = getattr(agent, "agent_type", "unknown")
            fixed_content = file_content + "\n# Fixed by AI agent: " + agent_name

            success = False
            if use_safe_ops:
                # Use safe file operations
                operation = self.safe_file_ops.plan_file_write(  # type: ignore[attr-defined]
                    file_path=file_path,
                    content=fixed_content,
                    reason=f"AI fix using {agent_name}",
                )
                success = operation.get("success", False)
            else:
                # Direct write (not recommended for production)
                with Path(file_path).open("w", encoding="utf-8") as f:
                    f.write(fixed_content)
                success = True

            return {
                "success": success,
                "confidence_score": 0.85,
                "agent_type": agent_name,
                "fixed_content": (
                    fixed_content[:MAX_CONTENT_PREVIEW] + "..."
                    if len(fixed_content) > MAX_CONTENT_PREVIEW
                    else fixed_content
                ),
                "issues_addressed": len(issues),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent_type": "error",
                "fixed_content": "",
                "issues_addressed": 0,
            }

    def queue_detected_issues(self, issues: list[LintingIssue], *, quiet: bool = False) -> int:
        """Queue detected linting issues for database-first processing."""
        if not quiet:
            logger.info("Queueing %d issues for processing", len(issues))

        # Queue issues in the database
        queued_count = 0
        for issue in issues:
            try:
                self.queue_manager.add_issue(issue)  # type: ignore[attr-defined]
                queued_count += 1
            except Exception as e:
                logger.warning("Failed to queue issue: %s", e)

        self.stats["issues_queued"] += queued_count
        return queued_count

    def _calculate_issue_priority(self, error_code: str) -> int:
        """Calculate priority for an issue type (1-10, higher = more priority)."""
        priority_map = {
            "F401": 8,  # Unused imports - high priority, easy to fix
            "F841": 7,  # Unused variable - high priority
            "E501": 6,  # Line too long - medium-high priority
            "E722": 5,  # Bare except - medium priority
            "F541": 4,  # F-string missing placeholders - medium-low priority
            "E741": 3,  # Ambiguous variable name - low priority
        }

        base_code = error_code.split("(")[0]  # Remove any parenthetical info
        return priority_map.get(base_code, 5)  # Default to medium priority

    def process_queued_issues(
        self,
        provider: str | None = None,
        model: str | None = None,
        filter_types: list[str] | None = None,
        *,
        quiet: bool = False,
    ) -> dict[str, Any]:
        """Process issues from the database queue using AI."""
        if not quiet:
            logger.info("Processing queued issues with AI")

        # Get issues from queue
        issues = self.queue_manager.get_pending_issues()  # type: ignore[attr-defined]
        if not issues:
            return {"success": True, "processed": 0, "fixed": 0}

        # Filter by type if specified
        if filter_types:
            issues = [
                issue
                for issue in issues
                if issue.get("error_code", "").split("(")[0] in filter_types
            ]

        total_processed = 0
        total_fixed = 0
        modified_files = []

        for i, issue_data in enumerate(issues):
            try:
                self.metrics.start_operation(f"fix_issue_{i}")

                # Simulate AI fix
                success = self._simulate_ai_fix_from_queue(issue_data, provider, model)

                if success:
                    total_fixed += 1
                    modified_files.append(issue_data.get("file_path", "unknown"))

                    # Update database
                    self.queue_manager.update_issue_status(  # type: ignore[attr-defined]
                        issue_data["id"], "fixed"
                    )

                    self.metrics.record_fix_attempt(success=True, confidence=0.85)
                else:
                    self.metrics.record_fix_attempt(success=False)

                total_processed += 1

            except Exception:
                logger.exception("Error fixing issue %s", issue_data)
                self.metrics.record_fix_attempt(success=False)
            finally:
                self.metrics.end_operation(f"fix_issue_{i}")

        return {
            "success": True,
            "processed": total_processed,
            "fixed": total_fixed,
            "modified_files": modified_files,
        }

    def fix_issues_with_ai(
        self,
        issues: list[LintingIssue],
        max_fixes: int = DEFAULT_MAX_FIXES,
        provider: str | None = None,
        model: str | None = None,
    ) -> LintingFixResult:
        """
        Fix issues using AI with clean architecture.

        In the full modular version, this would delegate to:
        - AgentManager for specialized fixing
        - FileOperations for safe file handling
        - Database module for logging
        """
        self.emit_event("started", {"total_issues": len(issues), "max_fixes": max_fixes})

        # Simplified implementation for demonstration
        # In full version, this would use the agent manager
        fixed_issues = []
        modified_files = []

        # For now, simulate some fixes
        for i, issue in enumerate(issues[:max_fixes]):
            self.metrics.start_operation(f"fix_issue_{i}")

            try:
                # Simulate AI fixing process
                success = self._simulate_ai_fix(issue, provider, model)

                if success:
                    fixed_issues.append(f"{issue.error_code}:{issue.line_number}")
                    if issue.file_path not in modified_files:
                        modified_files.append(issue.file_path)

                    self.metrics.record_fix_attempt(success=True, confidence=0.85)
                else:
                    self.metrics.record_fix_attempt(success=False)

            except Exception:
                logger.exception("Error fixing issue %s", issue)
                self.metrics.record_fix_attempt(success=False)
            finally:
                self.metrics.end_operation(f"fix_issue_{i}")

        self.emit_event(
            "completed", {"issues_fixed": len(fixed_issues), "files_modified": len(modified_files)}
        )

        return LintingFixResult(
            success=len(fixed_issues) > 0,
            fixed_issues=fixed_issues,
            remaining_issues=[
                f"{issue.error_code}:{issue.line_number}" for issue in issues[max_fixes:]
            ],
            modified_files=modified_files,
        )

    def _simulate_ai_fix(
        self, issue: LintingIssue, _provider: str | None, _model: str | None
    ) -> bool:
        """
        Simulate AI fixing for demonstration.
        In full version, this would call the actual LLM with the issue data.
        """
        self.metrics.record_api_call(1.5, tokens_used=150)  # Simulate API call

        # Simulate based on error code

        # Use different success rates for different error types
        success_rates = {
            "F401": 0.9,  # Unused imports - high success
            "E501": 0.7,  # Line too long - medium success
            "E302": 0.8,  # Expected 2 blank lines - high success
            "E303": 0.8,  # Too many blank lines - high success
            "E305": 0.9,  # Expected 2 blank lines after class - high success
            "E306": 0.8,  # Expected 1 blank line - high success
            "E711": 0.6,  # Comparison to None - medium success
            "E712": 0.6,  # Comparison to True/False - medium success
            "E713": 0.7,  # Test for membership - medium success
            "E714": 0.7,  # Test for object identity - medium success
            "E721": 0.5,  # Do not compare types - low success
            "E722": 0.4,  # Do not use bare except - low success
            "E731": 0.6,  # Do not assign a lambda expression - medium success
            "E741": 0.5,  # Do not use variables named 'l', 'O', or 'I' - low success
            "E742": 0.8,  # Do not define classes named 'l', 'O', or 'I' - high success
            "E743": 0.8,  # Do not define functions named 'l', 'O', or 'I' - high success
            "E901": 0.3,  # SyntaxError or IndentationError - very low success
            "E902": 0.3,  # IOError - very low success
            "W291": 0.9,  # Trailing whitespace - very high success
            "W292": 0.9,  # No newline at end of file - very high success
            "W293": 0.9,  # Blank line contains whitespace - very high success
            "W391": 0.9,  # Blank lines at end of file - very high success
            "W503": 0.6,  # Line break before binary operator - medium success
            "W504": 0.6,  # Line break after binary operator - medium success
            "W505": 0.6,  # doc line too long - medium success
            "W601": 0.7,  # .has_key() is deprecated - medium success
            "W602": 0.7,  # Deprecated form of raising exception - medium success
            "W603": 0.7,  # '<>' is deprecated - medium success
            "W604": 0.7,  # backticks are deprecated - medium success
            "W605": 0.6,  # Invalid escape sequence - medium success
            "W606": 0.6,  # 'async' and 'await' are reserved keywords - medium success
        }

        # Get success rate for this error code
        base_code = issue.error_code.split("(")[0]
        success_rate = success_rates.get(base_code, 0.5)

        return random.random() < success_rate  # - Used for simulation, not security

    def _simulate_ai_fix_from_queue(
        self, issue_data: dict[str, Any], _provider: str | None, _model: str | None
    ) -> bool:
        """
        Simulate AI fixing for demonstration using database queue data.
        In full version, this would call the actual LLM with the issue data.
        """
        self.metrics.record_api_call(1.5, tokens_used=150)  # Simulate API call

        # Simulate based on issue data

        # Extract issue type from data
        error_code = issue_data.get("error_code", "UNKNOWN")
        base_code = error_code.split("(")[0]

        # Use same success rates as _simulate_ai_fix
        success_rates = {
            "F401": 0.9,  # Unused imports - high success
            "E501": 0.7,  # Line too long - medium success
            "E302": 0.8,  # Expected 2 blank lines - high success
            "E303": 0.8,  # Too many blank lines - high success
            "E305": 0.9,  # Expected 2 blank lines after class - high success
            "E306": 0.8,  # Expected 1 blank line - high success
            "E711": 0.6,  # Comparison to None - medium success
            "E712": 0.6,  # Comparison to True/False - medium success
            "E713": 0.7,  # Test for membership - medium success
            "E714": 0.7,  # Test for object identity - medium success
            "E721": 0.5,  # Do not compare types - low success
            "E722": 0.4,  # Do not use bare except - low success
            "E731": 0.6,  # Do not assign a lambda expression - medium success
            "E741": 0.5,  # Do not use variables named 'l', 'O', or 'I' - low success
            "E742": 0.8,  # Do not define classes named 'l', 'O', or 'I' - high success
            "E743": 0.8,  # Do not define functions named 'l', 'O', or 'I' - high success
            "E901": 0.3,  # SyntaxError or IndentationError - very low success
            "E902": 0.3,  # IOError - very low success
            "W291": 0.9,  # Trailing whitespace - very high success
            "W292": 0.9,  # No newline at end of file - very high success
            "W293": 0.9,  # Blank line contains whitespace - very high success
            "W391": 0.9,  # Blank lines at end of file - very high success
            "W503": 0.6,  # Line break before binary operator - medium success
            "W504": 0.6,  # Line break after binary operator - medium success
            "W505": 0.6,  # doc line too long - medium success
            "W601": 0.7,  # .has_key() is deprecated - medium success
            "W602": 0.7,  # Deprecated form of raising exception - medium success
            "W603": 0.7,  # '<>' is deprecated - medium success
            "W604": 0.7,  # backticks are deprecated - medium success
            "W605": 0.6,  # Invalid escape sequence - medium success
            "W606": 0.6,  # 'async' and 'await' are reserved keywords - medium success
        }

        success_rate = success_rates.get(base_code, 0.5)
        return random.random() < success_rate  # - Used for simulation, not security

    def close(self) -> None:
        """Clean up resources and close connections."""
        try:
            # Close database connections
            if hasattr(self, "db"):
                self.db.close()  # type: ignore[attr-defined]

            # Close Redis connections
            if hasattr(self, "redis_manager") and self.redis_manager:
                self.redis_manager.close()  # type: ignore[attr-defined]

            # End metrics session
            if hasattr(self, "metrics"):
                self.metrics.end_session()

            logger.info("AI Linting Fixer resources cleaned up")

        except Exception:
            logger.exception("Error during cleanup")

    def get_queue_statistics(self) -> dict[str, Any]:
        """Get statistics about the issue queue."""
        if hasattr(self, "queue_manager"):
            return self.queue_manager.get_statistics()  # type: ignore[attr-defined,no-any-return]
        return {}

    def get_session_results(self) -> AILintingFixerOutputs:
        """Get comprehensive results from the current session."""
        if not hasattr(self, "metrics"):
            return create_empty_outputs(self.session_id)

        # Get metrics summary
        metrics_summary = self.metrics.get_summary()  # type: ignore[attr-defined]

        # Get queue statistics
        queue_stats = self.get_queue_statistics()

        # Get Redis statistics if available
        redis_stats = None
        if hasattr(self, "redis_manager") and self.redis_manager:
            with suppress(Exception):
                redis_stats = self.redis_manager.get_statistics()  # type: ignore[attr-defined]

        # Create comprehensive results
        return AILintingFixerOutputs(
            success=metrics_summary.get("success_rate", 0.0) > DEFAULT_SUCCESS_RATE_THRESHOLD,
            total_issues_found=metrics_summary.get("total_issues", 0),
            issues_fixed=metrics_summary.get("issues_fixed", 0),
            files_modified=metrics_summary.get("modified_files", []),
            summary=f"Session completed with {metrics_summary.get('success_rate', 0.0):.1%} success rate",
            total_issues_detected=metrics_summary.get("total_issues", 0),
            issues_queued=queue_stats.get("queued_count", 0),
            issues_processed=metrics_summary.get("issues_processed", 0),
            issues_failed=metrics_summary.get("issues_failed", 0),
            total_duration=metrics_summary.get("total_duration", 0.0),
            backup_files_created=metrics_summary.get("backup_files", 0),
            errors=metrics_summary.get("errors", []),
            warnings=metrics_summary.get("warnings", []),
            agent_stats=metrics_summary.get("agent_performance", {}),
            queue_stats=queue_stats,
            redis_stats=redis_stats,
            session_id=self.session_id,
            processing_mode="standalone",
            dry_run=False,
        )


# =============================================================================
# MAIN FUNCTION (Much Simpler!)
# =============================================================================


def ai_linting_fixer(inputs: AILintingFixerInputs) -> AILintingFixerOutputs:
    """
    Main AI linting function with clean modular architecture using new display system.

    This function now uses the modular display system for all UI interactions,
    providing clean separation between business logic and presentation.
    """

    # Initialize display system
    display_config = DisplayConfig(
        mode=(
            OutputMode.QUIET
            if inputs.quiet  # type: ignore[attr-defined]
            else (
                OutputMode.VERBOSE
                if inputs.verbose_metrics  # type: ignore[attr-defined]
                else OutputMode.NORMAL
            )
        )
    )
    display = get_display(display_config)

    try:
        # Initialize main fixer with all modular components
        fixer = AILintingFixer()

        # Show session start information
        display.operation.show_session_start(inputs, fixer.session_id)

        # Show provider status
        try:
            # Create default LLM config
            llm_config = {
                "default_provider": inputs.provider or "azure_openai",
                "fallback_order": ["azure_openai", "openai", "anthropic"],
                "providers": {
                    "azure_openai": {
                        "azure_endpoint": "https://dev-saf-openai-phoenixvc-ai.openai.azure.com/",
                        "api_version": "2024-02-01",
                        "deployment_name": inputs.model or "gpt-4.1",
                    }
                },
            }
            llm_manager = LLMProviderManager(llm_config)
            available_providers = llm_manager.get_available_providers()
            display.system.show_provider_status(available_providers)
        except Exception as e:
            logger.warning("Could not check provider status: %s", e)

        # Step 1: Detect issues
        display.operation.show_detection_progress(inputs.target_path)
        issues = fixer.issue_detector.detect_issues(inputs.target_path)

        # Update stats
        fixer.stats["issues_detected"] = len(issues)

        if not issues:
            # No issues found
            results = create_empty_outputs(fixer.session_id)
            results.success = True
            results.total_issues_detected = 0
            display.operation.show_detection_results(0, 0)
            display.results.show_results_summary(results)
            return results

        files_count = len({issue.file_path for issue in issues})
        display.operation.show_detection_results(len(issues), files_count)

        # Step 2: Queue issues for processing
        display.operation.show_queueing_progress(len(issues))

        # Convert issues to the format expected by queue_detected_issues
        legacy_issues = []
        for issue in issues:
            legacy_issue = LintingIssue(
                file_path=issue.file_path,
                line_number=issue.line_number,
                column_number=issue.column_number,
                error_code=issue.error_code,
                message=issue.message,
                line_content=issue.line_content,
            )
            legacy_issues.append(legacy_issue)

        queued_count = fixer.queue_detected_issues(legacy_issues, quiet=inputs.quiet)  # type: ignore[attr-defined]
        fixer.stats["issues_queued"] = queued_count
        display.operation.show_queueing_results(queued_count, len(issues))

        if queued_count == 0:
            # No issues queued
            results = create_empty_outputs(fixer.session_id)
            results.success = True
            results.total_issues_detected = len(issues)
            results.issues_queued = 0
            display.error.show_warning("No issues were queued for processing")
            return results

        # Step 3: Process issues
        processing_mode = "redis" if fixer.redis_manager else "local"
        display.operation.show_processing_start(len(legacy_issues))

        process_results = fixer.process_queued_issues(
            filter_types=inputs.filter_types,
            quiet=inputs.quiet,  # type: ignore[attr-defined]
        )

        # Update stats from processing results
        fixer.stats["issues_processed"] = process_results.get("processed", 0)
        fixer.stats["issues_fixed"] = process_results.get("fixed", 0)
        fixer.stats["issues_failed"] = process_results.get("failed", 0)

        display.operation.show_processing_results(
            process_results.get("fixed", 0), process_results.get("failed", 0)
        )

        # Show dry run notice if applicable
        if inputs.dry_run:
            display.operation.show_dry_run_notice()

        # Step 4: Generate final results
        final_results = fixer.get_session_results()

        # Display comprehensive results
        display.results.show_results_summary(final_results)
        if inputs.verbose_metrics:  # type: ignore[attr-defined]
            display.results.show_agent_performance(final_results.agent_stats)
            display.results.show_queue_statistics(final_results.queue_stats)
        display.results.show_suggestions(final_results)  # type: ignore[arg-type]

        return final_results

    except Exception as e:
        # Handle errors with display system
        error_msg = f"AI linting fixer failed: {e!s}"
        logger.exception(error_msg)
        display.error.show_error(error_msg)

        # Return error result
        error_results = create_empty_outputs("error")
        error_results.success = False
        error_results.errors = [error_msg]
        return error_results

    finally:
        # Clean up
        try:
            if "fixer" in locals():
                fixer.close()
        except Exception as e:
            logger.debug("Cleanup error: %s", e)


# Legacy compatibility functions


def print_feature_status() -> None:
    """Print feature status (legacy compatibility)."""

    # Get system features
    features = {
        "core_ai_linting": True,
        "orchestration": False,
        "temporal_integration": False,
        "celery_integration": False,
        "prefect_integration": False,
        "performance_metrics": True,
        "workflow_integration": True,
        "specialized_agents": True,
        "database_support": True,
        "redis_support": REDIS_AVAILABLE,
    }

    # Check orchestration availability
    try:
        from .orchestration import detect_available_orchestrators

        available_orchestrators = detect_available_orchestrators()
        features["orchestration"] = any(available_orchestrators.values())
        features["temporal_integration"] = available_orchestrators.get("temporal", False)
        features["celery_integration"] = available_orchestrators.get("celery", False)
        features["prefect_integration"] = available_orchestrators.get("prefect", False)
    except Exception:
        logger.debug("Failed to detect orchestrators")

    display_print_feature_status(features)


def display_provider_status(*, quiet: bool = False) -> None:
    """Display LLM provider status (legacy compatibility)."""

    try:
        # Create a basic config for LLMProviderManager

        config = AutoPRConfig()  # type: ignore[attr-defined]
        llm_manager = LLMProviderManager(config)
        available_providers = llm_manager.get_available_providers()
        display_show_provider_status(available_providers, quiet=quiet)
    except Exception:
        if not quiet:
            logger.debug("Failed to display provider status")
