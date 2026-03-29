"""OpenAI adapter using the openai SDK.

Wraps openai.AsyncOpenAI for the LLMAdapter interface.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import openai
from pydantic import BaseModel

from deckforge.llm.base import LLMAdapter
from deckforge.llm.models import (
    CompletionResponse,
    LLMUsage,
    RateLimitError,
    ServiceUnavailableError,
    StreamChunk,
)

DEFAULT_MODEL = "gpt-4o"


class OpenAIAdapter(LLMAdapter):
    """LLM adapter for OpenAI models."""

    def __init__(self, api_key: str) -> None:
        self._client = openai.AsyncOpenAI(api_key=api_key)

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        response_format: dict[str, Any] | None = None,
    ) -> CompletionResponse:
        """Send messages to OpenAI and return a standardized response."""
        model = model or DEFAULT_MODEL
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if response_format is not None:
            kwargs["response_format"] = response_format

        try:
            response = await self._client.chat.completions.create(**kwargs)
        except openai.RateLimitError as exc:
            raise RateLimitError(str(exc)) from exc
        except openai.APIStatusError as exc:
            if exc.status_code in (500, 503):
                raise ServiceUnavailableError(str(exc)) from exc
            raise

        choice = response.choices[0]
        return CompletionResponse(
            content=choice.message.content or "",
            model=response.model,
            usage=LLMUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.prompt_tokens + response.usage.completion_tokens,
            ),
            finish_reason=choice.finish_reason or "unknown",
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
        """Use OpenAI json_schema response_format to return a validated Pydantic model."""
        model = model or DEFAULT_MODEL
        schema = self._schema_from_model(response_model)

        response_format = {
            "type": "json_schema",
            "json_schema": {"name": "response", "schema": schema},
        }

        result = await self.complete(
            messages,
            model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
        )

        parsed = json.loads(result.content)
        return response_model.model_validate(parsed)

    async def stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion chunks from OpenAI."""
        model = model or DEFAULT_MODEL
        try:
            stream = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )
        except openai.RateLimitError as exc:
            raise RateLimitError(str(exc)) from exc
        except openai.APIStatusError as exc:
            if exc.status_code in (500, 503):
                raise ServiceUnavailableError(str(exc)) from exc
            raise

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield StreamChunk(content=chunk.choices[0].delta.content)
            if chunk.choices and chunk.choices[0].finish_reason:
                yield StreamChunk(
                    content="",
                    finish_reason=chunk.choices[0].finish_reason,
                )
