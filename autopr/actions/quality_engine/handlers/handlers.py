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
    for _issue in results:
        pass
