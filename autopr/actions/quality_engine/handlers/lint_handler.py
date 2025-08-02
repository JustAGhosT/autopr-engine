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
            print("No lint issues found.")
            return

        print(f"Found {len(results)} lint issues:")

        for issue in results:
            print(
                f"[{issue['level'].upper()}] {issue['filename']}:{issue['line_number']}:{issue['column_number']} → {issue['message']}"
            )
