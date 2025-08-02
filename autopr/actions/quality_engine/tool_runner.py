"""
Tool runner for quality engine - handles running tools and processing results
"""

import time
from typing import Any

import structlog

from .models import ToolResult
from .tools.tool_base import ToolExecutionResult

logger = structlog.get_logger(__name__)


async def run_tool(
    tool_name: str,
    tool_instance: Any,
    files: list[str],
    tool_config: dict[str, Any],
    handler_registry: Any | None = None,
) -> ToolResult | None:
    """Run a quality tool with enhanced timeout and error handling."""
    try:
        logger.info("Running tool", tool=tool_name, file_count=len(files))

        # Use the enhanced run_with_timeout method if available
        if hasattr(tool_instance, "run_with_timeout"):
            result: ToolExecutionResult = await tool_instance.run_with_timeout(files, tool_config)

            # Extract issues and handle errors
            issues = result["issues"]
            execution_time = result["execution_time"]
            error_message = result["error_message"]
            warnings = result["warnings"]
            output_summary = result["output_summary"]

            # Log warnings if any
            if warnings:
                for warning in warnings:
                    logger.warning(f"Tool {tool_name} warning: {warning}")

            # Log error if any
            if error_message:
                logger.error(f"Tool {tool_name} error: {error_message}")

            # Log completion with summary
            logger.info(
                "Tool completed",
                tool=tool_name,
                issues_found=len(issues),
                execution_time=f"{execution_time:.2f}s",
                success=result["success"],
                summary=output_summary,
            )

        else:
            # Fallback to old method for backward compatibility
            start_time = time.time()
            results = await tool_instance.run(files=files, config=tool_config)
            execution_time = time.time() - start_time

            # Handle different result types
            if isinstance(results, list):
                issues = results
                files_with_issues = list(
                    set(
                        issue.get("filename", "")
                        for issue in issues
                        if isinstance(issue, dict) and issue.get("filename")
                    )
                )
            elif isinstance(results, dict):
                issues = results.get("issues", [])
                files_with_issues = results.get("files_with_issues", [])
            else:
                issues = []
                files_with_issues = []

            logger.info(
                "Tool completed (legacy mode)",
                tool=tool_name,
                issues_found=len(issues),
                execution_time=f"{execution_time:.2f}s",
            )

        # If we have a handler registry, process the results with the appropriate handler
        if handler_registry is not None and hasattr(tool_instance, "result_type"):
            result_type = tool_instance.result_type
            try:
                handler_registry.handle_results(issues, result_type)
            except Exception as handler_error:
                logger.warning(
                    "Error handling tool results", tool=tool_name, error=str(handler_error)
                )

        # Extract files with issues for the result
        files_with_issues = list(
            set(
                issue.get("filename", "")
                for issue in issues
                if isinstance(issue, dict) and issue.get("filename")
            )
        )

        return ToolResult(
            issues=issues,
            files_with_issues=files_with_issues,
            summary=(
                output_summary
                if "output_summary" in locals()
                else f"Completed {tool_name} analysis"
            ),
            execution_time=execution_time,
        )

    except Exception as e:
        logger.error("Error running tool", tool=tool_name, error=str(e))
        return None


def determine_smart_tools(files: list[str]) -> list[str]:
    """Select tools dynamically based on file context."""
    tools = set()

    for file in files:
        if file.endswith(".py"):
            # Python files get standard Python tools
            tools.update(["ruff", "mypy", "bandit", "pytest"])

            # Add documentation checking for Python files
            tools.add("interrogate")

            # Add complexity analysis for Python files
            tools.add("radon")

        elif file.endswith((".js", ".ts", ".jsx", ".tsx")):
            # JavaScript/TypeScript files would get JS-specific tools
            # These would be added as plugins
            pass

        elif file.endswith((".yml", ".yaml")):
            # YAML files might need specific validation
            pass

        elif file.endswith((".json", ".jsonc")):
            # JSON files might need validation
            pass

    # Always include cross-platform security tools
    tools.add("semgrep")

    # Add dependency scanning for any project
    tools.add("dependency_scanner")

    return list(tools)


def get_tool_performance_info(tool_instance: Any) -> dict[str, Any]:
    """Get performance information for a tool."""
    if hasattr(tool_instance, "get_performance_metrics"):
        return tool_instance.get_performance_metrics()

    return {
        "recommended_timeout": 60.0,
        "recommended_max_files": 100,
        "category": getattr(tool_instance, "category", "general"),
        "description": getattr(tool_instance, "description", "Unknown tool"),
    }


def validate_tool_config(tool_instance: Any, config: dict[str, Any]) -> list[str]:
    """Validate tool configuration."""
    if hasattr(tool_instance, "validate_config"):
        return tool_instance.validate_config(config)

    return []  # No validation errors if tool doesn't implement validation
