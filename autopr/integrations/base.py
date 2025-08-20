"""
AutoPR Integration Base Classes

Base classes and interfaces for integration implementation.
"""

from abc import ABC, abstractmethod
import logging
from typing import Any


logger = logging.getLogger(__name__)


class Integration(ABC):
    """
    Base class for all AutoPR integrations.

    Integrations provide connectivity to external services and platforms.
    """

    def __init__(self, name: str, description: str = "", version: str = "1.0.0") -> None:
        """
        Initialize the integration.

        Args:
            name: Unique integration name
            description: Human-readable description
            version: Integration version
        """
        self.name = name
        self.description = description
        self.version = version
        self.is_initialized = False
        self.config: dict[str, Any] = {}
        self.required_config_keys: list[str] = []

    @abstractmethod
    async def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize the integration with configuration.

        Args:
            config: Integration configuration
        """

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up integration resources."""

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """
        Perform health check on the integration.

        Returns:
            Health status dictionary
        """

    def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate integration configuration.

        Args:
            config: Configuration to validate

        Returns:
            True if configuration is valid
        """
        for key in self.required_config_keys:
            if key not in config:
                logger.error(
                    "Missing required config key '%s' for integration '%s'",
                    key,
                    self.name,
                )
                return False
        return True

    def get_metadata(self) -> dict[str, Any]:
        """
        Get integration metadata.

        Returns:
            Dictionary containing integration metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "is_initialized": self.is_initialized,
            "required_config_keys": self.required_config_keys,
        }

    def __str__(self) -> str:
        return f"Integration(name='{self.name}', version='{self.version}')"

    def __repr__(self) -> str:
        return self.__str__()


class GitHubIntegration(Integration):
    """
    Base class for GitHub integrations.

    Provides common functionality for GitHub API interactions.
    """

    def __init__(self, name: str, description: str = "", version: str = "1.0.0") -> None:
        super().__init__(name, description, version)
        self.required_config_keys.extend(["github_token"])
        self.github_client: dict[str, Any] | None = None

    async def initialize(self, config: dict[str, Any]) -> None:
        """Initialize GitHub integration."""
        if not self.validate_config(config):
            msg = f"Invalid configuration for GitHub integration '{self.name}'"
            raise ValueError(msg)

        self.config = config

        try:
            # Initialize GitHub client
            github_token = config["github_token"]
            # Note: Initialize actual GitHub client when SDK is integrated
            self.github_client = {"token": github_token}  # Placeholder

            self.is_initialized = True
            logger.info("GitHub integration '%s' initialized successfully", self.name)

        except Exception:
            logger.exception("Failed to initialize GitHub integration '%s'", self.name)
            raise

    async def cleanup(self) -> None:
        """Clean up GitHub integration."""
        self.github_client = None
        self.is_initialized = False
        logger.info("GitHub integration '%s' cleaned up", self.name)

    async def health_check(self) -> dict[str, Any]:
        """Perform GitHub API health check."""
        if not self.is_initialized:
            return {"status": "unhealthy", "message": "Integration not initialized"}

        try:
            # Note: Replace with real GitHub API health check
            return {
                "status": "healthy",
                "message": "GitHub API accessible",
                "api_rate_limit": "unknown",
            }
        except Exception as e:
            return {"status": "unhealthy", "message": f"GitHub API error: {e}"}


class LLMIntegration(Integration):
    """
    Base class for LLM provider integrations.

    Provides common functionality for AI/LLM service interactions.
    """

    def __init__(self, name: str, description: str = "", version: str = "1.0.0") -> None:
        super().__init__(name, description, version)
        self.required_config_keys.extend(["api_key"])
        self.client: dict[str, Any] | None = None
        self.model_name = "default"

    async def initialize(self, config: dict[str, Any]) -> None:
        """Initialize LLM integration."""
        if not self.validate_config(config):
            msg = f"Invalid configuration for LLM integration '{self.name}'"
            raise ValueError(msg)

        self.config = config
        self.model_name = config.get("model_name", "default")

        try:
            # Initialize LLM client
            api_key = config["api_key"]
            # Note: Initialize actual LLM client when SDK is integrated
            self.client = {"api_key": api_key}  # Placeholder

            self.is_initialized = True
            logger.info("LLM integration '%s' initialized successfully", self.name)

        except Exception:
            logger.exception("Failed to initialize LLM integration '%s'", self.name)
            raise

    async def cleanup(self) -> None:
        """Clean up LLM integration."""
        self.client = None
        self.is_initialized = False
        logger.info("LLM integration '%s' cleaned up", self.name)

    async def health_check(self) -> dict[str, Any]:
        """Perform LLM provider health check."""
        if not self.is_initialized:
            return {"status": "unhealthy", "message": "Integration not initialized"}

        try:
            # Note: Replace with real LLM provider health check
            return {
                "status": "healthy",
                "message": "LLM provider accessible",
                "model": self.model_name,
            }
        except Exception as e:
            return {"status": "unhealthy", "message": f"LLM provider error: {e}"}

    async def generate_completion(
        self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7
    ) -> str:
        """
        Generate text completion using the LLM.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        if not self.is_initialized:
            msg = f"LLM integration '{self.name}' not initialized"
            raise RuntimeError(msg)

        # Placeholder implementation uses parameters to satisfy interface until SDK integration
        return (
            f"Generated response (max_tokens={max_tokens}, temperature={temperature}) "
            f"for prompt: {prompt[:50]}..."
        )
