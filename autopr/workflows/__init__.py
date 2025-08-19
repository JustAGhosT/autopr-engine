"""
AutoPR Engine Workflows
Pre-built workflow definitions for common automation scenarios
"""

from pathlib import Path
from typing import Any, Dict, List

import yaml


# Workflow registry
WORKFLOW_REGISTRY: dict[str, Any] = {}


def load_workflow(workflow_name: str) -> dict[str, Any]:
    """Load a workflow definition from YAML file"""
    workflow_file = Path(__file__).parent / f"{workflow_name}.yaml"
    if workflow_file.exists():
        with open(workflow_file, encoding="utf-8") as f:
            result = yaml.safe_load(f)
            return result if result is not None else {}
    msg = f"Workflow '{workflow_name}' not found"
    raise FileNotFoundError(msg)


def list_workflows() -> list[str]:
    """List all available workflows"""
    workflow_dir = Path(__file__).parent
    workflows = [file.stem for file in workflow_dir.glob("*.yaml")]
    return sorted(workflows)


# Core workflow definitions
CORE_WORKFLOWS = [
    "phase2_rapid_prototyping",
    "phase1_pr_review_workflow",
    "enhanced_pr_comment_handler",
    "pr_comment_handler",
    "screenshot_gallery",
    "pr_size_labeler",
    "branch_cleanup",
    "changelog_updater",
    "security_audit",
    "dead_code_report",
    "stale_issue_closer",
    "automated_dependency_update",
    "onboard_contributor",
    "magic_fix",
    "release_drafter",
    "tech_debt_report",
    "update_documentation",
    "scaffold_component_workflow",
    "quality_gate",
]

# Workflow categories
WORKFLOW_CATEGORIES = {
    "pr_management": [
        "phase1_pr_review_workflow",
        "enhanced_pr_comment_handler",
        "pr_comment_handler",
        "pr_size_labeler",
        "magic_fix",
    ],
    "rapid_prototyping": ["phase2_rapid_prototyping", "scaffold_component_workflow"],
    "quality_assurance": [
        "security_audit",
        "quality_gate",
        "dead_code_report",
        "tech_debt_report",
    ],
    "maintenance": [
        "branch_cleanup",
        "stale_issue_closer",
        "automated_dependency_update",
        "changelog_updater",
    ],
    "documentation": ["update_documentation", "screenshot_gallery"],
    "release": ["release_drafter"],
    "onboarding": ["onboard_contributor"],
}


def get_workflows_by_category(category: str) -> list[str]:
    """Get workflows by category"""
    return WORKFLOW_CATEGORIES.get(category, [])


def get_workflow_info(workflow_name: str) -> dict[str, Any]:
    """Get workflow information including metadata"""
    try:
        workflow = load_workflow(workflow_name)
        return {
            "name": workflow.get("name", workflow_name),
            "description": workflow.get("description", ""),
            "triggers": workflow.get("triggers", []),
            "steps": len(workflow.get("steps", [])),
            "category": next(
                (
                    cat
                    for cat, workflows in WORKFLOW_CATEGORIES.items()
                    if workflow_name in workflows
                ),
                "other",
            ),
        }
    except FileNotFoundError:
        return {"error": f"Workflow '{workflow_name}' not found"}


__all__ = [
    "CORE_WORKFLOWS",
    "WORKFLOW_CATEGORIES",
    "get_workflow_info",
    "get_workflows_by_category",
    "list_workflows",
    "load_workflow",
]
