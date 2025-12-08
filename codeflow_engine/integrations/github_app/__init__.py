"""GitHub App Integration for AutoPR.

Provides one-click installation and automatic secret configuration.
"""

from codeflow_engine.integrations.github_app.callback import callback_router
from codeflow_engine.integrations.github_app.install import install_router
from codeflow_engine.integrations.github_app.setup import setup_router
from codeflow_engine.integrations.github_app.webhook import webhook_router

__all__ = [
    "install_router",
    "callback_router",
    "webhook_router",
    "setup_router",
]

