from ..registry import HandlerRegistry
from ..results import LintIssue

registry = HandlerRegistry()


@registry.register(LintIssue)
def handle_lint(results: list[LintIssue]):
    """
    Handle lint issues.

    Args:
        results: The lint issues to process.
    """
    print("Processing lint issues:")
    for issue in results:
        print(
            f"[{issue['level'].upper()}] {issue['filename']}:{issue['line_number']} → {issue['message']}"
        )
