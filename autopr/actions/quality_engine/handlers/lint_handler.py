from ..handler_base import Handler
from .lint_issue import LintIssue


class LintHandler(Handler[LintIssue]):
    def handle(self, results: list[LintIssue]) -> None:
        """
        Process and display lint issues.

        Args:
            results: The list of lint issues.
        """
        if not results:
            return


        for _issue in results:
            pass
