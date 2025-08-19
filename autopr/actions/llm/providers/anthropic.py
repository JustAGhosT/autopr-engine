"""
Anthropic Claude provider implementation.
"""

from typing import Any

from autopr.actions.llm.base import BaseLLMProvider
from autopr.actions.llm.types import LLMResponse


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        try:
            import anthropic

            self.client = anthropic.Anthropic(api_key=self.api_key, base_url=self.base_url)
            self.available = True
        except ImportError:
            self.available = False

    def complete(self, request: dict[str, Any]) -> LLMResponse:
        try:
            messages = request.get("messages", [])
            model = request.get("model", self.default_model) or "claude-3-sonnet-20240229"
            max_tokens = request.get("max_tokens", 1024)
            temperature = request.get("temperature", 0.7)

            # Convert messages to Anthropic format
            system_prompt = ""
            converted_messages: list[dict[str, str]] = []

            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if not content:
                    continue

                if role == "system":
                    system_prompt += content + "\n"
                else:
                    converted_messages.append({"role": role, "content": content})

            # Prepare system parameter - use NotGiven if empty
            system_param = system_prompt.strip() or None

            # Call the API
            if system_param:
                response = self.client.messages.create(
                    model=str(model),
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_param,
                    messages=converted_messages,  # type: ignore[arg-type]
                )
            else:
                response = self.client.messages.create(
                    model=str(model),
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=converted_messages,  # type: ignore[arg-type]
                )

            # Extract content and finish reason
            content = ""
            if hasattr(response, "content") and response.content:
                content = "\n".join(
                    block.text for block in response.content if hasattr(block, "text")
                )

            finish_reason = getattr(response, "stop_reason", "stop")
            usage = {
                "prompt_tokens": getattr(response, "usage", {}).get("input_tokens", 0),
                "completion_tokens": getattr(response, "usage", {}).get("output_tokens", 0),
                "total_tokens": getattr(response, "usage", {}).get("input_tokens", 0)
                + getattr(response, "usage", {}).get("output_tokens", 0),
            }

            return LLMResponse(
                content=content,
                model=str(model),
                finish_reason=finish_reason,
                usage=usage,
            )

        except Exception as e:
            return LLMResponse.from_error(
                f"Error calling Anthropic API: {e!s}",
                str(request.get("model") or "claude-3-sonnet-20240229"),
            )

    def is_available(self) -> bool:
        return self.available and bool(self.api_key)
