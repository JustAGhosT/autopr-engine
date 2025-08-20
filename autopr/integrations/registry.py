"""
AutoPR Integration Registry

Registry for managing and discovering integrations.
"""

import logging
from typing import Any

from autopr.integrations.base import Integration


logger = logging.getLogger(__name__)


class IntegrationRegistry:
    """
    Registry for managing AutoPR integrations.

    Provides registration, discovery, and management of integrations.
    """

    def __init__(self) -> None:
        """Initialize the integration registry."""
        self._integrations: dict[str, type[Integration]] = {}
        self._instances: dict[str, Integration] = {}

        logger.info("Integration registry initialized")

    def register_integration(self, integration_class: type[Integration]) -> None:
        """
        Register an integration class.

        Args:
            integration_class: Integration class to register
        """
        # Create a temporary instance to get the name
        temp_instance = integration_class("temp", "temp")
        integration_name = temp_instance.name

        self._integrations[integration_name] = integration_class
        logger.info("Registered integration: %s", integration_name)

    def unregister_integration(self, integration_name: str) -> None:
        """
        Unregister an integration.

        Args:
            integration_name: Name of integration to unregister
        """
        if integration_name in self._integrations:
            del self._integrations[integration_name]

        if integration_name in self._instances:
            # Clean up instance
            _ = self._instances[integration_name]
            try:
                # Note: This is synchronous, but cleanup might be async
                # In a real implementation, you'd want to handle this properly
                pass
            except Exception:
                logger.exception("Error cleaning up integration '%s'", integration_name)

            del self._instances[integration_name]

        logger.info("Unregistered integration: %s", integration_name)

    async def get_integration(
        self, integration_name: str, config: dict[str, Any] | None = None
    ) -> Integration | None:
        """
        Get an integration instance by name.

        Args:
            integration_name: Name of integration to get
            config: Configuration for the integration

        Returns:
            Integration instance or None if not found
        """
        if integration_name not in self._integrations:
            logger.warning("Integration not found: %s", integration_name)
            return None

        # Return cached instance if available and initialized
        if integration_name in self._instances:
            instance = self._instances[integration_name]
            if instance.is_initialized:
                return instance

        # Create new instance
        try:
            integration_class = self._integrations[integration_name]
            instance = integration_class(integration_name, f"Instance of {integration_name}")

            # Initialize if config provided
            if config:
                await instance.initialize(config)

            self._instances[integration_name] = instance
            return instance

        except Exception:
            logger.exception("Failed to create integration instance '%s'", integration_name)
            return None

    async def initialize(self, configs: dict[str, dict[str, Any]] | None = None) -> None:
        """
        Initialize all registered integrations.

        Args:
            configs: Dictionary mapping integration names to their configs
        """
        if not configs:
            configs = {}

        for integration_name in self._integrations:
            if integration_name in configs:
                try:
                    await self.get_integration(integration_name, configs[integration_name])
                    logger.info("Initialized integration: %s", integration_name)
                except Exception:
                    logger.exception("Failed to initialize integration '%s'", integration_name)

    async def cleanup(self) -> None:
        """Clean up all integration instances."""
        for integration_name, instance in self._instances.items():
            try:
                await instance.cleanup()
                logger.info("Cleaned up integration: %s", integration_name)
            except Exception:
                logger.exception("Error cleaning up integration '%s'", integration_name)

        self._instances.clear()

    def get_all_integrations(self) -> list[str]:
        """
        Get list of all registered integration names.

        Returns:
            List of integration names
        """
        return list(self._integrations.keys())

    def get_initialized_integrations(self) -> list[str]:
        """
        Get list of initialized integration names.

        Returns:
            List of initialized integration names
        """
        return [name for name, instance in self._instances.items() if instance.is_initialized]

    def get_integrations_metadata(self) -> dict[str, dict]:
        """
        Get metadata for all registered integrations.

        Returns:
            Dictionary mapping integration names to their metadata
        """
        metadata = {}

        for integration_name in self._integrations:
            if integration_name in self._instances:
                instance = self._instances[integration_name]
                metadata[integration_name] = instance.get_metadata()
            else:
                # Create temporary instance for metadata
                try:
                    integration_class = self._integrations[integration_name]
                    temp_instance = integration_class(integration_name, "Temporary")
                    metadata[integration_name] = temp_instance.get_metadata()
                except Exception:
                    logger.exception("Failed to get metadata for '%s'", integration_name)
                    metadata[integration_name] = {"error": "metadata_error"}

        return metadata

    async def health_check_all(self) -> dict[str, dict]:
        """
        Perform health check on all initialized integrations.

        Returns:
            Dictionary mapping integration names to health status
        """
        health_status = {}

        for integration_name, instance in self._instances.items():
            try:
                status = await instance.health_check()
                health_status[integration_name] = status
            except Exception as e:
                health_status[integration_name] = {
                    "status": "error",
                    "message": f"Health check failed: {e}",
                }

        return health_status

    def search_integrations(self, query: str) -> list[str]:
        """
        Search for integrations by name or description.

        Args:
            query: Search query

        Returns:
            List of matching integration names
        """
        query_lower = query.lower()
        matching_integrations = []

        for integration_name in self._integrations:
            if integration_name in self._instances:
                instance = self._instances[integration_name]
                if (
                    query_lower in instance.name.lower()
                    or query_lower in instance.description.lower()
                ):
                    matching_integrations.append(integration_name)
            # Check class name
            elif query_lower in integration_name.lower():
                matching_integrations.append(integration_name)

        return matching_integrations

    def get_registry_stats(self) -> dict[str, int]:
        """
        Get registry statistics.

        Returns:
            Dictionary with registry statistics
        """
        return {
            "total_integrations": len(self._integrations),
            "initialized_integrations": len(
                [instance for instance in self._instances.values() if instance.is_initialized]
            ),
            "total_instances": len(self._instances),
        }
