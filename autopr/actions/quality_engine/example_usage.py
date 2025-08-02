"""
Example usage of the Quality Engine with dependency injection.
"""

import asyncio

from .engine import create_quality_engine
from .handlers.lint_issue import LintIssue


async def run_quality_analysis(files: list[str]) -> None:
    """
    Run quality analysis on files.

    Args:
        files: List of files to analyze
    """
    # Create an engine instance with DI
    engine = create_quality_engine()

    # Run MyPy tool
    mypy_config = {"args": ["--strict"]}
    await engine.run_and_handle(
        tool_name="mypy", files=files, config=mypy_config, result_type=LintIssue
    )

    # Run ESLint tool for JavaScript files
    js_files = [f for f in files if f.endswith((".js", ".jsx", ".ts", ".tsx"))]
    if js_files:
        eslint_config = {
            "extensions": [".js", ".jsx", ".ts", ".tsx"],
            "config": ".eslintrc.js",
            "fix": False,
        }
        await engine.run_and_handle(
            tool_name="eslint", files=js_files, config=eslint_config, result_type=LintIssue
        )

    # Run all linting tools
    linting_configs = {
        "mypy": {"args": ["--strict"]},
        "eslint": {"extensions": [".js", ".jsx", ".ts", ".tsx"]},
        "ruff": {"select": ["E", "F", "B"]},
    }

    result_types = {
        "mypy": LintIssue,
        "eslint": LintIssue,
        "ruff": LintIssue,
    }

    all_results = await engine.run_category(
        category="linting", files=files, configs=linting_configs, result_types=result_types
    )

    # Summarize results
    print("\nLinting summary:")
    for tool_name, results in all_results.items():
        print(f"{tool_name}: {len(results)} issues")


if __name__ == "__main__":
    # Example files
    python_files = [
        "autopr/actions/quality_engine/engine.py",
        "autopr/actions/quality_engine/handler_registry.py",
    ]

    # Run analysis
    asyncio.run(run_quality_analysis(python_files))
