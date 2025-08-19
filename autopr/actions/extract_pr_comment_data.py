"""
AutoPR Action: Extract PR Comment Data
Extracts structured data from PR comment events for processing.
"""

import json
import os

from pydantic import BaseModel


class ExtractPRCommentDataInputs(BaseModel):
    comment_id: int
    pr_number: int


class ExtractPRCommentDataOutputs(BaseModel):
    comment_body: str
    comment_author: str
    repo_owner: str
    repo_name: str
    branch_name: str
    file_path: str | None = None
    line_number: int | None = None
    comment_url: str
    pr_url: str


def extract_pr_comment_data(
    inputs: ExtractPRCommentDataInputs,
) -> ExtractPRCommentDataOutputs:
    """
    Extracts and structures PR comment data from GitHub event context.

    This action reads the GitHub event payload and extracts relevant
    information about the PR comment for further processing.
    """

    # Read GitHub event payload
    github_event_path = os.getenv("GITHUB_EVENT_PATH", "")
    if not github_event_path:
        msg = "No GitHub event payload found"
        raise ValueError(msg)

    with open(github_event_path, encoding="utf-8") as f:
        event_data = json.load(f)

    # Extract comment data
    comment = event_data.get("comment", {})
    pr = event_data.get("pull_request", {})
    repository = event_data.get("repository", {})

    # Handle both regular comments and review comments
    if "pull_request" in comment:
        # Review comment
        file_path = comment.get("path")
        line_number = comment.get("line")
    else:
        # Regular PR comment
        file_path = None
        line_number = None

    return ExtractPRCommentDataOutputs(
        comment_body=comment.get("body", ""),
        comment_author=comment.get("user", {}).get("login", ""),
        repo_owner=repository.get("owner", {}).get("login", ""),
        repo_name=repository.get("name", ""),
        branch_name=pr.get("head", {}).get("ref", ""),
        file_path=file_path,
        line_number=line_number,
        comment_url=comment.get("html_url", ""),
        pr_url=pr.get("html_url", ""),
    )
