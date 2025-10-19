"""
LLM Client for AI Linting Fixer

Client for LLM interactions in the AI linting fixer.
"""

import asyncio
import logging
from typing import Any

from autopr.ai.core.providers.manager import LLMProviderManager


logger = logging.getLogger(__name__)


class LLMClient:
    """Unified client for both async and sync LLM manager interfaces."""

    def __init__(self, llm_manager: LLMProviderManager):
        """Initialize the LLM client.
        
        Args:
            llm_manager: The LLM provider manager instance
        """
        self.llm_manager = llm_manager

    async def complete(self, request: dict[str, Any]) -> Any:
        """Make a completion request using the appropriate interface.
        
        Args:
            request: Request parameters including messages, provider, temperature, etc.
            
        Returns:
            LLM response or None if failed
        """
        try:
            # Check if the manager has async methods
            if hasattr(self.llm_manager, "generate_completion") and asyncio.iscoroutinefunction(
                self.llm_manager.generate_completion
            ):
                # Use async interface with generate_completion
                # Build kwargs excluding known keys to forward all other parameters
                known_keys = {"messages", "provider", "temperature", "max_tokens"}
                kwargs = {k: v for k, v in request.items() if k not in known_keys}

                response = await self.llm_manager.generate_completion(
                    messages=request.get("messages", []),
                    provider_name=request.get("provider"),
                    temperature=request.get("temperature", 0.1),
                    max_tokens=request.get("max_tokens"),
                    model=request.get("model"),
                    **kwargs
                )
            elif hasattr(self.llm_manager, "complete") and asyncio.iscoroutinefunction(
                self.llm_manager.complete
            ):
                # Use async interface with complete
                response = await self.llm_manager.complete(request)
            else:
                # Use sync interface - check if result is awaitable
                if hasattr(self.llm_manager, "generate_completion"):
                    # Build kwargs excluding known keys to forward all other parameters
                    known_keys = {"messages", "provider", "temperature", "max_tokens"}
                    kwargs = {k: v for k, v in request.items() if k not in known_keys}

                    response = self.llm_manager.generate_completion(
                        messages=request.get("messages", []),
                        provider_name=request.get("provider"),
                        temperature=request.get("temperature", 0.1),
                        max_tokens=request.get("max_tokens"),
                        model=request.get("model"),
                        **kwargs
                    )
                else:
                    response = self.llm_manager.complete(request)

                # Check if the returned value is awaitable and await if needed
                if asyncio.iscoroutine(response):
                    response = await response

            return response

        except Exception as e:
            logger.warning("LLM completion failed: %s", e)
            return None

    def create_request(
        self,
        system_prompt: str,
        user_prompt: str,
        provider: str | None = None,
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> dict[str, Any]:
        """Create a standardized LLM request.
        
        Args:
            system_prompt: System message content
            user_prompt: User message content
            provider: Provider name (optional)
            model: Model name (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Standardized request dictionary
        """
        request = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if provider:
            request["provider"] = provider
        elif hasattr(self.llm_manager, "default_provider"):
            request["provider"] = self.llm_manager.default_provider

        if model:
            request["model"] = model

        return request
