"""
AutoPR Action: Handle PR Comments
Processes PR comments, attempts to fix issues, and creates GitHub issues for complex problems.
"""

import re
from typing import Any

from pydantic import BaseModel

from autopr.actions.base import Action


class HandlePRCommentInputs(BaseModel):
    comment_body: str
    comment_author: str
    pr_number: int
    comment_id: int
    repo_owner: str
    repo_name: str
    branch_name: str
    file_path: str | None = None
    line_number: int | None = None


class HandlePRCommentOutputs(BaseModel):
    action_taken: str
    fix_applied: bool
    issue_created: bool
    issue_number: int | None = None
    response_message: str


def handle_pr_comment(inputs: HandlePRCommentInputs) -> HandlePRCommentOutputs:
    """
    Processes PR comments and attempts to fix issues or create GitHub issues.

    Workflow:
    1. React to comment with 👀 to indicate pickup
    2. Analyze comment for actionable feedback
    3. Attempt simple fixes (typos, formatting, etc.)
    4. For complex issues, create GitHub issue
    5. Mark comment as resolved if fix applied
    """

    comment = inputs.comment_body.lower()

    # React to comment to show we picked it up
    react_to_comment(inputs.repo_owner, inputs.repo_name, inputs.comment_id, "eyes")

    # Analyze comment type
    if is_simple_fix(comment):
        # Attempt to apply simple fix
        fix_result = attempt_simple_fix(inputs)
        if fix_result["success"]:
            # Mark comment as resolved
            resolve_comment(inputs.repo_owner, inputs.repo_name, inputs.comment_id)
            return HandlePRCommentOutputs(
                action_taken="simple_fix",
                fix_applied=True,
                issue_created=False,
                response_message=f"Applied fix: {fix_result['description']}",
            )

    # For complex issues, create GitHub issue
    if is_complex_issue(comment):
        issue_number = create_github_issue(inputs)
        # React with 📝 to indicate issue created
        react_to_comment(inputs.repo_owner, inputs.repo_name, inputs.comment_id, "memo")

        return HandlePRCommentOutputs(
            action_taken="issue_created",
            fix_applied=False,
            issue_created=True,
            issue_number=issue_number,
            response_message=f"Created issue #{issue_number} to track this feedback",
        )

    # Default: acknowledge but no action
    react_to_comment(inputs.repo_owner, inputs.repo_name, inputs.comment_id, "thumbsup")
    return HandlePRCommentOutputs(
        action_taken="acknowledged",
        fix_applied=False,
        issue_created=False,
        response_message="Comment acknowledged but no automated action taken",
    )


def is_simple_fix(comment: str) -> bool:
    """Check if comment describes a simple fix we can automate."""
    simple_patterns = [
        r"typo|spelling|misspell",
        r"missing\s+(semicolon|comma|period)",
        r"format|formatting|indent",
        r"trailing\s+space",
        r"add\s+newline",
        r"remove\s+console\.log",
        r"unused\s+import",
    ]
    return any(re.search(pattern, comment) for pattern in simple_patterns)


def is_complex_issue(comment: str) -> bool:
    """Check if comment describes a complex issue that needs tracking."""
    complex_patterns = [
        r"refactor|redesign|architecture",
        r"performance|optimization|slow",
        r"security|vulnerability|exposed",
        r"accessibility|a11y",
        r"bug|error|crash|fail",
        r"feature\s+request|enhancement",
        r"documentation|docs|readme",
    ]
    return any(re.search(pattern, comment) for pattern in complex_patterns)


def attempt_simple_fix(inputs: HandlePRCommentInputs) -> dict[str, Any]:
    """Attempt to apply simple fixes based on comment content."""
    comment = inputs.comment_body.lower()

    # Example fixes (extend as needed)
    if "remove console.log" in comment and inputs.file_path:
        return remove_console_logs(inputs.file_path)
    if "trailing space" in comment and inputs.file_path:
        return fix_trailing_spaces(inputs.file_path)
    if "unused import" in comment and inputs.file_path:
        return remove_unused_imports(inputs.file_path)

    return {"success": False, "description": "No automated fix available"}


def remove_console_logs(file_path: str) -> dict[str, Any]:
    """Remove console.log statements from file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Remove console.log lines
        lines = content.split("\n")
        filtered_lines = [line for line in lines if "console.log" not in line]

        if len(filtered_lines) < len(lines):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(filtered_lines))
            return {
                "success": True,
                "description": f"Removed {len(lines) - len(filtered_lines)} console.log statements",
            }
    except Exception as e:
        return {"success": False, "description": f"Error: {e!s}"}

    return {"success": False, "description": "No console.log statements found"}


def fix_trailing_spaces(file_path: str) -> dict[str, Any]:
    """Remove trailing spaces from file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")
        cleaned_lines = [line.rstrip() for line in lines]

        if any(line != cleaned for line, cleaned in zip(lines, cleaned_lines, strict=False)):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(cleaned_lines))
            return {"success": True, "description": "Removed trailing whitespace"}
    except Exception as e:
        return {"success": False, "description": f"Error: {e!s}"}

    return {"success": False, "description": "No trailing spaces found"}


def remove_unused_imports(file_path: str) -> dict[str, Any]:
    """Remove unused imports (basic implementation)."""
    # This would require more sophisticated AST parsing
    # For now, return not implemented
    return {
        "success": False,
        "description": "Unused import removal not yet implemented",
    }


def create_github_issue(inputs: HandlePRCommentInputs) -> int:
    """Create a GitHub issue from PR comment."""
    import subprocess

    # Extract issue title and body from comment
    title = f"Feedback from PR #{inputs.pr_number}"
    if inputs.file_path:
        title += f" - {inputs.file_path}"

    body = f"""
**Original comment by @{inputs.comment_author}:**

{inputs.comment_body}

---

**Context:**
- PR: #{inputs.pr_number}
- Branch: {inputs.branch_name}
- File: {inputs.file_path or "N/A"}
- Line: {inputs.line_number or "N/A"}

**Generated automatically by AutoPR**
"""

    # Create issue using GitHub CLI
    cmd = [
        "gh",
        "issue",
        "create",
        "--title",
        title,
        "--body",
        body,
        "--repo",
        f"{inputs.repo_owner}/{inputs.repo_name}",
        "--label",
        "autopr-generated,from-pr-comment",
    ]

    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode == 0:
        # Extract issue number from output
        issue_url = result.stdout.strip()
        return int(issue_url.split("/")[-1])

    return 0  # Failed to create issue


def react_to_comment(repo_owner: str, repo_name: str, comment_id: int, reaction: str) -> None:
    """Add reaction to PR comment."""
    import subprocess

    cmd = [
        "gh",
        "api",
        f"/repos/{repo_owner}/{repo_name}/issues/comments/{comment_id}/reactions",
        "--method",
        "POST",
        "--field",
        f"content={reaction}",
    ]

    subprocess.run(cmd, check=False, capture_output=True)


def resolve_comment(repo_owner: str, repo_name: str, comment_id: int) -> None:
    """Mark comment as resolved (if part of a review)."""
    # Note: This would require GitHub API to resolve review comments
    # Implementation depends on whether it's a regular comment or review comment


def git_commit_and_push(branch_name: str, message: str) -> None:
    """Commit changes and push to branch."""
    import subprocess

    # Stage all changes
    subprocess.run(["git", "add", "."], check=False)

    # Commit with message
    subprocess.run(["git", "commit", "-m", message], check=False)

    # Push to branch
    subprocess.run(["git", "push", "origin", branch_name], check=False)


class PRCommentHandler(Action[HandlePRCommentInputs, HandlePRCommentOutputs]):
    """Action for handling PR comments."""

    def __init__(self) -> None:
        super().__init__(
            name="pr_comment_handler",
            description="Processes PR comments, attempts to fix issues, and creates GitHub issues for complex problems",
            version="1.0.0",
        )

    async def execute(
        self, inputs: HandlePRCommentInputs, context: dict[str, Any]
    ) -> HandlePRCommentOutputs:
        """Execute the PR comment handling."""
        return handle_pr_comment(inputs)
