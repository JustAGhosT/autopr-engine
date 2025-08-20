"""
Dependency Injection container for the Quality Engine.
"""

from dependency_injector import containers, providers

from autopr.actions.quality_engine.config import load_config
from autopr.actions.quality_engine.engine import QualityEngine
from autopr.actions.quality_engine.handler_registry import HandlerRegistry
from autopr.actions.quality_engine.handlers.lint_handler import LintHandler
from autopr.actions.quality_engine.handlers.lint_issue import LintIssue
from autopr.actions.quality_engine.tools import discover_tools

# Import registry at the module level to avoid circular imports
from autopr.actions.quality_engine.tools.registry import (
    registry as tool_registry_instance,
)


class HandlerContainer(containers.DeclarativeContainer):
    """Container for result handlers."""

    # Configure handlers
    lint_handler = providers.Factory(LintHandler)


class ToolRegistryContainer(containers.DeclarativeContainer):
    """Container for tool registry."""

    # Discover and register all tools
    @staticmethod
    def _register_discovered_tools() -> "tool_registry_instance":
        """Register all discovered tools with the registry."""
        discovered_tools = discover_tools()
        for tool_class in discovered_tools:
            tool_registry_instance.register(tool_class)
        return tool_registry_instance

    # Provide the tool registry as a singleton with auto-registration
    registry = providers.Singleton(_register_discovered_tools)


class HandlerRegistryContainer(containers.DeclarativeContainer):
    """Container for handler registry."""

    # Dependencies
    handlers = providers.DependenciesContainer()

    # Create a handler mapping
    handler_mapping = providers.Dict(
        {LintIssue: providers.Callable(lambda handlers: handlers.lint_handler(), handlers=handlers)}
    )

    # Create the handler registry with the mapping
    registry = providers.Singleton(HandlerRegistry, handler_map=handler_mapping)


class QualityEngineContainer(containers.DeclarativeContainer):
    """Main container for the Quality Engine."""

    # Configuration
    config_path = providers.Configuration("config_path")
    config_path.from_env("QUALITY_ENGINE_CONFIG_PATH", "pyproject.toml")

    # Container for handlers
    handlers = providers.Container(HandlerContainer)

    # Container for tool registry
    tools = providers.Container(ToolRegistryContainer)

    # Container for handler registry
    handler_registry = providers.Container(HandlerRegistryContainer, handlers=handlers)

    config = providers.Callable(load_config, config_path=config_path)

    # The main QualityEngine class
    engine = providers.Factory(
        QualityEngine,
        config_path=config_path,
        tool_registry=tools.registry,
        handler_registry=handler_registry.registry,
        config=config,
    )


# Create a global container instance
container = QualityEngineContainer()


# Helper function to get the engine instance
def get_engine(skip_windows_check: bool = False) -> QualityEngine:
    """Get the configured QualityEngine instance."""
    return container.engine(skip_windows_check=skip_windows_check)
