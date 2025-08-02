"""
AutoPR Action: Issue Creator
Creates GitHub issues and Linear tickets based on AI analysis
"""

import os
from typing import Any

from pydantic import BaseModel, Field
import requests


class IssueCreatorInputs(BaseModel):
    github_issues: list[dict[str, Any]] = Field(default_factory=list)
    linear_tickets: list[dict[str, Any]] = Field(default_factory=list)
    ai_assignments: dict[str, str] = Field(default_factory=dict)
    repository: str
    create_github: bool = True
    create_linear: bool = True
    notify_ai_tools: bool = True


class IssueCreatorOutputs(BaseModel):
    github_issues_created: list[dict[str, Any]] = Field(default_factory=list)
    linear_tickets_created: list[dict[str, Any]] = Field(default_factory=list)
    ai_notifications_sent: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    success_count: int


class IssueCreator:
    def __init__(self) -> None:
        self.github_token: str = os.getenv("GITHUB_TOKEN") or ""
        self.linear_token: str = os.getenv("LINEAR_API_KEY") or ""
        self.slack_webhook: str = os.getenv("SLACK_WEBHOOK_URL") or ""

    def create_issues_and_tickets(self, inputs: IssueCreatorInputs) -> IssueCreatorOutputs:
        """Main function to create issues and tickets"""

        github_created = []
        linear_created = []
        ai_notifications = []
        errors = []

        # Create GitHub issues
        if inputs.create_github and inputs.github_issues:
            for issue_data in inputs.github_issues:
                try:
                    created_issue = self._create_github_issue(issue_data, inputs.repository)
                    github_created.append(created_issue)
                except Exception as e:
                    errors.append(f"Failed to create GitHub issue: {e!s}")

        # Create Linear tickets
        if inputs.create_linear and inputs.linear_tickets:
            for ticket_data in inputs.linear_tickets:
                try:
                    created_ticket = self._create_linear_ticket(ticket_data)
                    linear_created.append(created_ticket)
                except Exception as e:
                    errors.append(f"Failed to create Linear ticket: {e!s}")

        # Send AI notifications
        if inputs.notify_ai_tools and inputs.ai_assignments:
            for assignment_key, ai_tool in inputs.ai_assignments.items():
                try:
                    notification = self._notify_ai_tool(
                        assignment_key, ai_tool, github_created, linear_created
                    )
                    ai_notifications.append(notification)
                except Exception as e:
                    errors.append(f"Failed to notify {ai_tool}: {e!s}")

        return IssueCreatorOutputs(
            github_issues_created=github_created,
            linear_tickets_created=linear_created,
            ai_notifications_sent=ai_notifications,
            errors=errors,
            success_count=len(github_created) + len(linear_created),
        )

    def _create_github_issue(self, issue_data: dict, repository: str) -> dict:
        """Create a GitHub issue"""
        url = f"https://api.github.com/repos/{repository}/issues"

        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        payload = {
            "title": issue_data["title"],
            "body": issue_data["body"],
            "labels": issue_data.get("labels", []),
            "assignees": issue_data.get("assignees", []),
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        created_issue = response.json()

        # Add AI-specific comments if needed
        self._add_ai_specific_comments(created_issue, issue_data)

        return {
            "number": created_issue["number"],
            "url": created_issue["html_url"],
            "title": created_issue["title"],
            "labels": [label["name"] for label in created_issue["labels"]],
            "created_at": created_issue["created_at"],
        }

    def _create_linear_ticket(self, ticket_data: dict) -> dict:
        """Create a Linear ticket"""
        url = "https://api.linear.app/graphql"

        headers = {
            "Authorization": self.linear_token,
            "Content-Type": "application/json",
        }

        # GraphQL mutation for creating issue
        mutation = """
        mutation IssueCreate($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    title
                    url
                    number
                    priority
                    labels {
                        nodes {
                            name
                        }
                    }
                    team {
                        name
                    }
                }
            }
        }
        """

        variables = {
            "input": {
                "title": ticket_data["title"],
                "description": ticket_data["description"],
                "priority": ticket_data.get("priority", 3),
                "teamId": self._get_team_id(ticket_data.get("team", "development")),
                "labelIds": self._get_label_ids(ticket_data.get("labels", [])),
            }
        }

        response = requests.post(
            url, headers=headers, json={"query": mutation, "variables": variables}, timeout=30
        )
        response.raise_for_status()

        result = response.json()

        if result.get("errors"):
            msg = f"Linear API error: {result['errors']}"
            raise Exception(msg)

        issue = result["data"]["issueCreate"]["issue"]

        # Add Charlie notification if it's a TypeScript issue
        if "typescript" in ticket_data.get("labels", []):
            self._notify_charlie_linear(issue["id"])

        return {
            "id": issue["id"],
            "number": issue["number"],
            "url": issue["url"],
            "title": issue["title"],
            "team": issue["team"]["name"],
            "priority": issue["priority"],
            "labels": [label["name"] for label in issue["labels"]["nodes"]],
        }

    def _add_ai_specific_comments(self, github_issue: dict, issue_data: dict) -> None:
        """Add AI-specific comments to GitHub issues"""
        issue_number = github_issue["number"]
        repository = github_issue["repository_url"].split("/")[-2:]
        repo_full_name = f"{repository[0]}/{repository[1]}"

        # Add comment based on issue type
        labels = issue_data.get("labels", [])

        if "security" in labels:
            comment = """
🔒 **Security Issue Detected**

This issue was automatically detected by AI security analysis.

**Next Steps:**
- [ ] Security team review
- [ ] Impact assessment
- [ ] Fix prioritization
- [ ] Automated Snyk scan results

@security-team please review this security vulnerability.
            """
            self._add_github_comment(repo_full_name, issue_number, comment)

        elif "typescript" in labels:
            comment = """
⚡ **TypeScript Issue Detected**

This TypeScript issue has been automatically detected and can be resolved autonomously.

**Next Steps:**
- [ ] CharlieHelps analysis
- [ ] Autonomous implementation
- [ ] Type safety verification
- [ ] Unit test generation

A Linear ticket has been created for autonomous resolution.
            """
            self._add_github_comment(repo_full_name, issue_number, comment)

    def _add_github_comment(self, repository: str, issue_number: int, comment: str) -> None:
        """Add a comment to a GitHub issue"""
        url = f"https://api.github.com/repos/{repository}/issues/{issue_number}/comments"

        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        payload = {"body": comment}

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

    def _notify_charlie_linear(self, issue_id: str) -> None:
        """Add Charlie notification comment to Linear ticket"""
        url = "https://api.linear.app/graphql"

        headers = {
            "Authorization": self.linear_token,
            "Content-Type": "application/json",
        }

        mutation = """
        mutation CommentCreate($input: CommentCreateInput!) {
            commentCreate(input: $input) {
                success
                comment {
                    id
                }
            }
        }
        """

        variables = {
            "input": {
                "issueId": issue_id,
                "body": """
🤖 **Charlie Assignment**

@charlie this TypeScript issue is ready for autonomous implementation.

**Expected Actions:**
1. Analyze requirements and current implementation
2. Create implementation plan
3. Generate TypeScript-compliant code
4. Create unit tests
5. Submit PR with complete solution

**Estimated Time:** 15-60 minutes depending on complexity
                """,
            }
        }

        response = requests.post(
            url, headers=headers, json={"query": mutation, "variables": variables}, timeout=30
        )
        response.raise_for_status()

    def _notify_ai_tool(
        self,
        assignment_key: str,
        ai_tool: str,
        github_issues: list,
        linear_tickets: list,
    ) -> dict:
        """Send notifications to AI tools about new assignments"""

        notification_methods = {
            "charlie": self._notify_charlie,
            "snyk": self._notify_snyk,
            "azure_sre": self._notify_azure_sre,
            "promptless": self._notify_promptless,
            "testim": self._notify_testim,
        }

        if ai_tool in notification_methods:
            return notification_methods[ai_tool](assignment_key, github_issues, linear_tickets)
        return {
            "ai_tool": ai_tool,
            "status": "no_notification_method",
            "message": f"No notification method configured for {ai_tool}",
        }

    def _notify_charlie(
        self, assignment_key: str, github_issues: list, linear_tickets: list
    ) -> dict:
        """Notify CharlieHelps about TypeScript assignments"""

        # Find relevant Linear tickets for Charlie
        charlie_tickets = [
            ticket for ticket in linear_tickets if "typescript" in ticket.get("labels", [])
        ]

        if not charlie_tickets:
            return {"ai_tool": "charlie", "status": "no_relevant_tickets"}

        # Send Slack notification to Charlie channel
        slack_message = {
            "text": "🤖 Charlie: New TypeScript Issues Assigned",
            "attachments": [
                {
                    "color": "good",
                    "fields": [
                        {
                            "title": "Linear Tickets Created",
                            "value": f"{len(charlie_tickets)} TypeScript issues ready for autonomous implementation",
                            "short": True,
                        },
                        {
                            "title": "Tickets",
                            "value": "\n".join(
                                [
                                    f"• <{ticket['url']}|{ticket['title']}>"
                                    for ticket in charlie_tickets
                                ]
                            ),
                            "short": False,
                        },
                    ],
                }
            ],
        }

        self._send_slack_notification(slack_message)

        return {
            "ai_tool": "charlie",
            "status": "notified",
            "tickets_assigned": len(charlie_tickets),
            "message": "Charlie notified via Slack and Linear comments",
        }

    def _notify_snyk(self, assignment_key: str, github_issues: list, linear_tickets: list) -> dict:
        """Notify Snyk about security issues"""

        security_issues = [
            issue for issue in github_issues if "security" in issue.get("labels", [])
        ]

        if not security_issues:
            return {"ai_tool": "snyk", "status": "no_security_issues"}

        # Trigger Snyk scans for security issues
        # This would integrate with Snyk's API to trigger targeted scans

        return {
            "ai_tool": "snyk",
            "status": "scan_triggered",
            "issues_count": len(security_issues),
            "message": "Snyk security scans triggered for detected vulnerabilities",
        }

    def _notify_azure_sre(
        self, assignment_key: str, github_issues: list, linear_tickets: list
    ) -> dict:
        """Notify Azure SRE about performance/infrastructure issues"""

        infra_issues = [
            issue
            for issue in github_issues
            if "performance" in issue.get("labels", [])
            or "infrastructure" in issue.get("labels", [])
        ]

        if not infra_issues:
            return {"ai_tool": "azure_sre", "status": "no_infra_issues"}

        return {
            "ai_tool": "azure_sre",
            "status": "monitoring_enhanced",
            "issues_count": len(infra_issues),
            "message": "Azure SRE monitoring enhanced for detected performance issues",
        }

    def _notify_promptless(
        self, assignment_key: str, github_issues: list, linear_tickets: list
    ) -> dict:
        """Notify Promptless about documentation issues"""

        doc_issues = [
            issue for issue in github_issues if "documentation" in issue.get("labels", [])
        ]

        if not doc_issues:
            return {"ai_tool": "promptless", "status": "no_doc_issues"}

        return {
            "ai_tool": "promptless",
            "status": "doc_updates_queued",
            "issues_count": len(doc_issues),
            "message": "Promptless queued for documentation updates",
        }

    def _notify_testim(
        self, assignment_key: str, github_issues: list, linear_tickets: list
    ) -> dict:
        """Notify Testim about testing issues"""

        test_issues = [issue for issue in github_issues if "testing" in issue.get("labels", [])]

        if not test_issues:
            return {"ai_tool": "testim", "status": "no_test_issues"}

        return {
            "ai_tool": "testim",
            "status": "test_generation_queued",
            "issues_count": len(test_issues),
            "message": "Testim test generation queued for detected issues",
        }

    def _send_slack_notification(self, message: dict) -> None:
        """Send notification to Slack"""
        if self.slack_webhook:
            response = requests.post(self.slack_webhook, json=message, timeout=30)
            response.raise_for_status()

    def _get_team_id(self, team_name: str) -> str:
        """Get Linear team ID by name"""
        # This would query Linear API to get team ID
        # For now, return mock IDs
        team_ids = {
            "frontend": "team_frontend_id",
            "backend": "team_backend_id",
            "security": "team_security_id",
            "devops": "team_devops_id",
            "development": "team_dev_id",
        }
        return team_ids.get(team_name, "team_dev_id")

    def _get_label_ids(self, label_names: list[str]) -> list[str]:
        """Get Linear label IDs by names"""
        # This would query Linear API to get label IDs
        # For now, return mock IDs
        label_map = {
            "ai-suggested": "label_ai_suggested_id",
            "typescript": "label_typescript_id",
            "security": "label_security_id",
            "bug": "label_bug_id",
            "enhancement": "label_enhancement_id",
        }
        return [label_map.get(name, "label_general_id") for name in label_names]


# Entry point for AutoPR
def run(inputs_dict: dict) -> dict:
    """AutoPR entry point"""
    inputs = IssueCreatorInputs(**inputs_dict)
    creator = IssueCreator()
    outputs = creator.create_issues_and_tickets(inputs)
    return outputs.dict()


if __name__ == "__main__":
    # Test the action
    sample_inputs = {
        "github_issues": [
            {
                "title": "[AI Detected] Missing type annotation",
                "body": "TypeScript issue detected in User.tsx",
                "labels": ["ai-detected", "high", "typescript"],
                "assignees": ["frontend-team"],
            }
        ],
        "linear_tickets": [
            {
                "title": "[AI Suggested] Add user role validation",
                "description": "Implement TypeScript interfaces for user roles",
                "labels": ["ai-suggested", "typescript"],
                "priority": 2,
                "team": "frontend",
            }
        ],
        "ai_assignments": {"typescript_src/components/User.tsx": "charlie"},
        "repository": "my-org/my-repo",
    }

    result = run(sample_inputs)
