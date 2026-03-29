"""Claude adapter using the Anthropic SDK.

Wraps anthropic.AsyncAnthropic for the LLMAdapter interface.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import anthropic
from pydantic import BaseModel

from deckforge.llm.base import LLMAdapter
from deckforge.llm.models import (
    CompletionResponse,
    LLMUsage,
    RateLimitError,
    ServiceUnavailableError,
    StreamChunk,
)

DEFAULT_MODEL = "claude-sonnet-4-20250514"


class ClaudeAdapter(LLMAdapter):
    """LLM adapter for Anthropic Claude models."""

    def __init__(self, api_key: str) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        response_format: dict[str, Any] | None = None,
    ) -> CompletionResponse:
        """Send messages to Claude and return a standardized response."""
        model = model or DEFAULT_MODEL
        try:
            response = await self._client.messages.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except anthropic.RateLimitError as exc:
            raise RateLimitError(str(exc)) from exc
        except anthropic.APIStatusError as exc:
            if exc.status_code in (500, 503):
                raise ServiceUnavailableError(str(exc)) from exc
            raise

        # Extract text from content blocks
        text_parts = [
            block.text for block in response.content if block.type == "text"
        ]
        content = "".join(text_parts)

        return CompletionResponse(
            content=content,
            model=response.model,
            usage=LLMUsage(
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            ),
            finish_reason=response.stop_reason or "unknown",
        )

    async def complete_structured(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        *,
        response_model: type[BaseModel],
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> BaseModel:
        """Use Claude tool_use to return a validated Pydantic model."""
        model = model or DEFAULT_MODEL
        schema = self._schema_from_model(response_model)

        tool = {
            "name": "structured_output",
            "description": f"Return a structured {response_model.__name__} response.",
            "input_schema": schema,
        }

        try:
            response = await self._client.messages.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                tools=[tool],
                tool_choice={"type": "tool", "name": "structured_output"},
            )
        except anthropic.RateLimitError as exc:
            raise RateLimitError(str(exc)) from exc
        except anthropic.APIStatusError as exc:
            if exc.status_code in (500, 503):
                raise ServiceUnavailableError(str(exc)) from exc
            raise

        # Find the tool_use content block
        for block in response.content:
            if block.type == "tool_use" and block.name == "structured_output":
                return response_model.model_validate(block.input)

        raise ValueError("No structured_output tool_use block in response")

    async def stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion chunks from Claude."""
        model = model or DEFAULT_MODEL
        async with self._client.messages.stream(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        ) as stream:
            async for event in stream:
                if hasattr(event, "delta") and hasattr(event.delta, "text"):
                    yield StreamChunk(content=event.delta.text)
            yield StreamChunk(content="", finish_reason="end_turn")
