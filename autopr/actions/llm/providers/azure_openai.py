"""
Azure OpenAI Provider for AutoPR LLM system.

Supports Azure OpenAI endpoints with custom configurations.
"""

import logging
import os
from typing import Any

from autopr.actions.llm.base import BaseLLMProvider
from autopr.actions.llm.types import LLMResponse

logger = logging.getLogger(__name__)


class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI provider implementation."""

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.name = "azure_openai"
        self.description = "Azure OpenAI API provider with custom endpoints"

        # Azure-specific configuration
        self.azure_endpoint = config.get("azure_endpoint") or os.getenv(
            "AZURE_OPENAI_ENDPOINT"
        )
        self.api_version = config.get("api_version", "2024-02-01")
        self.deployment_name = config.get("deployment_name", "gpt-35-turbo")

        # Use Azure-specific API key environment variable
        azure_api_key = config.get("api_key") or os.getenv("AZURE_OPENAI_API_KEY")
        if azure_api_key:
            self.api_key = azure_api_key

        self.default_model = self.deployment_name
        self._client = None

    def is_available(self) -> bool:
        """Check if Azure OpenAI is properly configured."""
        return bool(self.api_key and self.azure_endpoint)

    def _get_client(self):
        """Get or create Azure OpenAI client."""
        if self._client is None:
            try:
                from openai import AzureOpenAI

                self._client = AzureOpenAI(
                    api_key=self.api_key,
                    api_version=self.api_version,
                    azure_endpoint=self.azure_endpoint,
                )
                logger.info(
                    f"Initialized Azure OpenAI client with endpoint: {self.azure_endpoint}"
                )
            except ImportError:
                logger.exception(
                    "openai package not installed. Install with: pip install openai"
                )
                return None
            except Exception as e:
                logger.exception(f"Failed to initialize Azure OpenAI client: {e}")
                return None

        return self._client

    def complete(self, request: dict[str, Any]) -> LLMResponse:
        """Complete a chat conversation using Azure OpenAI."""
        client = self._get_client()
        if not client:
            return LLMResponse.from_error(
                "Azure OpenAI client not available",
                request.get("model", self.default_model),
            )

        try:
            # Extract parameters
            messages = request.get("messages", [])
            model = request.get("model", self.deployment_name)
            temperature = request.get("temperature", 0.7)
            max_tokens = request.get("max_tokens", 1000)

            # Validate messages format
            if not messages:
                return LLMResponse.from_error("No messages provided", model)

            # Make the API call
            response = client.chat.completions.create(
                model=model,  # This is the deployment name in Azure
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Extract response content
            content = ""
            finish_reason = "unknown"
            usage = None

            if response.choices:
                choice = response.choices[0]
                content = choice.message.content or ""
                finish_reason = choice.finish_reason or "unknown"

            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            return LLMResponse(
                content=content,
                model=model,
                finish_reason=finish_reason,
                usage=usage,
            )

        except Exception as e:
            error_msg = f"Azure OpenAI API error: {e!s}"
            logger.exception(error_msg)
            return LLMResponse.from_error(
                error_msg, request.get("model", self.default_model)
            )
