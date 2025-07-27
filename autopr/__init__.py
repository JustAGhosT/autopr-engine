"""
AutoPR Engine - AI-Powered GitHub PR Automation and Issue Management

A comprehensive platform for intelligent GitHub pull request analysis,
automated issue creation, and multi-agent AI collaboration.
"""

from typing import Any, Dict, List, Optional, Union, cast

__version__ = "1.0.0"
__author__ = "VeritasVault Team"
__email__ = "dev@veritasvault.net"
__license__ = "MIT"
__url__ = "https://github.com/veritasvault/autopr-engine"

# Action framework
from .actions.base import Action, ActionInputs, ActionOutputs
from .actions.registry import ActionRegistry

# AI and LLM providers
from .ai.base import LLMProvider
from .ai.providers.manager import LLMProviderManager
from .config import AutoPRConfig

# Core components
from .engine import AutoPREngine
from .exceptions import AutoPRException, ConfigurationError, IntegrationError

# Integration framework
from .integrations.base import Integration
from .integrations.registry import IntegrationRegistry
from .workflows.base import Workflow

# Workflow system
from .workflows.engine import WorkflowEngine

# Public API exports
__all__ = [
    # Core
    "AutoPREngine",
    "AutoPRConfig",
    # Exceptions
    "AutoPRException",
    "ConfigurationError",
    "IntegrationError",
    # Actions
    "Action",
    "ActionInputs",
    "ActionOutputs",
    "ActionRegistry",
    # Integrations
    "Integration",
    "IntegrationRegistry",
    # AI/LLM
    "LLMProvider",
    "LLMProviderManager",
    # Workflows
    "WorkflowEngine",
    "Workflow",
    # Version info
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__url__",
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
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
}

# Compatibility check
import sys

if sys.version_info < (3, 8):
    raise RuntimeError(
        f"AutoPR Engine requires Python 3.8 or higher. "
        f"Current version: {sys.version_info.major}.{sys.version_info.minor}"
    )

# Optional dependency warnings
try:
    import autogen
except ImportError:
    import warnings

    warnings.warn(
        "AutoGen is not installed. Multi-agent features will be unavailable. "
        "Install with: pip install 'autopr-engine[ai]'",
        ImportWarning,
        stacklevel=2,
    )

try:
    import mem0
except ImportError:
    import warnings

    warnings.warn(
        "Mem0 is not installed. Advanced memory features will be unavailable. "
        "Install with: pip install 'autopr-engine[memory]'",
        ImportWarning,
        stacklevel=2,
    )

# Setup logging defaults
import logging
from typing import Any, Optional, cast

# Import structlog with error handling
STRUCTLOG_AVAILABLE: bool
try:
    import structlog

    STRUCTLOG_AVAILABLE = True
    structlog_module = cast(Any, structlog)
except ImportError:
    STRUCTLOG_AVAILABLE = False
    structlog_module = None


def configure_logging(level: str = "INFO", format_json: bool = False) -> None:
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


# Configure default logging
import os

log_level = os.getenv("AUTOPR_LOG_LEVEL", "INFO")
json_logging = os.getenv("AUTOPR_JSON_LOGGING", "false").lower() == "true"
configure_logging(level=log_level, format_json=json_logging)
