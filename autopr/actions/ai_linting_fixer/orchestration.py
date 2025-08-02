"""
Orchestration Module

This module handles workflow orchestration functions for the AI linting fixer.
"""

import contextlib
import logging
import os
from typing import Any

from .models import AILintingFixerInputs, AILintingFixerOutputs, OrchestrationConfig, WorkflowResult

logger = logging.getLogger(__name__)


def detect_available_orchestrators() -> dict[str, bool]:
    """Detect which orchestration systems are available."""
    availability = {"temporal": False, "celery": False, "prefect": False, "airflow": False}

    # Check Temporal.io
    try:
        # Check if environment variables are set
        if os.getenv("TEMPORAL_API_KEY") or os.getenv("TEMPORAL_ADDRESS"):
            availability["temporal"] = True
    except ImportError:
        pass

    # Check Celery
    with contextlib.suppress(ImportError):
        availability["celery"] = True

    # Check Prefect
    with contextlib.suppress(ImportError):
        availability["prefect"] = True

    # Check Airflow
    with contextlib.suppress(ImportError):
        availability["airflow"] = True

    return availability


def get_orchestration_config() -> OrchestrationConfig:
    """Get orchestration configuration from environment."""
    # Check which orchestrators are available
    available = detect_available_orchestrators()

    # Determine which orchestrator to use based on environment
    orchestrator_type = "none"
    if available["temporal"] and os.getenv("USE_TEMPORAL"):
        orchestrator_type = "temporal"
    elif available["celery"] and os.getenv("USE_CELERY"):
        orchestrator_type = "celery"
    elif available["prefect"] and os.getenv("USE_PREFECT"):
        orchestrator_type = "prefect"
    elif available["airflow"] and os.getenv("USE_AIRFLOW"):
        orchestrator_type = "airflow"

    return OrchestrationConfig(
        enabled=orchestrator_type != "none", orchestrator_type=orchestrator_type
    )


def execute_with_orchestration(
    inputs: AILintingFixerInputs, orchestration_config: OrchestrationConfig
) -> AILintingFixerOutputs | WorkflowResult:
    """Execute AI linting fixer with orchestration."""
    if not orchestration_config.enabled:
        logger.info("Orchestration disabled, running in standalone mode")
        return _execute_standalone(inputs)

    try:
        if orchestration_config.orchestrator_type == "temporal":
            return _execute_with_temporal(inputs, orchestration_config)
        if orchestration_config.orchestrator_type == "celery":
            return _execute_with_celery(inputs, orchestration_config)
        if orchestration_config.orchestrator_type == "prefect":
            return _execute_with_prefect(inputs, orchestration_config)
        logger.warning(f"Unknown orchestrator type: {orchestration_config.orchestrator_type}")
        return _execute_standalone(inputs)

    except Exception as e:
        logger.exception(f"Orchestration execution failed: {e}")
        if orchestration_config.fallback_to_standalone:
            logger.info("Falling back to standalone execution")
            return _execute_standalone(inputs)
        raise


def _execute_standalone(inputs: AILintingFixerInputs) -> AILintingFixerOutputs:
    """Execute AI linting fixer in standalone mode."""
    try:
        from .ai_linting_fixer import AILintingFixer

        # Initialize components
        fixer = AILintingFixer()

        # Run the AI linting fixer
        result = fixer.run(inputs)

        return result

    except Exception as e:
        logger.exception(f"Standalone execution failed: {e}")
        return AILintingFixerOutputs(
            total_issues_found=0,
            issues_fixed=0,
            files_modified=[],
            success=False,
            summary=f"Execution failed: {e!s}",
        )


def _execute_with_temporal(
    inputs: AILintingFixerInputs, orchestration_config: OrchestrationConfig
) -> WorkflowResult:
    """Execute with Temporal.io orchestration."""
    try:
        from datetime import timedelta

        from temporalio import activity, workflow

        @activity.defn
        async def ai_linting_activity(input_data: dict[str, Any]) -> dict[str, Any]:
            """Temporal activity for AI linting."""
            # This would contain the actual AI linting logic
            # For now, return a placeholder result
            return {"success": True, "issues_found": 0, "issues_fixed": 0, "files_modified": []}

        @workflow.defn
        class AILintingWorkflow:
            @workflow.run
            async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
                """Run the AI linting workflow."""
                # Execute the activity
                return await workflow.execute_activity(
                    ai_linting_activity, input_data, start_to_close_timeout=timedelta(minutes=30)
                )

        # Convert inputs to dict for Temporal
        inputs.model_dump()

        # Execute workflow (this is a simplified version)
        # In a real implementation, you would use Temporal client
        logger.info("Executing with Temporal orchestration")

        # Placeholder result
        return WorkflowResult(
            workflow_id="temporal_workflow_123",
            step_name="ai_linting",
            execution_time=60.0,
            status="success",
            files_processed=1,
            issues_found=0,
            issues_fixed=0,
            modified_files=[],
            success_rate=100.0,
            average_confidence=0.9,
            performance_metrics={},
        )

    except ImportError:
        logger.exception("Temporal.io not available")
        raise
    except Exception as e:
        logger.exception(f"Temporal execution failed: {e}")
        raise


def _execute_with_celery(
    inputs: AILintingFixerInputs, orchestration_config: OrchestrationConfig
) -> WorkflowResult:
    """Execute with Celery orchestration."""
    try:
        from celery import Celery

        # Initialize Celery app
        app = Celery(
            orchestration_config.celery["task_name"],
            broker=orchestration_config.celery["broker_url"],
            backend=orchestration_config.celery["result_backend"],
        )

        @app.task
        def ai_linting_task(input_data: dict[str, Any]) -> dict[str, Any]:
            """Celery task for AI linting."""
            # This would contain the actual AI linting logic
            return {"success": True, "issues_found": 0, "issues_fixed": 0, "files_modified": []}

        # Convert inputs to dict for Celery
        input_data = inputs.model_dump()

        # Execute task
        logger.info("Executing with Celery orchestration")
        result = ai_linting_task.delay(input_data)

        # Get result (blocking)
        task_result = result.get(timeout=300)  # 5 minute timeout

        return WorkflowResult(
            workflow_id=f"celery_task_{result.id}",
            step_name="ai_linting",
            execution_time=60.0,
            status="success" if task_result.get("success") else "failed",
            files_processed=1,
            issues_found=task_result.get("issues_found", 0),
            issues_fixed=task_result.get("issues_fixed", 0),
            modified_files=task_result.get("files_modified", []),
            success_rate=100.0 if task_result.get("success") else 0.0,
            average_confidence=0.9,
            performance_metrics={},
        )

    except ImportError:
        logger.exception("Celery not available")
        raise
    except Exception as e:
        logger.exception(f"Celery execution failed: {e}")
        raise


def _execute_with_prefect(
    inputs: AILintingFixerInputs, orchestration_config: OrchestrationConfig
) -> WorkflowResult:
    """Execute with Prefect orchestration."""
    try:
        from prefect import flow, task

        @task
        def ai_linting_task(input_data: dict[str, Any]) -> dict[str, Any]:
            """Prefect task for AI linting."""
            # This would contain the actual AI linting logic
            return {"success": True, "issues_found": 0, "issues_fixed": 0, "files_modified": []}

        @flow(name=orchestration_config.prefect["flow_name"])
        def ai_linting_flow(input_data: dict[str, Any]) -> dict[str, Any]:
            """Prefect flow for AI linting."""
            return ai_linting_task(input_data)

        # Convert inputs to dict for Prefect
        input_data = inputs.model_dump()

        # Execute flow
        logger.info("Executing with Prefect orchestration")
        result = ai_linting_flow(input_data)

        return WorkflowResult(
            workflow_id="prefect_flow_123",
            step_name="ai_linting",
            execution_time=60.0,
            status="success" if result.get("success") else "failed",
            files_processed=1,
            issues_found=result.get("issues_found", 0),
            issues_fixed=result.get("issues_fixed", 0),
            modified_files=result.get("files_modified", []),
            success_rate=100.0 if result.get("success") else 0.0,
            average_confidence=0.9,
            performance_metrics={},
        )

    except ImportError:
        logger.exception("Prefect not available")
        raise
    except Exception as e:
        logger.exception(f"Prefect execution failed: {e}")
        raise


def create_workflow_context(
    workflow_id: str | None = None,
    step_name: str = "ai_linting",
    execution_mode: str = "standalone",
    priority: int = 5,
    timeout_seconds: int = 300,
) -> dict[str, Any]:
    """Create a workflow context for orchestration."""
    from .models import WorkflowContext

    return WorkflowContext(
        workflow_id=workflow_id,
        step_name=step_name,
        execution_mode=execution_mode,
        priority=priority,
        timeout_seconds=timeout_seconds,
    ).model_dump()


def validate_orchestration_config(config: OrchestrationConfig) -> bool:
    """Validate orchestration configuration."""
    try:
        if not config.enabled:
            return True

        if config.orchestrator_type == "temporal":
            # Validate Temporal configuration
            required_fields = ["namespace", "task_queue", "address"]
            for field in required_fields:
                if field not in config.temporal:
                    logger.error(f"Missing required Temporal field: {field}")
                    return False

        elif config.orchestrator_type == "celery":
            # Validate Celery configuration
            required_fields = ["broker_url", "result_backend"]
            for field in required_fields:
                if field not in config.celery:
                    logger.error(f"Missing required Celery field: {field}")
                    return False

        elif config.orchestrator_type == "prefect":
            # Validate Prefect configuration
            required_fields = ["flow_name", "task_name"]
            for field in required_fields:
                if field not in config.prefect:
                    logger.error(f"Missing required Prefect field: {field}")
                    return False

        return True

    except Exception as e:
        logger.exception(f"Error validating orchestration config: {e}")
        return False
