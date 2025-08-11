"""
Temporal.io Workflow Integration for AI Linting System

This module provides enterprise-grade workflow orchestration using Temporal.io
for the AutoPR AI linting system. It demonstrates how to integrate our
WorkflowContext architecture with real workflow orchestration.

Author: AutoPR AI Systems
"""

import asyncio
import logging
import os
import pathlib
from datetime import timedelta
from typing import Any

from temporalio import activity, workflow
from temporalio.client import Client, TLSConfig
from temporalio.common import RetryPolicy
from temporalio.worker import Worker

from autopr.actions.ai_linting_fixer import (
    AILintingFixerInputs,
    WorkflowContext,
    WorkflowResult,
    ai_linting_fixer,
)

logger = logging.getLogger(__name__)


# =============================================================================
# TEMPORAL WORKFLOW DEFINITIONS
# =============================================================================


@workflow.defn
class AILintingWorkflow:
    """
    Temporal workflow for orchestrating AI-powered code linting.

    This workflow demonstrates enterprise-grade orchestration with:
    - Automatic retries and error handling
    - Progress tracking and monitoring
    - Resource management
    - Integration with other workflows
    """

    @workflow.run
    async def run(self, workflow_input: dict[str, Any]) -> dict[str, Any]:
        """
        Main workflow execution for AI linting.

        Args:
            workflow_input: Configuration for the linting workflow

        Returns:
            Comprehensive workflow result with metrics and artifacts
        """
        workflow_id = workflow.info().workflow_id

        logger.info(f"🚀 Starting AI Linting Workflow: {workflow_id}")

        # Create workflow context for tracking
        workflow_context = WorkflowContext(
            workflow_id=workflow_id,
            execution_mode="orchestrated",
            step_name="ai_linting_temporal",
            priority=workflow_input.get("priority", 5),
            timeout_seconds=workflow_input.get("timeout", 600),
            metadata={
                "temporal_workflow": True,
                "namespace": workflow.info().namespace,
                "task_queue": workflow.info().task_queue,
                "run_id": workflow.info().run_id,
            },
        )

        # Step 1: Validate inputs and setup
        setup_result = await workflow.execute_activity(
            validate_and_setup_activity,
            workflow_input,
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                backoff_coefficient=2.0,
                maximum_interval=timedelta(seconds=10),
                maximum_attempts=3,
            ),
        )

        if not setup_result["valid"]:
            return {
                "success": False,
                "error": setup_result["error"],
                "workflow_id": workflow_id,
                "step": "validation",
            }

        # Step 2: Run AI linting with full orchestration
        linting_result = await workflow.execute_activity(
            ai_linting_activity,
            {"inputs": workflow_input, "workflow_context": workflow_context.dict()},
            start_to_close_timeout=timedelta(minutes=10),
            heartbeat_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=5),
                backoff_coefficient=2.0,
                maximum_interval=timedelta(minutes=1),
                maximum_attempts=2,
            ),
        )

        # Step 3: Post-processing based on results
        if linting_result.get("success") and linting_result.get("modified_files"):
            # If files were modified, trigger follow-up workflows

            # Run tests (parallel activity)
            test_future = workflow.execute_activity(
                run_tests_activity,
                {"files": linting_result["modified_files"]},
                start_to_close_timeout=timedelta(minutes=5),
            )

            # Generate quality report (parallel activity)
            report_future = workflow.execute_activity(
                generate_quality_report_activity,
                {"linting_result": linting_result},
                start_to_close_timeout=timedelta(minutes=2),
            )

            # Wait for both to complete
            test_result, report_result = await asyncio.gather(test_future, report_future)

            # Step 4: Final integration steps
            if test_result.get("success"):
                # Commit changes if tests pass
                commit_result = await workflow.execute_activity(
                    commit_changes_activity,
                    {
                        "files": linting_result["modified_files"],
                        "summary": linting_result.get("summary", "AI linting fixes"),
                    },
                    start_to_close_timeout=timedelta(minutes=2),
                )

                # Notify stakeholders
                notification_result = await workflow.execute_activity(
                    notify_completion_activity,
                    {
                        "workflow_id": workflow_id,
                        "linting_result": linting_result,
                        "test_result": test_result,
                        "commit_result": commit_result,
                    },
                    start_to_close_timeout=timedelta(minutes=1),
                )

                return {
                    "success": True,
                    "workflow_id": workflow_id,
                    "linting_result": linting_result,
                    "test_result": test_result,
                    "commit_result": commit_result,
                    "report_result": report_result,
                    "notification_result": notification_result,
                    "final_status": "completed_with_changes",
                }
            # Tests failed - create issue for manual review
            issue_result = await workflow.execute_activity(
                create_review_issue_activity,
                {
                    "workflow_id": workflow_id,
                    "linting_result": linting_result,
                    "test_failure": test_result,
                },
                start_to_close_timeout=timedelta(minutes=2),
            )

            return {
                "success": False,
                "workflow_id": workflow_id,
                "linting_result": linting_result,
                "test_result": test_result,
                "issue_result": issue_result,
                "final_status": "tests_failed_manual_review_required",
            }
        # No changes made or linting failed
        return {
            "success": linting_result.get("success", False),
            "workflow_id": workflow_id,
            "linting_result": linting_result,
            "final_status": "no_changes" if linting_result.get("success") else "linting_failed",
        }


# =============================================================================
# TEMPORAL ACTIVITIES
# =============================================================================


@activity.defn
async def validate_and_setup_activity(workflow_input: dict[str, Any]) -> dict[str, Any]:
    """Validate inputs and setup the environment for AI linting."""
    try:
        # Validate required fields
        required_fields = ["target_path", "fix_types"]
        for field in required_fields:
            if field not in workflow_input:
                return {"valid": False, "error": f"Missing required field: {field}"}

        # Validate API keys are available
        if not os.getenv("AZURE_OPENAI_API_KEY"):
            return {"valid": False, "error": "AZURE_OPENAI_API_KEY environment variable not set"}

        # Validate target path exists
        target_path = workflow_input["target_path"]
        if not pathlib.Path(target_path).exists():
            return {"valid": False, "error": f"Target path does not exist: {target_path}"}

        return {"valid": True, "message": "Validation successful"}

    except Exception as e:
        logger.exception(f"Setup validation failed: {e}")
        return {"valid": False, "error": f"Validation error: {e!s}"}


@activity.defn
async def ai_linting_activity(activity_input: dict[str, Any]) -> dict[str, Any]:
    """Core AI linting activity with full workflow integration."""
    try:
        inputs_dict = activity_input["inputs"]
        workflow_context_dict = activity_input["workflow_context"]

        # Reconstruct workflow context
        workflow_context = WorkflowContext(**workflow_context_dict)

        # Convert to AILintingFixerInputs
        linting_inputs = AILintingFixerInputs(
            target_path=inputs_dict["target_path"],
            fix_types=inputs_dict.get("fix_types", ["E501", "F401", "F841"]),
            max_fixes_per_run=inputs_dict.get("max_fixes", 10),
            provider=inputs_dict.get("provider", "azure_openai"),
            model=inputs_dict.get("model", "gpt-4.1"),
            max_workers=inputs_dict.get("max_workers", 4),
        )

        # Add progress callback for Temporal heartbeats
        def progress_callback(event):
            activity.heartbeat(f"Processing: {event.data.get('stage', 'unknown')}")

        workflow_context.progress_callback = progress_callback

        # Run the AI linting with workflow context
        result = ai_linting_fixer(linting_inputs, workflow_context)

        # Convert result to dict for Temporal serialization
        if isinstance(result, WorkflowResult):
            return result.dict()
        # Convert legacy result format
        return {
            "success": result.success,
            "issues_fixed": result.issues_fixed,
            "modified_files": result.files_modified,
            "total_issues_found": result.total_issues_found,
            "summary": result.summary,
        }

    except Exception as e:
        logger.exception(f"AI linting activity failed: {e}")
        return {"success": False, "error": str(e), "issues_fixed": 0, "modified_files": []}


@activity.defn
async def run_tests_activity(test_input: dict[str, Any]) -> dict[str, Any]:
    """Run tests on modified files."""
    try:
        modified_files = test_input["files"]

        if not modified_files:
            return {"success": True, "message": "No files to test"}

        # For demo purposes, we'll simulate test execution
        # In a real implementation, this would run actual tests
        logger.info(f"🧪 Running tests for {len(modified_files)} modified files")

        # Simulate test execution
        await asyncio.sleep(2)

        # For now, assume tests pass if less than 5 files were modified
        success = len(modified_files) <= 5

        return {
            "success": success,
            "files_tested": len(modified_files),
            "message": "Tests passed" if success else "Tests failed - too many changes",
            "test_command": "python -m pytest",
            "execution_time": 2.0,
        }

    except Exception as e:
        logger.exception(f"Test execution failed: {e}")
        return {"success": False, "error": str(e)}


@activity.defn
async def generate_quality_report_activity(report_input: dict[str, Any]) -> dict[str, Any]:
    """Generate a quality report for the linting results."""
    try:
        linting_result = report_input["linting_result"]

        report = {
            "timestamp": activity.info().current_attempt_scheduled_time.isoformat(),
            "summary": {
                "total_issues_found": linting_result.get("total_issues_found", 0),
                "issues_fixed": linting_result.get("issues_fixed", 0),
                "files_modified": len(linting_result.get("modified_files", [])),
                "success_rate": (
                    linting_result.get("issues_fixed", 0)
                    / max(linting_result.get("total_issues_found", 1), 1)
                )
                * 100,
            },
            "files": linting_result.get("modified_files", []),
            "performance": linting_result.get("performance_metrics", {}),
            "recommendations": [],
        }

        # Add recommendations based on results
        if report["summary"]["success_rate"] < 50:
            report["recommendations"].append("Consider manual review of complex issues")

        if len(report["files"]) > 10:
            report["recommendations"].append("Large number of changes - review carefully")

        return {
            "success": True,
            "report": report,
            "report_url": f"/reports/linting/{activity.info().workflow_id}",
        }

    except Exception as e:
        logger.exception(f"Report generation failed: {e}")
        return {"success": False, "error": str(e)}


@activity.defn
async def commit_changes_activity(commit_input: dict[str, Any]) -> dict[str, Any]:
    """Commit the AI linting changes."""
    try:
        files = commit_input["files"]
        summary = commit_input["summary"]

        # For demo purposes, simulate git operations
        # In real implementation, this would use git commands
        logger.info(f"📝 Committing {len(files)} modified files")

        commit_message = f"🤖 AI: {summary}\n\nAutomated via Temporal workflow"

        return {
            "success": True,
            "commit_sha": "abc123def456",  # Simulated
            "commit_message": commit_message,
            "files_committed": len(files),
            "branch": "main",
        }

    except Exception as e:
        logger.exception(f"Commit failed: {e}")
        return {"success": False, "error": str(e)}


@activity.defn
async def notify_completion_activity(notification_input: dict[str, Any]) -> dict[str, Any]:
    """Send completion notifications."""
    try:
        workflow_id = notification_input["workflow_id"]
        linting_result = notification_input["linting_result"]

        message = f"""🎉 AI Linting Workflow Completed!

**Workflow ID:** {workflow_id}
**Issues Fixed:** {linting_result.get('issues_fixed', 0)}
**Files Modified:** {len(linting_result.get('modified_files', []))}
**Status:** Success ✅

View details in Temporal UI: https://cloud.temporal.io/workflows/{workflow_id}
"""

        # In real implementation, send to Slack/Teams/etc
        logger.info(f"📢 Notification: {message}")

        return {
            "success": True,
            "message": "Notifications sent",
            "channels": ["console"],  # Would be ["slack", "email"] in real implementation
        }

    except Exception as e:
        logger.exception(f"Notification failed: {e}")
        return {"success": False, "error": str(e)}


@activity.defn
async def create_review_issue_activity(issue_input: dict[str, Any]) -> dict[str, Any]:
    """Create an issue for manual review when tests fail."""
    try:
        workflow_id = issue_input["workflow_id"]
        test_failure = issue_input["test_failure"]

        issue_title = "Manual Review Required: AI Linting Changes Failed Tests"
        f"""
AI linting workflow `{workflow_id}` made changes but tests failed.

**Test Failure Details:**
{test_failure.get('message', 'Unknown test failure')}

**Next Steps:**
1. Review the AI-generated changes
2. Fix any test failures
3. Manually commit approved changes

**Workflow Details:**
- Workflow ID: {workflow_id}
- View in Temporal: https://cloud.temporal.io/workflows/{workflow_id}
"""

        # In real implementation, create GitHub/Linear issue
        logger.info(f"📋 Creating review issue: {issue_title}")

        return {
            "success": True,
            "issue_id": "ISS-123",  # Simulated
            "issue_url": "https://github.com/repo/issues/123",
            "title": issue_title,
        }

    except Exception as e:
        logger.exception(f"Issue creation failed: {e}")
        return {"success": False, "error": str(e)}


# =============================================================================
# TEMPORAL CLIENT AND WORKER SETUP
# =============================================================================


async def create_temporal_client() -> Client:
    """Create and configure Temporal client with TLS."""

    # Get credentials from environment
    api_key = os.getenv("TEMPORAL_API_KEY")
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    address = os.getenv("TEMPORAL_ADDRESS", "europe-west3.gcp.api.temporal.io:7233")

    if not api_key:
        msg = "TEMPORAL_API_KEY environment variable is required"
        raise ValueError(msg)

    # Configure TLS for Temporal Cloud
    tls_config = TLSConfig(
        client_cert=None,  # Using API key authentication
        client_private_key=None,
    )

    # Create client with proper Temporal Cloud regional endpoint
    client = await Client.connect(
        target_host=address,  # Use the full regional endpoint
        namespace=namespace,
        tls=tls_config,
        api_key=api_key,
    )

    logger.info(f"✅ Connected to Temporal Cloud: {namespace} at {address}")
    return client


async def start_temporal_worker():
    """Start Temporal worker for AI linting workflows."""

    client = await create_temporal_client()

    # Create worker
    worker = Worker(
        client,
        task_queue="ai-linting-queue",
        workflows=[AILintingWorkflow],
        activities=[
            validate_and_setup_activity,
            ai_linting_activity,
            run_tests_activity,
            generate_quality_report_activity,
            commit_changes_activity,
            notify_completion_activity,
            create_review_issue_activity,
        ],
    )

    logger.info("🚀 Starting Temporal worker for AI linting...")
    await worker.run()


async def execute_ai_linting_workflow(
    target_path: str = ".",
    fix_types: list[str] | None = None,
    max_fixes: int = 10,
    priority: int = 5,
) -> dict[str, Any]:
    """Execute AI linting workflow via Temporal."""

    if fix_types is None:
        fix_types = ["E501", "F401", "F841"]

    client = await create_temporal_client()

    # Start workflow
    workflow_input = {
        "target_path": target_path,
        "fix_types": fix_types,
        "max_fixes": max_fixes,
        "priority": priority,
        "provider": "azure_openai",
        "model": "gpt-4.1",
        "max_workers": 4,
    }

    return await client.execute_workflow(
        AILintingWorkflow.run,
        workflow_input,
        id=f"ai-linting-{target_path.replace('/', '-').replace('.', 'root')}",
        task_queue="ai-linting-queue",
        execution_timeout=timedelta(minutes=15),
    )


# =============================================================================
# CLI INTEGRATION
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Temporal AI Linting Workflow")
    parser.add_argument(
        "--mode",
        choices=["worker", "execute"],
        required=True,
        help="Run as worker or execute workflow",
    )
    parser.add_argument("--target", default=".", help="Target path for linting")
    parser.add_argument(
        "--fix-types", nargs="+", default=["E501", "F401"], help="Issue types to fix"
    )
    parser.add_argument("--max-fixes", type=int, default=10, help="Maximum fixes per run")

    args = parser.parse_args()

    if args.mode == "worker":
        asyncio.run(start_temporal_worker())
    else:
        result = asyncio.run(
            execute_ai_linting_workflow(
                target_path=args.target, fix_types=args.fix_types, max_fixes=args.max_fixes
            )
        )
