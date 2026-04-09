"""Claude adapter using the Anthropic SDK.

Wraps anthropic.AsyncAnthropic for the LLMAdapter interface.

Supports Anthropic prompt caching via ``cache_control`` on static system blocks.
Callers can pass a ``system`` kwarg as either:

* A plain string (no caching — compatible with old call sites).
* A list of system blocks, e.g.:
  ``[{"type": "text", "text": "...theme spec...", "cache_control": {"type": "ephemeral"}}]``
  These blocks are forwarded to the Anthropic API unchanged, which activates
  prompt caching and reduces input tokens on a cache hit to ~10% of normal
  pricing (5-minute TTL by default).

Use :func:`build_cached_system` to build a correctly-shaped cached system block
from one or more static strings.
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


def build_cached_system(
    *blocks: str,
    cache_last: bool = True,
) -> list[dict[str, Any]]:
    """Build a list of Anthropic system blocks with prompt caching enabled.

    Pass one or more long, *stable* strings (theme definitions, IR schema docs,
    few-shot examples). Only the LAST block gets a ``cache_control`` marker,
    which is Anthropic's recommended pattern — everything before the last
    marker is cached up to that point.

    Args:
        *blocks: One or more string blocks to include in the system prompt.
                Should be stable/static content that benefits from caching.
        cache_last: If True (default), attach ``cache_control`` to the final
                   block. Set False to disable caching (useful in tests).

    Returns:
        A list of system blocks suitable for ``messages.create(system=...)``.

    Example:
        >>> blocks = build_cached_system(THEME_SPEC, IR_SCHEMA_DOCS)
        >>> resp = await client.messages.create(system=blocks, ...)
    """
    if not blocks:
        return []

    result: list[dict[str, Any]] = []
    for i, text in enumerate(blocks):
        block: dict[str, Any] = {"type": "text", "text": text}
        if cache_last and i == len(blocks) - 1:
            block["cache_control"] = {"type": "ephemeral"}
        result.append(block)
    return result


def _extract_system_and_messages(
    messages: list[dict[str, Any]],
    system_override: Any | None,
) -> tuple[Any | None, list[dict[str, Any]]]:
    """Separate system messages from user/assistant messages.

    If ``system_override`` is provided, it wins (string or list of blocks).
    Otherwise, any ``role="system"`` entries in ``messages`` are concatenated
    into a plain string (no caching — callers must opt in via ``system=``).
    """
    if system_override is not None:
        non_system = [m for m in messages if m.get("role") != "system"]
        return system_override, non_system

    system_parts: list[str] = []
    non_system: list[dict[str, Any]] = []
    for msg in messages:
        if msg.get("role") == "system":
            system_parts.append(str(msg.get("content", "")))
        else:
            non_system.append(msg)

    system_value: Any | None = "\n\n".join(system_parts) if system_parts else None
    return system_value, non_system


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
        system: str | list[dict[str, Any]] | None = None,
    ) -> CompletionResponse:
        """Send messages to Claude and return a standardized response.

        If ``system`` is a list of blocks with ``cache_control`` markers, the
        Anthropic API will apply prompt caching to the static prefix.
        """
        model = model or DEFAULT_MODEL
        system_value, user_messages = _extract_system_and_messages(messages, system)
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": user_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_value is not None:
            kwargs["system"] = system_value
        try:
            response = await self._client.messages.create(**kwargs)
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
        system: str | list[dict[str, Any]] | None = None,
    ) -> BaseModel:
        """Use Claude tool_use to return a validated Pydantic model."""
        model = model or DEFAULT_MODEL
        schema = self._schema_from_model(response_model)
        system_value, user_messages = _extract_system_and_messages(messages, system)

        tool = {
            "name": "structured_output",
            "description": f"Return a structured {response_model.__name__} response.",
            "input_schema": schema,
        }

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": user_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "tools": [tool],
            "tool_choice": {"type": "tool", "name": "structured_output"},
        }
        if system_value is not None:
            kwargs["system"] = system_value

        try:
            response = await self._client.messages.create(**kwargs)
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
        system: str | list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion chunks from Claude."""
        model = model or DEFAULT_MODEL
        system_value, user_messages = _extract_system_and_messages(messages, system)
        stream_kwargs: dict[str, Any] = {
            "model": model,
            "messages": user_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_value is not None:
            stream_kwargs["system"] = system_value
        async with self._client.messages.stream(**stream_kwargs) as stream:
            async for event in stream:
                if hasattr(event, "delta") and hasattr(event.delta, "text"):
                    yield StreamChunk(content=event.delta.text)
            yield StreamChunk(content="", finish_reason="end_turn")
