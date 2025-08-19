"""
OpenAI GPT provider implementation.
"""

from typing import Any

from autopr.actions.llm.base import BaseLLMProvider
from autopr.actions.llm.types import LLMResponse


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider."""

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        try:
            import openai

            self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
            self.available = True
        except ImportError:
            self.available = False

    def complete(self, request: dict[str, Any]) -> LLMResponse:
        try:
            # Ensure all messages have non-empty content (additional robustness)
            filtered_messages = [msg for msg in request["messages"] if msg["content"].strip()]
            response = self.client.chat.completions.create(
                model=request["model"] or self.default_model or "gpt-4",
                messages=filtered_messages,
                temperature=request.get("temperature", 0.7),
                max_tokens=request.get("max_tokens"),
                top_p=request.get("top_p", 1.0),
                frequency_penalty=request.get("frequency_penalty", 0.0),
                presence_penalty=request.get("presence_penalty", 0.0),
                stop=request.get("stop"),
            )

            # Defensive: ensure response has expected attributes
            if hasattr(response, "choices") and hasattr(response.choices[0], "message"):
                content = response.choices[0].message.content or ""
                finish_reason = getattr(response.choices[0], "finish_reason", "stop") or "stop"
            else:
                content = ""
                finish_reason = "stop"

            model = getattr(
                response, "model", request.get("model") or self.default_model or "gpt-4"
            )
            usage = (
                response.usage.dict()
                if hasattr(response, "usage") and response.usage is not None
                else None
            )

            return LLMResponse(
                content=str(content),
                model=str(model),
                finish_reason=str(finish_reason),
                usage=usage,
            )
        except Exception as e:
            return LLMResponse.from_error(
                str(e), request.get("model") or self.default_model or "gpt-4"
            )

    def is_available(self) -> bool:
        return self.available and bool(self.api_key)
