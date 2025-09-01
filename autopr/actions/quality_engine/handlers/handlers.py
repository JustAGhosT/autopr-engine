import logging

from autopr.actions.quality_engine.handler_base import Handler
from autopr.actions.quality_engine.handler_registry import register_for_result
from autopr.actions.quality_engine.handlers.lint_issue import LintIssue


logger = logging.getLogger(__name__)


@register_for_result(LintIssue)
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
        for issue in results:
            logger.warning(
                "Lint issue: %s:%d:%d [%s] %s (%s)",
                issue["filename"],
                issue["line_number"],
                issue["column_number"],
                issue["code"],
                issue["message"],
                issue["level"]
            )
