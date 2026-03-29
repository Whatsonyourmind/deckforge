"""Abstract base class for LLM provider adapters.

All provider adapters inherit from LLMAdapter and implement:
- complete() for single-shot completions
- complete_structured() for Pydantic-validated structured output
- stream() for streaming completions
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel

from deckforge.llm.models import CompletionResponse, StreamChunk


class LLMAdapter(ABC):
    """Protocol for all LLM provider adapters."""

    @abstractmethod
    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        response_format: dict[str, Any] | None = None,
    ) -> CompletionResponse:
        """Send messages and receive a single completion response."""
        ...

    @abstractmethod
    async def complete_structured(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        *,
        response_model: type[BaseModel],
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> BaseModel:
        """Send messages and receive a validated Pydantic model."""
        ...

    @abstractmethod
    async def stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion chunks."""
        ...

    @staticmethod
    def _schema_from_model(response_model: type[BaseModel]) -> dict[str, Any]:
        """Extract JSON Schema dict from a Pydantic model class."""
        return response_model.model_json_schema()
