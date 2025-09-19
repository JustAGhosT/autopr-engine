from typing import TypedDict

from autopr.actions.quality_engine.handlers.lint_issue import LintIssue


class LintResult(TypedDict):
    issues: list[LintIssue]
