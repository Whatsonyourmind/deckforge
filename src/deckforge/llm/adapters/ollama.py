"""Ollama adapter using httpx REST calls.

Communicates with the Ollama REST API at /api/chat.
No external SDK dependency -- uses httpx which is already in the project.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from deckforge.llm.base import LLMAdapter
from deckforge.llm.models import (
    CompletionResponse,
    LLMUsage,
    RateLimitError,
    ServiceUnavailableError,
    StreamChunk,
)

DEFAULT_MODEL = "llama3.1:8b"
MAX_STRUCTURED_RETRIES = 3


class OllamaAdapter(LLMAdapter):
    """LLM adapter for Ollama (local LLM server) via REST API."""

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self._base_url = base_url
        self._client = httpx.AsyncClient(base_url=base_url, timeout=120.0)

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        response_format: dict[str, Any] | None = None,
    ) -> CompletionResponse:
        """Send messages to Ollama and return a standardized response."""
        model = model or DEFAULT_MODEL
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if response_format is not None:
            payload["format"] = response_format

        response = await self._client.post("/api/chat", json=payload)

        if response.status_code == 429:
            raise RateLimitError("Ollama rate limit exceeded")
        if response.status_code in (500, 503):
            raise ServiceUnavailableError(
                f"Ollama server error: {response.status_code}"
            )

        data = response.json()
        message_content = data.get("message", {}).get("content", "")

        return CompletionResponse(
            content=message_content,
            model=data.get("model", model),
            usage=LLMUsage(
                prompt_tokens=data.get("prompt_eval_count", 0),
                completion_tokens=data.get("eval_count", 0),
                total_tokens=(
                    data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                ),
            ),
            finish_reason="stop" if data.get("done") else "unknown",
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
        """Send messages to Ollama with JSON format, validate against response_model.

        Retries up to MAX_STRUCTURED_RETRIES times on ValidationError,
        appending error feedback to messages for self-correction.
        """
        model = model or DEFAULT_MODEL
        working_messages = list(messages)

        for attempt in range(MAX_STRUCTURED_RETRIES):
            result = await self.complete(
                working_messages,
                model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format="json",
            )

            try:
                parsed = json.loads(result.content)
                return response_model.model_validate(parsed)
            except (json.JSONDecodeError, ValidationError) as exc:
                if attempt == MAX_STRUCTURED_RETRIES - 1:
                    raise
                # Append error feedback for self-correction
                working_messages.append(
                    {"role": "assistant", "content": result.content}
                )
                working_messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"Your response had validation errors: {exc}. "
                            f"Please fix and return valid JSON matching the schema."
                        ),
                    }
                )

        # Should not reach here, but satisfy type checker
        raise RuntimeError("Exhausted retry attempts")  # pragma: no cover

    async def stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion chunks from Ollama via NDJSON."""
        model = model or DEFAULT_MODEL
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        async with self._client.stream("POST", "/api/chat", json=payload) as response:
            if response.status_code == 429:
                raise RateLimitError("Ollama rate limit exceeded")
            if response.status_code in (500, 503):
                raise ServiceUnavailableError(
                    f"Ollama server error: {response.status_code}"
                )

            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                data = json.loads(line)
                content = data.get("message", {}).get("content", "")
                done = data.get("done", False)
                yield StreamChunk(
                    content=content,
                    finish_reason="stop" if done else None,
                )
