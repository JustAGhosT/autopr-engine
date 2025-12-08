"""
AutoPR Engine - Automated Code Review and Quality Management System

This package provides AI-powered code analysis, automated fixes, and quality assurance workflows.
"""

import logging
import os
from typing import Any, cast

from codeflow_engine.actions.registry import ActionRegistry
# from codeflow_engine.agents.agents import AgentManager  # Not implemented yet
from codeflow_engine.ai.core.base import LLMProvider
from codeflow_engine.ai.core.providers.manager import LLMProviderManager
from codeflow_engine.config import AutoPRConfig
from codeflow_engine.engine import AutoPREngine
from codeflow_engine.exceptions import (AutoPRException, ConfigurationError,
                               IntegrationError)
from codeflow_engine.integrations.base import Integration
# from codeflow_engine.integrations.bitbucket.bitbucket_integration import \
#     BitbucketIntegration  # Not implemented yet
# from codeflow_engine.integrations.github.github_integration import GitHubIntegration  # Not implemented yet
# from codeflow_engine.integrations.gitlab.gitlab_integration import GitLabIntegration  # Not implemented yet
# from codeflow_engine.integrations.jira.jira_integration import JiraIntegration  # Not implemented yet
# from codeflow_engine.integrations.registry import IntegrationRegistry  # Not implemented yet
# from codeflow_engine.integrations.slack.slack_integration import SlackIntegration  # Not implemented yet
from codeflow_engine.quality.metrics_collector import MetricsCollector
# from codeflow_engine.reporting.report_generator import ReportGenerator  # Not implemented yet
from codeflow_engine.security.authorization.enterprise_manager import \
    EnterpriseAuthorizationManager
from codeflow_engine.workflows.base import Workflow
from codeflow_engine.workflows.engine import WorkflowEngine

# from codeflow_engine.workflows.workflow_manager import WorkflowManager  # Not implemented yet

# Import structlog with error handling
STRUCTLOG_AVAILABLE: bool
try:
    import structlog

    STRUCTLOG_AVAILABLE = True
    structlog_module = cast("Any", structlog)
except ImportError:
    STRUCTLOG_AVAILABLE = False
    structlog_module = None

__version__ = "1.0.1"

# Public API exports
__all__ = [
    "ActionRegistry",
    "AutoPREngine",
    "MetricsCollector",
    "EnterpriseAuthorizationManager",
    "LLMProvider",
    "LLMProviderManager",
]

# Setup logging defaults


def configure_logging(level: str = "INFO", *, format_json: bool = False) -> None:
    """Configure default logging for AutoPR Engine."""

    if format_json and STRUCTLOG_AVAILABLE and structlog_module:
        # Structured JSON logging
        structlog_module.configure(
            processors=[
                structlog_module.processors.TimeStamper(fmt="iso"),
                structlog_module.processors.add_log_level,
                structlog_module.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog_module.WriteLoggerFactory(),
            wrapper_class=structlog_module.make_filtering_bound_logger(
                getattr(logging, level.upper())
            ),
            cache_logger_on_first_use=True,
        )
    else:
        # Standard logging
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


log_level = os.getenv("AUTOPR_LOG_LEVEL", "INFO")
json_logging = os.getenv("AUTOPR_JSON_LOGGING", "false").lower() == "true"
configure_logging(level=log_level, format_json=json_logging)
