from typing import TypedDict

from codeflow_engine.actions.quality_engine.handlers.lint_issue import LintIssue


class LintResult(TypedDict):
    issues: list[LintIssue]
