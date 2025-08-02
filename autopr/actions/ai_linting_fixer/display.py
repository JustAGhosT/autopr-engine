"""
Display and UI Module for AI Linting Fixer

This module handles all user interface, formatting, and output display.
It provides a clean separation between business logic and presentation.

Key Principles:
- No business logic, only presentation
- Consistent formatting and styling
- Support for different output modes (normal, quiet, verbose)
- Emoji and color support for better UX
- Easy to test and modify
"""

from dataclasses import dataclass
from enum import Enum
import logging
import sys
from typing import Any, TextIO

from .models import (  # SessionMetrics, # Removed; ProcessingMode, # Removed
    AILintingFixerInputs,
    AILintingFixerOutputs,
    LintingIssue,
)

logger = logging.getLogger(__name__)


class OutputMode(Enum):
    """Output verbosity modes."""

    QUIET = "quiet"
    NORMAL = "normal"
    VERBOSE = "verbose"
    DEBUG = "debug"


class DisplayTheme(Enum):
    """Display themes for different contexts."""

    DEFAULT = "default"
    MINIMAL = "minimal"
    ENTERPRISE = "enterprise"
    DEV = "dev"


@dataclass
class DisplayConfig:
    """Configuration for display output."""

    mode: OutputMode = OutputMode.NORMAL
    theme: DisplayTheme = DisplayTheme.DEFAULT
    use_colors: bool = True
    use_emojis: bool = True
    output_stream: TextIO = sys.stdout
    error_stream: TextIO = sys.stderr
    line_width: int = 80

    def is_quiet(self) -> bool:
        return self.mode == OutputMode.QUIET

    def is_verbose(self) -> bool:
        return self.mode in {OutputMode.VERBOSE, OutputMode.DEBUG}


class DisplayFormatter:
    """Handles formatting and styling of output."""

    def __init__(self, config: DisplayConfig):
        self.config = config

        # Define emoji sets by theme
        self.emojis = {
            DisplayTheme.DEFAULT: {
                "success": "✅",
                "error": "❌",
                "warning": "⚠️",
                "info": "ℹ️",
                "processing": "🔄",
                "detection": "🔍",
                "agent": "🤖",
                "file": "📁",
                "backup": "🛡️",
                "metrics": "📊",
                "redis": "🚀",
                "database": "🗄️",
                "config": "⚙️",
                "queue": "📋",
                "timer": "⏱️",
                "target": "🎯",
                "dry_run": "🧪",
                "celebration": "🎉",
                "suggestion": "💡",
            },
            DisplayTheme.MINIMAL: {},  # No emojis
            DisplayTheme.ENTERPRISE: {
                "success": "[OK]",
                "error": "[ERROR]",
                "warning": "[WARN]",
                "info": "[INFO]",
                "processing": "[PROC]",
            },
            DisplayTheme.DEV: {
                "success": "✓",
                "error": "✗",
                "warning": "⚠",
                "info": "→",
            },
        }

    def emoji(self, name: str) -> str:
        """Get emoji for the current theme."""
        if not self.config.use_emojis:
            return ""

        theme_emojis = self.emojis.get(self.config.theme, {})
        emoji = theme_emojis.get(name, "")
        return f"{emoji} " if emoji else ""

    def header(self, text: str, level: int = 1) -> str:
        """Format a header."""
        if level == 1:
            return f"\n{text}\n{'=' * len(text)}"
        if level == 2:
            return f"\n{text}\n{'-' * len(text)}"
        return f"\n{text}:"

    def section(self, title: str, emoji_name: str = "info") -> str:
        """Format a section header."""
        return f"\n{self.emoji(emoji_name)}{title}"

    def item(self, text: str, indent: int = 1) -> str:
        """Format a list item."""
        prefix = "   " * indent + "• "
        return f"{prefix}{text}"

    def metric(self, label: str, value: Any, emoji_name: str = "info") -> str:
        """Format a metric display."""
        return f"   {self.emoji(emoji_name)}{label}: {value}"

    def separator(self, char: str = "=", length: int | None = None) -> str:
        """Create a separator line."""
        length = length or self.config.line_width
        return char * length

    def progress_bar(self, current: int, total: int, width: int = 30) -> str:
        """Create a simple progress bar."""
        percentage = 0 if total == 0 else min(100, current / total * 100)

        filled = int(width * percentage / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {percentage:.1f}% ({current}/{total})"


class SystemStatusDisplay:
    """Handles display of system status and health information."""

    def __init__(self, formatter: DisplayFormatter):
        self.formatter = formatter
        self.config = formatter.config

    def show_system_status(self, status: dict[str, Any]):
        """Display comprehensive system status."""
        if self.config.is_quiet():
            return

        self._print(self.formatter.header("🎯 AI Linting Fixer - System Status"))

        # Version and basic info
        version = status.get("version", "unknown")
        self._print(f"Version: {version}")

        # Components status
        components = status.get("components", {})
        self._print(self.formatter.section("Components Status", "config"))

        for component, available in components.items():
            emoji = "success" if available else "warning"
            status_text = "Available" if available else "Not Available"
            component_name = component.replace("_", " ").title()
            self._print(self.formatter.metric(component_name, status_text, emoji))

        # Agent statistics
        if self.config.is_verbose():
            agent_stats = status.get("agent_stats", {})
            if agent_stats:
                self._print(self.formatter.section("Agent Performance", "agent"))
                for agent_name, stats in agent_stats.items():
                    success_rate = stats.get("success_rate", 0) * 100
                    attempts = stats.get("attempts", 0)
                    successes = stats.get("successes", 0)
                    self._print(
                        self.formatter.metric(
                            agent_name, f"{successes}/{attempts} ({success_rate:.1f}%)", "agent"
                        )
                    )

    def show_provider_status(self, providers: list[str]):
        """Display LLM provider status."""
        if self.config.is_quiet():
            return

        self._print(self.formatter.section("AI Provider Status", "agent"))

        if providers:
            self._print(
                self.formatter.metric(f"{len(providers)} provider(s) available", "", "success")
            )
            for provider in providers:
                self._print(self.formatter.item(provider))
        else:
            self._print(
                self.formatter.metric(
                    "No providers available", "Configure API keys in environment", "warning"
                )
            )

    def show_feature_status(self, features: dict[str, bool]):
        """Display feature availability status."""
        if self.config.is_quiet():
            return

        self._print(self.formatter.header("🎯 AI Linting Fixer - Feature Status"))

        for feature, available in features.items():
            emoji = "success" if available else "error"
            status_text = "Available" if available else "Not Available"
            feature_name = feature.replace("_", " ").title()
            self._print(self.formatter.metric(feature_name, status_text, emoji))

        # Show installation suggestions for missing features
        missing_features = [name for name, available in features.items() if not available]
        if missing_features and not self.config.is_quiet():
            self._print(self.formatter.section("💡 To enable missing features", "suggestion"))

            suggestions = {
                "temporal_integration": "pip install temporalio",
                "celery_integration": "pip install celery redis",
                "prefect_integration": "pip install prefect",
                "redis_support": "pip install redis",
            }

            for feature in missing_features:
                if feature in suggestions:
                    self._print(self.formatter.item(f"{feature}: {suggestions[feature]}"))

    def _print(self, text: str):
        """Print to the configured output stream."""
        print(text, file=self.config.output_stream)


class OperationDisplay:
    """Handles display of operation progress and results."""

    def __init__(self, formatter: DisplayFormatter):
        self.formatter = formatter
        self.config = formatter.config

    def show_session_start(self, inputs: AILintingFixerInputs, session_id: str):
        """Display session start information."""
        if self.config.is_quiet():
            return

        self._print(self.formatter.header(f"🎯 AI Linting Fixer v2.0 - Session: {session_id[:8]}"))

        # Configuration summary
        self._print(self.formatter.section("Configuration", "config"))

        config_items = [
            ("Target", inputs.target_path),
            ("Max fixes", inputs.max_fixes),
            ("Specialized agents", "✅" if inputs.use_specialized_agents else "❌"),
            ("Safe operations", "✅" if inputs.create_backups else "❌"),
            ("Dry run", "✅" if inputs.dry_run else "❌"),
            ("Async processing", "✅" if inputs.enable_async else "❌"),
        ]

        for label, value in config_items:
            self._print(self.formatter.metric(label, value))

    def show_detection_progress(self, target_path: str):
        """Show issue detection progress."""
        if not self.config.is_quiet():
            self._print(
                f"\n{self.formatter.emoji('detection')}Detecting linting issues in: {target_path}"
            )

    def show_detection_results(
        self, filtered_count: int, total_count: int, unique_files_count: int | None = None
    ):
        """Display detection results."""
        if self.config.is_quiet():
            return

        if unique_files_count:
            pass

        if total_count != filtered_count:
            pass

    def show_backup_creation(self, unique_files_count: int):
        """Display backup creation progress."""
        if self.config.is_quiet():
            return

    def show_queueing_progress(self, issues_count: int):
        """Show issue queueing progress."""
        if not self.config.is_quiet():
            self._print(
                f"\n{self.formatter.emoji('queue')}Queueing {issues_count} issues for processing..."
            )

    def show_queueing_results(self, queued_count: int, total_count: int):
        """Show queueing results."""
        if not self.config.is_quiet():
            if queued_count == total_count:
                self._print(f"{self.formatter.emoji('success')}Queued {queued_count} issues")
            else:
                self._print(
                    f"{self.formatter.emoji('success')}Queued {queued_count} new issues (duplicates skipped)"
                )

    def show_processing_start(self, issue_count: int):
        """Show processing start."""
        if self.config.is_quiet():
            return
        self._print(f"\n🔄 Processing {issue_count} issues with AI agents...")

    def show_processing_progress(self, current: int, total: int, issue: "LintingIssue") -> None:
        """Show progress for processing individual issues."""
        if self.config.is_quiet():
            return

        (current / total) * 100
        filled_length = int(50 * current // total)
        "█" * filled_length + "░" * (50 - filled_length)

        # Clear previous line and show progress

        if current == total:
            pass  # Add newline when complete

    def show_processing_results(self, fixed: int, failed: int):
        """Show processing results."""
        if not self.config.is_quiet():
            self._print(
                f"{self.formatter.emoji('success')}Processing complete: {fixed} fixes, {failed} failures"
            )

    def show_dry_run_notice(self):
        """Show dry run notice."""
        if not self.config.is_quiet():
            self._print(
                f"{self.formatter.emoji('dry_run')}DRY RUN MODE - No actual changes were made"
            )

    def _print(self, text: str):
        """Print to the configured output stream."""
        print(text, file=self.config.output_stream)


class ResultsDisplay:
    """Handles display of final results and statistics."""

    def __init__(self, formatter: DisplayFormatter):
        self.formatter = formatter
        self.config = formatter.config

    def show_results_summary(self, outputs: "AILintingFixerOutputs"):
        """Show results summary."""
        if self.config.is_quiet():
            return

        if outputs.files_modified:
            for _file_path in outputs.files_modified:
                pass

    def show_agent_performance(self, agent_stats: dict[str, Any]):
        """Show detailed agent performance statistics."""
        if not self.config.is_verbose() or not agent_stats:
            return

        self._print(self.formatter.section("Agent Performance", "agent"))

        for agent_name, stats in agent_stats.items():
            attempts = stats.get("attempts", 0)
            successes = stats.get("successes", 0)
            success_rate = stats.get("success_rate", 0) * 100

            display_name = agent_name.replace("_", " ").title()
            self._print(
                self.formatter.metric(
                    display_name, f"{successes}/{attempts} ({success_rate:.1f}%)", "agent"
                )
            )

    def show_queue_statistics(self, queue_stats: dict[str, Any]):
        """Show database queue statistics."""
        if not self.config.is_verbose() or not queue_stats:
            return

        self._print(self.formatter.section("Queue Statistics", "database"))

        overall = queue_stats.get("overall", {})
        if overall:
            metrics = [
                ("Total issues", overall.get("total_issues", 0)),
                ("Completed", overall.get("completed", 0)),
                ("Failed", overall.get("failed", 0)),
                ("Success rate", f"{overall.get('success_rate', 0):.1f}%"),
            ]

            for label, value in metrics:
                self._print(self.formatter.metric(label, value, "database"))

    def show_suggestions(self, suggestions: list[str]):
        """Show suggestions."""
        if self.config.is_quiet() or not suggestions:
            return

        for _suggestion in suggestions:
            pass

    def _print(self, text: str):
        """Print to the configured output stream."""
        print(text, file=self.config.output_stream)


class ErrorDisplay:
    """Handles error and warning display with enhanced capabilities."""

    def __init__(self, formatter: DisplayFormatter):
        self.formatter = formatter
        self.config = formatter.config
        self._error_history: list[dict[str, Any]] = []

    def show_error(self, message: str, details: str | None = None):
        """Display an error message with optional details."""
        if self.config.is_quiet():
            return

        if details:
            pass

    def show_warning(self, message: str):
        """Display a warning message."""
        if self.config.is_quiet():
            return

    def show_info(self, message: str):
        """Display an info message."""
        if self.config.is_quiet():
            return

    def show_error_details(self, error_details: dict[str, Any]):
        """Display detailed error information for drill-down analysis."""
        if self.config.is_quiet():
            return

        # Show context information
        context = error_details.get("context", {})
        if context:
            components = context.get("components_initialized", {})
            if components:
                for _component, _status in components.items():
                    pass

        # Show validation details if available
        validation_details = error_details.get("validation_details", {})
        if validation_details:
            missing_fields = validation_details.get("missing_fields", [])
            if missing_fields:
                pass

        # Show connection details if available
        connection_details = error_details.get("connection_details", {})
        if connection_details:
            pass

        # Show permission details if available
        permission_details = error_details.get("permission_details", {})
        if permission_details:
            pass

        # Show stack trace in verbose mode
        if self.config.is_verbose() and error_details.get("stack_trace"):
            stack_trace = error_details["stack_trace"]
            # Limit stack trace length for readability
            if len(stack_trace) > 1000:
                stack_trace = stack_trace[:1000] + "\n... (truncated)"

    def show_suggested_actions(self, suggestions: list[str]):
        """Display suggested actions for error recovery."""
        if self.config.is_quiet() or not suggestions:
            return

        for _i, _suggestion in enumerate(suggestions, 1):
            pass

    def show_error_summary(self, error_counts: dict[str, int], total_errors: int = 0):
        """Display a summary of errors encountered."""
        if self.config.is_quiet():
            return

        if error_counts:
            for _error_type, _count in error_counts.items():
                pass

    def show_error_recovery_attempt(self, error_type: str, attempt: int, max_attempts: int):
        """Display information about error recovery attempts."""
        if self.config.is_quiet():
            return

    def show_error_recovery_success(self, error_type: str):
        """Display success message for error recovery."""
        if self.config.is_quiet():
            return

    def show_error_recovery_failure(self, error_type: str, final_message: str = ""):
        """Display failure message for error recovery."""
        if self.config.is_quiet():
            return

        if final_message:
            pass

    def get_error_history(self) -> list[dict[str, Any]]:
        """Get the history of errors encountered."""
        return self._error_history.copy()

    def clear_error_history(self):
        """Clear the error history."""
        self._error_history.clear()

    def export_error_history(self, file_path: str):
        """Export error history to a file."""
        import json

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.get_error_history(), f, indent=2)
        except Exception:
            pass

    def _format_error_details(self, details: str) -> str:
        """Format error details for better readability."""
        lines = details.split("\n")
        formatted_lines = []

        for line in lines:
            if line.strip():
                # Indent and format the line
                formatted_lines.append(f"     {line}")
            else:
                formatted_lines.append("")

        return "\n".join(formatted_lines)

    def _print(self, text: str):
        """Print to the configured output stream."""
        print(text, file=self.config.output_stream)

    def _print_error(self, text: str):
        """Print to the configured error stream."""
        print(text, file=self.config.error_stream)


class AILintingFixerDisplay:
    """Main display coordinator for AI Linting Fixer."""

    def __init__(self, config: DisplayConfig | None = None):
        """Initialize display with configuration."""
        self.config = config or DisplayConfig()
        self.formatter = DisplayFormatter(self.config)

        # Initialize specialized displays
        self.system = SystemStatusDisplay(self.formatter)
        self.operation = OperationDisplay(self.formatter)
        self.results = ResultsDisplay(self.formatter)
        self.error = ErrorDisplay(self.formatter)

    def configure(self, **kwargs):
        """Update display configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def set_quiet(self, quiet: bool = True):
        """Set quiet mode."""
        self.config.mode = OutputMode.QUIET if quiet else OutputMode.NORMAL

    def set_verbose(self, verbose: bool = True):
        """Set verbose mode."""
        self.config.mode = OutputMode.VERBOSE if verbose else OutputMode.NORMAL


# Global display instance
_default_display = None


def get_display(config: DisplayConfig | None = None) -> AILintingFixerDisplay:
    """Get or create the default display instance."""
    global _default_display

    if _default_display is None or config is not None:
        _default_display = AILintingFixerDisplay(config)

    return _default_display


# Convenience functions for backward compatibility
def display_provider_status(providers: list[str], quiet: bool = False):
    """Display LLM provider status (backward compatibility)."""
    display = get_display()
    display.set_quiet(quiet)
    display.system.show_provider_status(providers)


def print_feature_status(features: dict[str, bool]):
    """Print feature status (backward compatibility)."""
    display = get_display()
    display.system.show_feature_status(features)


def show_session_summary(
    outputs: AILintingFixerOutputs, verbose: bool = False, quiet: bool = False
):
    """Show complete session summary."""
    display = get_display()
    display.set_quiet(quiet)
    display.set_verbose(verbose)

    display.results.show_results_summary(outputs)
    display.results.show_agent_performance(outputs.agent_stats)
    display.results.show_queue_statistics(outputs.queue_stats)
    display.results.show_suggestions(outputs)
