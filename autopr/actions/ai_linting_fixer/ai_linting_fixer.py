"""
AI Linting Fixer

A comprehensive AI-powered linting fixer that automatically detects and fixes Python code issues
using advanced language models and specialized agents.
"""

import logging
import time
from typing import Any, BaseException

from autopr.actions.llm.manager import LLMProviderManager

from .ai_agent_manager import AIAgentManager
from .code_analyzer import CodeAnalyzer
from .detection import IssueDetector
from .display import AILintingFixerDisplay, DisplayConfig
from .error_handler import ErrorHandler
from .file_manager import FileManager
from .issue_fixer import IssueFixer
from .models import AILintingFixerInputs, AILintingFixerOutputs
from .performance_tracker import PerformanceTracker

logger = logging.getLogger(__name__)


class AILintingFixer:
    """Main AI Linting Fixer class that orchestrates all components."""

    def __init__(self, display_config: DisplayConfig | None = None):
        """Initialize the AI Linting Fixer with all components."""
        # Set logging levels to ERROR by default to prevent clutter
        logging.getLogger("autopr.actions.ai_linting_fixer").setLevel(logging.ERROR)
        logging.getLogger("autopr.actions.llm").setLevel(logging.ERROR)
        logging.getLogger("httpx").setLevel(logging.ERROR)

        # Initialize display
        self.display = AILintingFixerDisplay(display_config)

        # Initialize core components
        self.performance_tracker = PerformanceTracker(display=self.display)
        self.error_handler = ErrorHandler()

        # Initialize LLM manager with default config
        llm_config = {
            "default_provider": "azure_openai",
            "fallback_order": ["azure_openai"],  # Only use Azure OpenAI
            "azure_openai": {
                "azure_endpoint": "https://dev-saf-openai-phoenixvc-ai.openai.azure.com/",
                "api_key": None,  # Will be loaded from environment
            },
        }
        self.llm_manager = LLMProviderManager(llm_config, display=self.display)

        # Initialize specialized components
        self.issue_detector = IssueDetector()
        self.code_analyzer = CodeAnalyzer()
        self.ai_agent_manager = AIAgentManager(self.llm_manager, self.performance_tracker)
        self.file_manager = FileManager()
        self.issue_fixer = IssueFixer(self.ai_agent_manager, self.file_manager, self.error_handler)

        # Initialize database for logging interactions
        try:
            from .database import AIInteractionDB

            self.database = AIInteractionDB()
            self.issue_fixer.database = self.database
        except Exception as e:
            logger.warning(f"Failed to initialize database: {e}")
            self.database = None

        logger.info("AI Linting Fixer initialized with modular components")

    def _analyze_error(self, error: Exception) -> dict[str, Any]:
        """Analyze an error and provide detailed information for drill-down."""
        error_type = type(error).__name__
        error_msg = str(error)

        analysis = {
            "error_type": error_type,
            "error_message": error_msg,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "severity": "high" if "validation" in error_type.lower() else "medium",
            "category": self._categorize_error(error),
            "context": self._get_error_context(error),
            "stack_trace": self._get_stack_trace(error),
            "suggested_actions": [],
        }

        # Add specific analysis based on error type
        if "validation" in error_type.lower():
            analysis.update(self._analyze_validation_error(error))
        elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            analysis.update(self._analyze_connection_error(error))
        elif "permission" in error_msg.lower():
            analysis.update(self._analyze_permission_error(error))

        return analysis

    def _categorize_error(self, error: Exception) -> str:
        """Categorize the error for better understanding."""
        error_msg = str(error).lower()

        if "validation" in error_msg:
            return "data_validation"
        if "connection" in error_msg or "timeout" in error_msg:
            return "network"
        if "permission" in error_msg or "access" in error_msg:
            return "permission"
        if "file" in error_msg or "path" in error_msg:
            return "file_system"
        if "api" in error_msg or "key" in error_msg:
            return "api"
        return "general"

    def _get_error_context(self, error: Exception) -> dict[str, Any]:
        """Get context information about when/where the error occurred."""
        return {
            "session_id": getattr(self, "session_id", "unknown"),
            "processing_stage": "workflow_execution",
            "components_initialized": {
                "display": hasattr(self, "display"),
                "llm_manager": hasattr(self, "llm_manager"),
                "issue_detector": hasattr(self, "issue_detector"),
                "file_manager": hasattr(self, "file_manager"),
                "database": hasattr(self, "database") and self.database is not None,
            },
        }

    def _get_stack_trace(self, error: Exception) -> str:
        """Get a formatted stack trace for the error."""
        import traceback

        return "".join(traceback.format_exception(type(error), error, error.__traceback__))

    def _analyze_validation_error(self, error: Exception) -> dict[str, Any]:
        """Analyze validation errors specifically."""
        error_msg = str(error)

        # Extract field names from validation error
        import re

        field_matches = re.findall(r"'([^']+)'", error_msg)

        return {
            "validation_details": {
                "missing_fields": field_matches,
                "error_pattern": "missing_required_fields",
                "model_affected": "AILintingFixerOutputs",
            },
            "suggested_actions": [
                "Check that all required fields are being set in the output creation",
                "Verify the AILintingFixerOutputs model definition",
                "Use --verbose flag for detailed error information",
            ],
        }

    def _analyze_connection_error(self, error: Exception) -> dict[str, Any]:
        """Analyze connection-related errors."""
        return {
            "connection_details": {
                "error_type": "network_timeout_or_connection_failure",
                "affected_component": "LLM provider",
            },
            "suggested_actions": [
                "Check your internet connection",
                "Verify API key is valid and has sufficient credits",
                "Try using a different LLM provider",
                "Check if the service is experiencing downtime",
            ],
        }

    def _analyze_permission_error(self, error: Exception) -> dict[str, Any]:
        """Analyze permission-related errors."""
        return {
            "permission_details": {
                "error_type": "file_or_directory_access_denied",
                "affected_operation": "file reading/writing",
            },
            "suggested_actions": [
                "Check file permissions in the target directory",
                "Ensure you have write access to the backup directory",
                "Run with elevated permissions if necessary",
                "Verify the file paths are correct",
            ],
        }

    def _get_error_recovery_suggestions(self, error_details: dict[str, Any]) -> list[str]:
        """Get specific recovery suggestions based on error analysis."""
        suggestions = []

        # Add general suggestions
        suggestions.extend(
            (
                "Use --verbose flag for detailed error information",
                "Check the logs for additional context",
            )
        )

        # Add specific suggestions based on error category
        category = error_details.get("category", "general")
        if category == "data_validation":
            suggestions.extend(
                [
                    "Verify input parameters are correct",
                    "Check model field definitions",
                    "Ensure all required fields are provided",
                ]
            )
        elif category == "network":
            suggestions.extend(
                [
                    "Check internet connection",
                    "Verify API credentials",
                    "Try again in a few minutes",
                ]
            )
        elif category == "permission":
            suggestions.extend(
                [
                    "Check file permissions",
                    "Verify directory access rights",
                    "Run with appropriate permissions",
                ]
            )

        # Add suggestions from error analysis
        if "suggested_actions" in error_details:
            suggestions.extend(error_details["suggested_actions"])

        return suggestions

    def run(self, inputs: AILintingFixerInputs) -> AILintingFixerOutputs:
        """Run the complete AI linting fixer workflow."""
        start_time = time.time()

        try:
            # Configure display based on inputs
            if hasattr(inputs, "verbose") and inputs.verbose:
                self.display.set_verbose(True)
                # Set logging to DEBUG for verbose mode
                logging.getLogger("autopr.actions.ai_linting_fixer").setLevel(logging.DEBUG)
                logging.getLogger("autopr.actions.llm").setLevel(logging.DEBUG)
                logging.getLogger("httpx").setLevel(logging.DEBUG)
            elif hasattr(inputs, "quiet") and inputs.quiet:
                self.display.set_quiet(True)
                # Set logging to ERROR only for quiet mode
                logging.getLogger("autopr.actions.ai_linting_fixer").setLevel(logging.ERROR)
                logging.getLogger("autopr.actions.llm").setLevel(logging.ERROR)
                logging.getLogger("httpx").setLevel(logging.ERROR)

            # Show session start
            session_id = f"session_{int(start_time)}"
            self.display.operation.show_session_start(inputs, session_id)

            # Use display for user-facing messages instead of logger
            self.display.error.show_info("Starting AI Linting Fixer workflow")

            # Step 1: Detect linting issues
            self.display.operation.show_detection_progress(inputs.target_path)

            issues = self.issue_detector.detect_issues(inputs.target_path)

            # Filter issues by specified types
            if inputs.fix_types:
                filtered_issues = [
                    issue for issue in issues if issue.error_code in inputs.fix_types
                ]
                self.display.error.show_info(
                    f"Filtered to {len(filtered_issues)} issues of specified types"
                )
            else:
                filtered_issues = issues

            # Calculate unique files for accurate reporting
            unique_files = len({issue.file_path for issue in filtered_issues})
            self.display.operation.show_detection_results(
                len(filtered_issues), len(issues), unique_files
            )

            if not filtered_issues:
                self.display.error.show_info("No issues found to fix")
                return AILintingFixerOutputs(
                    success=True,
                    total_issues_found=len(issues),
                    issues_fixed=0,
                    files_modified=[],
                    summary="No linting issues found to fix",
                    total_issues_detected=len(issues),
                    issues_processed=0,
                    issues_failed=0,
                    total_duration=time.time() - start_time,
                    backup_files_created=0,
                    agent_stats={},
                    queue_stats={},
                    session_id=session_id,
                    processing_mode="standalone",
                    dry_run=getattr(inputs, "dry_run", False),
                )

            # Step 2: Create backups if requested
            backup_count = 0
            if hasattr(inputs, "create_backups") and inputs.create_backups:
                # Get unique files that will be modified
                unique_files = list({issue.file_path for issue in filtered_issues})
                self.display.operation.show_backup_creation(len(unique_files))
                backup_count = self.file_manager.create_backups(unique_files)
                self.display.error.show_info(f"Created {backup_count} backup files")

            # Step 3: Process issues with AI
            self.display.operation.show_processing_start(len(filtered_issues))

            # Limit to max_fixes
            issues_to_process = filtered_issues[: inputs.max_fixes]
            self.display.error.show_info(
                f"Starting AI-powered fix for {len(issues_to_process)} issues"
            )

            processed_issues = []
            failed_issues = []
            files_modified = set()

            for i, issue in enumerate(issues_to_process, 1):
                self.display.operation.show_processing_progress(i, len(issues_to_process), issue)

                try:
                    # Read current file content
                    content = self.file_manager.read_file(issue.file_path)
                    if content is None:
                        self.display.error.show_warning(f"Could not read file: {issue.file_path}")
                        failed_issues.append(issue)
                        continue

                    # Fix the issue
                    result = self.issue_fixer._fix_single_issue(
                        file_path=issue.file_path,
                        content=content,
                        issue=issue,
                        provider=inputs.provider,
                        model=inputs.model,
                    )

                    if result.get("success", False):
                        # Write the fixed content
                        if not hasattr(inputs, "dry_run") or not inputs.dry_run:
                            success = self.file_manager.write_file(
                                issue.file_path, result["content"]
                            )
                            if success:
                                files_modified.add(issue.file_path)
                                processed_issues.append(issue)
                                confidence = result.get("confidence", 0.0)
                                self.display.error.show_info(
                                    f"✅ Fixed {issue.error_code} in {issue.file_path} (confidence: {confidence:.3f})"
                                )
                            else:
                                failed_issues.append(issue)
                                self.display.error.show_error(
                                    f"Failed to write fixed content to {issue.file_path}"
                                )
                        else:
                            processed_issues.append(issue)
                            self.display.error.show_info(
                                f"🔍 Would fix {issue.error_code} in {issue.file_path} (dry run)"
                            )
                    else:
                        failed_issues.append(issue)
                        error_msg = result.get("error", "Unknown error")
                        self.display.error.show_warning(
                            f"❌ Failed to fix {issue.error_code}: {error_msg}"
                        )

                except Exception as e:
                    failed_issues.append(issue)
                    self.display.error.show_error(f"Error processing {issue.error_code}: {e!s}")

            # Show processing results
            self.display.operation.show_processing_results(
                len(processed_issues), len(failed_issues)
            )

            # Generate results
            processing_duration = time.time() - start_time

            # Get performance metrics
            performance_summary = self.performance_tracker.get_performance_summary()

            # Create suggestions
            suggestions: list[str] = []
            if failed_issues:
                suggestions.append("Try increasing --max-fixes if you want to process more issues")
            suggestions.append("Check if the specified fix types match available issues")
            if hasattr(inputs, "verbose") and not inputs.verbose:
                suggestions.append("Use --verbose for detailed performance metrics")
            suggestions.append("Use --db-stats to view database statistics")

            # Create output
            outputs = AILintingFixerOutputs(
                success=len(failed_issues) == 0,
                total_issues_found=len(issues),
                issues_fixed=len(processed_issues),
                files_modified=list(files_modified),
                summary=f"Fixed {len(processed_issues)} out of {len(issues)} issues",
                total_issues_detected=len(issues),
                issues_processed=len(processed_issues),
                issues_failed=len(failed_issues),
                total_duration=processing_duration,
                backup_files_created=backup_count,
                agent_stats=performance_summary.get("agent_performance", {}),
                queue_stats=performance_summary.get("queue_statistics", {}),
                session_id=session_id,
                processing_mode="standalone",
                dry_run=getattr(inputs, "dry_run", False),
            )

            # Show results
            self.display.results.show_results_summary(outputs)
            self.display.results.show_agent_performance(outputs.agent_stats)
            self.display.results.show_queue_statistics(outputs.queue_stats)
            self.display.results.show_suggestions(suggestions)

            return outputs

        except Exception as e:
            # Enhanced error handling with drill-down capability
            error_details = self._analyze_error(e)
            self.display.error.show_error(f"Error in AI Linting Fixer workflow: {e!s}")

            # Show detailed error information
            if hasattr(inputs, "verbose") and inputs.verbose:
                self.display.error.show_error_details(error_details)

            # Show recovery suggestions
            suggestions = self._get_error_recovery_suggestions(error_details)
            self.display.error.show_suggested_actions(suggestions)

            raise
        finally:
            # Cleanup
            logger.info("AI Linting Fixer resources cleaned up")

    def __enter__(self) -> "AILintingFixer":
        """Context manager entry."""
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any
    ) -> None:
        """Context manager exit."""
        try:
            # End performance tracking
            self.performance_tracker.end_session()

            # Export final metrics
            self.performance_tracker.export_metrics()

            # Use display module for user-facing messages
            if self.display:
                self.display.error.show_info("🔧 AI Linting Fixer resources cleaned up")
            else:
                logger.info("AI Linting Fixer resources cleaned up")

        except Exception as e:
            if self.display:
                self.display.error.show_warning(f"⚠️ Error during cleanup: {e}")
            else:
                logger.exception(f"Error during cleanup: {e}")


# Convenience functions for backward compatibility
def create_ai_linting_fixer(display_config: DisplayConfig | None = None) -> AILintingFixer:
    """Create an AI linting fixer with default configuration."""
    return AILintingFixer(display_config=display_config)


def run_ai_linting_fixer(
    target_path: str,
    fix_types: list[str] | None = None,
    max_fixes: int = 10,
    provider: str | None = None,
    model: str | None = None,
    max_workers: int = 4,
) -> AILintingFixerOutputs:
    """Run the AI linting fixer with simple parameters."""
    inputs = AILintingFixerInputs(
        target_path=target_path,
        fix_types=fix_types or ["E501", "F401", "F841", "E722"],
        max_fixes=max_fixes,
        provider=provider,
        model=model,
        max_workers=max_workers,
    )

    fixer = AILintingFixer()
    return fixer.run(inputs)
