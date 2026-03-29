"""LLM data models and error types.

Shared types used across all provider adapters and the router.
"""

from __future__ import annotations

from pydantic import BaseModel


class LLMUsage(BaseModel):
    """Token usage statistics from an LLM completion."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class CompletionResponse(BaseModel):
    """Standardized response from any LLM provider."""

    content: str
    model: str
    usage: LLMUsage
    finish_reason: str


class StreamChunk(BaseModel):
    """A single chunk from a streaming LLM response."""

    content: str
    finish_reason: str | None = None


class LLMConfig(BaseModel):
    """Configuration for an LLM provider connection.

    Used to override defaults (e.g., BYO API key).
    """

    provider: str
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None


# ---------------------------------------------------------------------------
# Error hierarchy
# ---------------------------------------------------------------------------


class LLMError(Exception):
    """Base exception for all LLM-related errors."""


class RateLimitError(LLMError):
    """Raised when the provider returns a 429 rate-limit response."""


class ServiceUnavailableError(LLMError):
    """Raised when the provider returns a 500/503 server error."""


class AllProvidersFailedError(LLMError):
    """Raised when every provider in the fallback chain has failed."""
