"""
Workflow Orchestrator for AI Linting Fixer

This module contains the main workflow orchestration logic that was
previously in the main function, now properly separated and focused.
"""

import logging
import os
from typing import Any

from autopr.actions.ai_linting_fixer.core import AILintingFixer
from autopr.actions.ai_linting_fixer.detection import issue_detector
from autopr.actions.ai_linting_fixer.display import (DisplayConfig, OutputMode,
                                                     get_display)
from autopr.actions.ai_linting_fixer.models import (AILintingFixerInputs,
                                                    AILintingFixerOutputs,
                                                    LintingIssue,
                                                    create_empty_outputs)
from autopr.actions.llm.manager import \
    ActionLLMProviderManager as LLMProviderManager

logger = logging.getLogger(__name__)

# Constants
DEFAULT_SUCCESS_RATE_THRESHOLD = 0.5


class WorkflowOrchestrator:
    """
    Orchestrates the main AI linting workflow.

    This class handles the high-level flow of:
    1. Issue detection
    2. Issue queuing
    3. Issue processing
    4. Results generation
    """

    def __init__(self, display_config: DisplayConfig):
        """Initialize the workflow orchestrator."""
        self.display = get_display(display_config)

    def create_llm_manager(self, inputs: AILintingFixerInputs) -> LLMProviderManager:
        """Create and configure the LLM manager."""
        llm_config = {
            "default_provider": inputs.provider or "azure_openai",
            "fallback_order": ["azure_openai", "openai", "anthropic"],
            "providers": {
                "azure_openai": {
                    "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
                    "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
                    "deployment_name": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-35-turbo"),
                }
            },
        }
        return LLMProviderManager(llm_config)

    def detect_issues(self, target_path: str) -> list[Any]:
        """Detect linting issues in the target path."""
        self.display.operation.show_detection_progress(target_path)
        issues = issue_detector.detect_issues(target_path)

        if not issues:
            self.display.operation.show_detection_results(0, 0)
            return []

        files_count = len({issue.file_path for issue in issues})
        self.display.operation.show_detection_results(len(issues), files_count)
        return issues

    def convert_to_legacy_format(self, issues: list[Any]) -> list[LintingIssue]:
        """Convert modern issue format to legacy format for compatibility."""
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
        return legacy_issues

    def queue_issues(self, fixer: AILintingFixer, issues: list[LintingIssue], quiet: bool) -> int:
        """Queue detected issues for processing."""
        self.display.operation.show_queueing_progress(len(issues))

        queued_count = fixer.queue_detected_issues(issues, quiet=quiet)
        fixer.stats["issues_queued"] = queued_count

        self.display.operation.show_queueing_results(queued_count, len(issues))
        return queued_count

    async def process_issues(
        self,
        fixer: AILintingFixer,
        issues: list[LintingIssue],
        inputs: AILintingFixerInputs,
    ) -> dict[str, Any]:
        """Process queued issues."""
        # Note: processing mode could be used for future enhancements
        _processing_mode = (
            "redis" if hasattr(fixer, 'redis_manager') and fixer.redis_manager else "local"
        )
        self.display.operation.show_processing_start(len(issues))

        process_results = await fixer.process_queued_issues(
            filter_types=inputs.fix_types,
            max_fixes=inputs.max_fixes_per_run,
            quiet=inputs.quiet,
        )

        # Update stats from processing results
        fixer.stats["issues_processed"] = process_results.get("processed", 0)
        fixer.stats["issues_fixed"] = process_results.get("fixed", 0)
        fixer.stats["issues_failed"] = process_results.get("failed", 0)

        self.display.operation.show_processing_results(
            process_results.get("fixed", 0), process_results.get("failed", 0)
        )

        return process_results

    def generate_final_results(
        self, fixer: AILintingFixer, inputs: AILintingFixerInputs
    ) -> AILintingFixerOutputs:
        """Generate the final results output."""
        session_results = fixer.get_session_results()

        # Convert dict to AILintingFixerOutputs instance
        final_results = AILintingFixerOutputs(
            total_issues_found=session_results.get("total_issues", 0),
            issues_fixed=session_results.get("successful_fixes", 0),
            files_modified=[],  # This would need to be filled from fixer if available
            success=session_results.get("success_rate", 0.0) > 0.5,
            summary=(
                f"Processed {session_results.get('total_issues', 0)} issues with "
                f"{session_results.get('success_rate', 0.0):.1%} success rate"
            ),
            total_issues_detected=session_results.get("total_issues", 0),
            issues_processed=session_results.get("total_issues", 0),
            issues_failed=session_results.get("failed_fixes", 0),
            total_duration=session_results.get("duration", 0.0),
            session_id=session_results.get("session_id"),
            agent_stats=session_results.get("stats", {}),
            queue_stats={},  # This would need to be filled from fixer if available
        )

        # Display comprehensive results
        self.display.results.show_results_summary(final_results)
        if inputs.verbose_metrics:
            self.display.results.show_agent_performance(final_results.agent_stats)
            self.display.results.show_queue_statistics(final_results.queue_stats)
        # Generate suggestions based on results
        suggestions = []
        if final_results.issues_failed > 0:
            suggestions.append("Review failed fixes and consider manual intervention")
        success_rate = final_results.issues_fixed / max(final_results.total_issues_found, 1)
        if success_rate < 0.8:
            suggestions.append("Consider adjusting fix parameters or reviewing code patterns")
        self.display.results.show_suggestions(suggestions)

        return final_results

    def create_error_output(self, error_msg: str) -> AILintingFixerOutputs:
        """Create error output when something goes wrong."""
        error_results = create_empty_outputs("error")
        error_results.success = False
        error_results.errors = [error_msg]
        return error_results


async def orchestrate_ai_linting_workflow(inputs: AILintingFixerInputs) -> AILintingFixerOutputs:
    """
    Main workflow orchestration function.

    This function orchestrates the entire AI linting workflow using
    the WorkflowOrchestrator class for clean separation of concerns.
    """
    # Initialize display system
    display_config = DisplayConfig(
        mode=(
            OutputMode.QUIET
            if inputs.quiet
            else (
                OutputMode.VERBOSE
                if inputs.verbose_metrics
                else OutputMode.NORMAL
            )
        )
    )

    orchestrator = WorkflowOrchestrator(display_config)
    display = orchestrator.display

    try:
        # Create LLM manager
        llm_manager = orchestrator.create_llm_manager(inputs)

        # Initialize main fixer
        fixer = AILintingFixer(llm_manager=llm_manager)

        # Show session start information
        display.operation.show_session_start(inputs, fixer.session_id)

        # Show provider status
        try:
            available_providers = llm_manager.get_available_providers()
            display.system.show_provider_status(available_providers)
        except Exception as e:
            logger.warning("Could not check provider status: %s", e)

        # Step 1: Detect issues
        issues = orchestrator.detect_issues(inputs.target_path)
        fixer.stats["issues_detected"] = len(issues)

        if not issues:
            # No issues found
            results = create_empty_outputs(fixer.session_id)
            results.success = True
            results.total_issues_detected = 0
            display.results.show_results_summary(results)
            return results

        # Step 2: Convert and queue issues
        legacy_issues = orchestrator.convert_to_legacy_format(issues)
        queued_count = orchestrator.queue_issues(fixer, legacy_issues, inputs.quiet)

        if queued_count == 0:
            # No issues queued
            results = create_empty_outputs(fixer.session_id)
            results.success = True
            results.total_issues_detected = len(issues)
            results.issues_queued = 0
            display.error.show_warning("No issues were queued for processing")
            return results

        # Step 3: Process issues
        process_results = await orchestrator.process_issues(fixer, legacy_issues, inputs)

        # Show dry run notice if applicable
        if inputs.dry_run:
            display.operation.show_dry_run_notice()

        # Step 4: Generate final results
        return orchestrator.generate_final_results(fixer, inputs)

    except Exception as e:
        # Handle errors with display system
        error_msg = f"AI linting fixer failed: {e}"
        logger.exception(error_msg)
        display.error.show_error(error_msg)

        return orchestrator.create_error_output(error_msg)

    finally:
        # Clean up
        try:
            if "fixer" in locals():
                fixer.close()
        except Exception as e:
            logger.debug("Cleanup error: %s", e)
