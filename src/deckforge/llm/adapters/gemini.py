"""Gemini adapter using the google-generativeai SDK.

Wraps google.generativeai for the LLMAdapter interface.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import google.generativeai as genai
from pydantic import BaseModel

# Import exception types for error mapping.
# google-generativeai raises google.api_core.exceptions on HTTP errors.
try:
    from google.api_core.exceptions import (
        InternalServerError as _InternalServerError,
        ResourceExhausted as _ResourceExhausted,
        ServiceUnavailable as _ServiceUnavailable,
    )

    resource_exhausted_exc: type[Exception] = _ResourceExhausted
    server_error_exc: type[Exception] = _InternalServerError
    _service_unavailable_exc: type[Exception] = _ServiceUnavailable
except ImportError:  # pragma: no cover
    # Fallback for environments where google-api-core is not installed
    resource_exhausted_exc = type("ResourceExhausted", (Exception,), {})
    server_error_exc = type("InternalServerError", (Exception,), {})
    _service_unavailable_exc = type("ServiceUnavailable", (Exception,), {})

from deckforge.llm.base import LLMAdapter
from deckforge.llm.models import (
    CompletionResponse,
    LLMUsage,
    RateLimitError,
    ServiceUnavailableError,
    StreamChunk,
)

DEFAULT_MODEL = "gemini-2.0-flash"


class GeminiAdapter(LLMAdapter):
    """LLM adapter for Google Gemini models."""

    def __init__(self, api_key: str, model_name: str | None = None) -> None:
        genai.configure(api_key=api_key)
        self._default_model = model_name or DEFAULT_MODEL
        self._api_key = api_key

    def _get_model(self, model: str | None) -> Any:
        """Create a GenerativeModel instance for the given model name."""
        return genai.GenerativeModel(model or self._default_model)

    def _convert_messages(self, messages: list[dict[str, str]]) -> list[dict[str, Any]]:
        """Convert OpenAI-style messages to Gemini format."""
        contents: list[dict[str, Any]] = []
        for msg in messages:
            role = "user" if msg["role"] in ("user", "system") else "model"
            contents.append({"role": role, "parts": [msg["content"]]})
        return contents

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        response_format: dict[str, Any] | None = None,
    ) -> CompletionResponse:
        """Send messages to Gemini and return a standardized response."""
        gmodel = self._get_model(model)
        contents = self._convert_messages(messages)

        generation_config: dict[str, Any] = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        try:
            response = await gmodel.generate_content_async(
                contents,
                generation_config=generation_config,
            )
        except resource_exhausted_exc as exc:
            raise RateLimitError(str(exc)) from exc
        except (server_error_exc, _service_unavailable_exc) as exc:
            raise ServiceUnavailableError(str(exc)) from exc

        # Extract usage metadata
        usage_meta = response.usage_metadata
        prompt_tokens = getattr(usage_meta, "prompt_token_count", 0)
        completion_tokens = getattr(usage_meta, "candidates_token_count", 0)

        # Extract finish reason
        finish_reason = "unknown"
        if response.candidates:
            fr = response.candidates[0].finish_reason
            finish_reason = fr.name if hasattr(fr, "name") else str(fr)

        return CompletionResponse(
            content=response.text,
            model=model or self._default_model,
            usage=LLMUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            finish_reason=finish_reason,
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
        """Use Gemini response_schema to return a validated Pydantic model."""
        gmodel = self._get_model(model)
        contents = self._convert_messages(messages)
        schema = self._schema_from_model(response_model)

        generation_config: dict[str, Any] = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
            "response_mime_type": "application/json",
            "response_schema": schema,
        }

        try:
            response = await gmodel.generate_content_async(
                contents,
                generation_config=generation_config,
            )
        except resource_exhausted_exc as exc:
            raise RateLimitError(str(exc)) from exc
        except (server_error_exc, _service_unavailable_exc) as exc:
            raise ServiceUnavailableError(str(exc)) from exc

        parsed = json.loads(response.text)
        return response_model.model_validate(parsed)

    async def stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion chunks from Gemini."""
        gmodel = self._get_model(model)
        contents = self._convert_messages(messages)

        generation_config: dict[str, Any] = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        try:
            response = await gmodel.generate_content_async(
                contents,
                generation_config=generation_config,
                stream=True,
            )
        except resource_exhausted_exc as exc:
            raise RateLimitError(str(exc)) from exc
        except (server_error_exc, _service_unavailable_exc) as exc:
            raise ServiceUnavailableError(str(exc)) from exc

        async for chunk in response:
            yield StreamChunk(content=chunk.text)
        yield StreamChunk(content="", finish_reason="stop")
