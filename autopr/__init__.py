"""
AutoPR Engine - AI-Powered GitHub PR Automation and Issue Management.

A comprehensive platform for intelligent GitHub pull request analysis,
automated issue creation, and multi-agent AI collaboration.
"""

import logging
import os
from typing import Any, cast

from autopr.actions.base import Action, ActionInputs, ActionOutputs
from autopr.actions.registry import ActionRegistry
from autopr.ai.base import LLMProvider
from autopr.ai.providers.manager import LLMProviderManager
from autopr.config import AutoPRConfig
from autopr.engine import AutoPREngine
from autopr.exceptions import (AutoPRException, ConfigurationError,
                               IntegrationError)
from autopr.integrations.base import Integration
from autopr.integrations.registry import IntegrationRegistry
from autopr.workflows.base import Workflow
from autopr.workflows.engine import WorkflowEngine

# Import structlog with error handling
STRUCTLOG_AVAILABLE: bool
try:
    import structlog

    STRUCTLOG_AVAILABLE = True
    structlog_module = cast("Any", structlog)
except ImportError:
    STRUCTLOG_AVAILABLE = False
    structlog_module = None

__version__ = "1.0.0"
__author__ = "VeritasVault Team"
__email__ = "dev@veritasvault.net"
__license__ = "MIT"
__url__ = "https://github.com/veritasvault/autopr-engine"

# Public API exports
__all__ = [
    # Actions
    "Action",
    "ActionInputs",
    "ActionOutputs",
    "ActionRegistry",
    "AutoPRConfig",
    # Core
    "AutoPREngine",
    # Exceptions
    "AutoPRException",
    "ConfigurationError",
    # Integrations
    "Integration",
    "IntegrationError",
    "IntegrationRegistry",
    # AI/LLM
    "LLMProvider",
    "LLMProviderManager",
    "Workflow",
    # Workflows
    "WorkflowEngine",
    "__author__",
    "__email__",
    "__license__",
    "__url__",
    # Version info
    "__version__",
]

# Package metadata
__package_info__ = {
    "name": "autopr-engine",
    "version": __version__,
    "description": "AI-Powered GitHub PR Automation and Issue Management",
    "author": __author__,
    "author_email": __email__,
    "license": __license__,
    "url": __url__,
    "keywords": [
        "github",
        "pull-request",
        "automation",
        "ai",
        "code-review",
        "ci-cd",
        "workflow",
        "integration",
        "slack",
        "linear",
        "autogen",
        "llm",
        "openai",
        "anthropic",
        "issue-management",
    ],
    "classifiers": [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
}

# Optional dependency warnings
try:
    pass
except ImportError:
    import warnings

    warnings.warn(
        "AutoGen is not installed. Multi-agent features will be unavailable. "
        "Install with: pip install 'autopr-engine[ai]'",
        ImportWarning,
        stacklevel=2,
    )

# Mem0 is an optional dependency for advanced memory features
mem0 = None
try:
    pass
except ImportError:
    import warnings

    warnings.warn(
        "Mem0 is not installed. Advanced memory features will be unavailable. "
        "Install with: pip install 'autopr-engine[memory]'",
        ImportWarning,
        stacklevel=2,
    )

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
