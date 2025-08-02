#!/usr/bin/env python3
"""
Example: Using the Enhanced Error Handler with AI Linting Fixer

This example demonstrates how to integrate the new error handler system
with the AI linting fixer for comprehensive error tracking and display.
"""

import sys
from pathlib import Path
from typing import Any

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from autopr.actions.ai_linting_fixer import (
    AILintingFixer,
    AILintingFixerInputs,
    DisplayConfig,
    ErrorHandler,
    OutputMode,
    create_error_context,
)
from autopr.actions.llm.manager import LLMProviderManager


def setup_error_handler() -> None:
    """Set up the error handler with custom configuration."""
    # Create display configuration
    display_config = DisplayConfig(mode=OutputMode.VERBOSE, use_colors=True, use_emojis=True)

    # Initialize error handler
    error_handler = ErrorHandler(display_config)

    # Register custom error callbacks
    def on_error_callback(error_info: Any) -> None:
        """Custom callback for when errors occur."""

    def on_recovery_callback(error_info: Any, strategy: Any) -> None:
        """Custom callback for recovery attempts."""

    error_handler.register_error_callback(on_error_callback)
    error_handler.register_recovery_callback(on_recovery_callback)

    return error_handler


def demonstrate_error_handler_integration() -> None:
    """Demonstrate how to integrate error handler with AI linting fixer."""

    # Set up error handler
    error_handler = setup_error_handler()

    # Initialize LLM manager
    llm_manager = LLMProviderManager()

    # Initialize AI linting fixer with error handler
    fixer = AILintingFixer(llm_manager=llm_manager, max_workers=2)

    # Create test inputs
    inputs = AILintingFixerInputs(
        target_path="test_lint_issues.py",
        fix_types=["E501", "F401", "F841", "E722"],
        max_fixes_per_run=5,
        provider="openai",  # or your preferred provider
        model="gpt-4",
    )

    try:
        # Run flake8 to detect issues
        issues = fixer.run_flake8(inputs.target_path)

        if not issues:
            return

        # Display issues found
        for _i, _issue in enumerate(issues[:5], 1):  # Show first 5 issues
            pass

        # Attempt to fix issues with error handling

        # Wrap the fixing process with error handling
        try:
            result = fixer.fix_issues_with_ai(
                issues=issues,
                max_fixes=inputs.max_fixes_per_run,
                provider=inputs.provider,
                model=inputs.model,
            )

            # Display results

            if result.error_message:
                pass

        except Exception as e:
            # Log the error with context
            context = create_error_context(
                file_path=inputs.target_path,
                function_name="fix_issues_with_ai",
                workflow_step="ai_fixing",
                provider=inputs.provider,
                model=inputs.model,
            )

            error_info = error_handler.log_error(e, context)

            # Attempt recovery if possible
            if error_handler.attempt_recovery(error_info):
                pass
                # You could implement retry logic here

        # Show error summary
        summary = error_handler.get_error_summary()

        if summary["error_counts_by_category"]:
            for _category, _count in summary["error_counts_by_category"].items():
                pass

        # Export error report
        error_report_path = "ai_linting_error_report.json"
        error_handler.export_errors(error_report_path)

    except Exception as e:
        # Handle any unexpected errors
        context = create_error_context(
            file_path=inputs.target_path,
            function_name="demonstrate_error_handler_integration",
            workflow_step="main_execution",
        )
        error_handler.log_error(e, context)

    finally:
        # Clean up
        fixer.close()


def demonstrate_error_categories():
    """Demonstrate different error categories and their handling."""

    error_handler = setup_error_handler()

    # Test different error types
    error_tests = [
        {
            "name": "File Not Found",
            "exception": FileNotFoundError("test_file.py not found"),
            "context": create_error_context(file_path="test_file.py", workflow_step="file_reading"),
        },
        {
            "name": "Permission Error",
            "exception": PermissionError("Access denied to /root/file.txt"),
            "context": create_error_context(
                file_path="/root/file.txt", workflow_step="file_writing"
            ),
        },
        {
            "name": "API Timeout",
            "exception": TimeoutError("API request timed out after 30 seconds"),
            "context": create_error_context(workflow_step="api_request", provider="openai"),
        },
        {
            "name": "Syntax Error",
            "exception": SyntaxError("invalid syntax"),
            "context": create_error_context(file_path="test.py", workflow_step="code_parsing"),
        },
        {
            "name": "AI Confidence Low",
            "exception": ValueError("AI confidence is too low for automatic fix"),
            "context": create_error_context(workflow_step="ai_processing", confidence=0.3),
        },
    ]

    for test in error_tests:
        try:
            raise test["exception"]
        except Exception as e:
            error_info = error_handler.log_error(e, test["context"], display=False)

            # Test recovery strategy
            error_handler.get_recovery_strategy(error_info)

    # Show final summary
    error_handler.get_error_summary()


if __name__ == "__main__":
    # Check if we're in the right directory
    if not Path("test_lint_issues.py").exists():
        sys.exit(1)

    # Run demonstrations
    demonstrate_error_categories()
    demonstrate_error_handler_integration()
