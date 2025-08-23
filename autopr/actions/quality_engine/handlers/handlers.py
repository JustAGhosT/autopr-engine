from autopr.actions.quality_engine.handler_registry import HandlerRegistry
from autopr.actions.quality_engine.handler_base import Handler
from autopr.actions.quality_engine.handlers.lint_issue import LintIssue


registry = HandlerRegistry()


@registry.register_for_result(LintIssue)
class LintIssueHandler(Handler[LintIssue]):
    """
    Handler for lint issues.
    """

    def handle(self, results: list[LintIssue]) -> None:
        """
        Handle lint issues.

        Args:
            results: The lint issues to process.
        """
        for _issue in results:
            pass
