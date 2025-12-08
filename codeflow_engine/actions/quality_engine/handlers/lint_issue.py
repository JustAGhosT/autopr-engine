from typing import TypedDict


class LintIssue(TypedDict):
    filename: str
    line_number: int
    column_number: int
    message: str
    code: str
    level: str
