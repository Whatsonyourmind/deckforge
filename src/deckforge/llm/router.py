"""LLM router with model-prefix dispatch and fallback chains.

Routes requests to the correct provider adapter based on model name prefix.
Falls back through a configurable chain on rate limit or service errors.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from deckforge.llm.adapters.claude import ClaudeAdapter
from deckforge.llm.adapters.gemini import GeminiAdapter
from deckforge.llm.adapters.ollama import OllamaAdapter
from deckforge.llm.adapters.openai import OpenAIAdapter
from deckforge.llm.base import LLMAdapter
from deckforge.llm.models import (
    AllProvidersFailedError,
    CompletionResponse,
    LLMConfig,
    RateLimitError,
    ServiceUnavailableError,
    StreamChunk,
)

if TYPE_CHECKING:
    from deckforge.config import Settings

logger = logging.getLogger(__name__)

# Model-prefix to provider mapping
_PREFIX_MAP: dict[str, str] = {
    "claude": "claude",
    "gpt": "openai",
    "gemini": "gemini",
    "llama": "ollama",
    "mistral": "ollama",
    "codellama": "ollama",
}

# Errors that trigger fallback
_FALLBACK_ERRORS = (RateLimitError, ServiceUnavailableError)


class LLMRouter:
    """Routes LLM requests to provider adapters with fallback support.

    Resolves the target provider from the model name prefix, then falls
    back through the chain if the primary provider returns a rate limit
    or service unavailable error.
    """

    def __init__(
        self,
        adapters: dict[str, LLMAdapter],
        fallback_chain: list[str],
    ) -> None:
        self._adapters = adapters
        self._fallback_chain = fallback_chain

    def _resolve_provider(self, model: str | None) -> str:
        """Map a model name to a provider key via prefix matching."""
        if model is None:
            return self._fallback_chain[0]

        model_lower = model.lower()
        for prefix, provider in _PREFIX_MAP.items():
            if model_lower.startswith(prefix):
                if provider in self._adapters:
                    return provider
                break

        # Default to first in fallback chain
        return self._fallback_chain[0]

    def _get_chain(self, primary: str) -> list[str]:
        """Build an ordered chain starting with primary, then remaining fallbacks."""
        chain = [primary]
        for provider in self._fallback_chain:
            if provider != primary and provider in self._adapters:
                chain.append(provider)
        return chain

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        **kwargs: Any,
    ) -> CompletionResponse:
        """Route a completion request with fallback on transient errors."""
        primary = self._resolve_provider(model)
        chain = self._get_chain(primary)
        errors: list[Exception] = []

        for provider_key in chain:
            adapter = self._adapters[provider_key]
            try:
                return await adapter.complete(messages, model=model, **kwargs)
            except _FALLBACK_ERRORS as exc:
                logger.warning(
                    "Provider %s failed with %s, trying next in chain",
                    provider_key,
                    type(exc).__name__,
                )
                errors.append(exc)

        raise AllProvidersFailedError(
            f"All {len(chain)} providers failed: "
            + ", ".join(f"{type(e).__name__}" for e in errors)
        )

    async def complete_structured(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        *,
        response_model: type[BaseModel],
        **kwargs: Any,
    ) -> BaseModel:
        """Route a structured completion request with fallback on transient errors."""
        primary = self._resolve_provider(model)
        chain = self._get_chain(primary)
        errors: list[Exception] = []

        for provider_key in chain:
            adapter = self._adapters[provider_key]
            try:
                return await adapter.complete_structured(
                    messages, model=model, response_model=response_model, **kwargs
                )
            except _FALLBACK_ERRORS as exc:
                logger.warning(
                    "Provider %s failed structured request with %s, trying next",
                    provider_key,
                    type(exc).__name__,
                )
                errors.append(exc)

        raise AllProvidersFailedError(
            f"All {len(chain)} providers failed structured request: "
            + ", ".join(f"{type(e).__name__}" for e in errors)
        )

    async def stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Route a streaming request (no mid-stream fallback)."""
        primary = self._resolve_provider(model)
        adapter = self._adapters.get(primary)
        if adapter is None:
            raise AllProvidersFailedError(f"No adapter for provider: {primary}")

        async for chunk in adapter.stream(messages, model=model, **kwargs):
            yield chunk


def create_router(
    llm_config: LLMConfig | None = None,
    settings: Any | None = None,
) -> LLMRouter:
    """Factory that builds an LLMRouter from config or settings.

    Args:
        llm_config: Optional user-provided config (BYO key). When given,
            creates a single-provider router with the user's key.
        settings: Optional Settings instance. When no llm_config, uses
            settings to build adapters for all providers with configured keys.
    """
    if llm_config is not None:
        # BYO key: create a single adapter for the specified provider
        adapter = _create_adapter(
            provider=llm_config.provider,
            api_key=llm_config.api_key,
            base_url=llm_config.base_url,
        )
        return LLMRouter(
            adapters={llm_config.provider: adapter},
            fallback_chain=[llm_config.provider],
        )

    # Use settings defaults
    if settings is None:
        from deckforge.config import settings as default_settings

        settings = default_settings

    adapters: dict[str, LLMAdapter] = {}
    fallback_chain: list[str] = settings.llm_fallback_list

    # Create adapters for providers with configured keys
    if settings.ANTHROPIC_API_KEY:
        adapters["claude"] = ClaudeAdapter(api_key=settings.ANTHROPIC_API_KEY)
    if settings.OPENAI_API_KEY:
        adapters["openai"] = OpenAIAdapter(api_key=settings.OPENAI_API_KEY)
    if settings.GEMINI_API_KEY:
        adapters["gemini"] = GeminiAdapter(api_key=settings.GEMINI_API_KEY)
    # Ollama is always available (no API key needed)
    adapters["ollama"] = OllamaAdapter(base_url=settings.OLLAMA_BASE_URL)

    return LLMRouter(adapters=adapters, fallback_chain=fallback_chain)


def _create_adapter(
    provider: str,
    api_key: str | None = None,
    base_url: str | None = None,
) -> LLMAdapter:
    """Create a single adapter for the given provider."""
    match provider:
        case "claude":
            if not api_key:
                raise ValueError("Claude adapter requires an API key")
            return ClaudeAdapter(api_key=api_key)
        case "openai":
            if not api_key:
                raise ValueError("OpenAI adapter requires an API key")
            return OpenAIAdapter(api_key=api_key)
        case "gemini":
            if not api_key:
                raise ValueError("Gemini adapter requires an API key")
            return GeminiAdapter(api_key=api_key)
        case "ollama":
            return OllamaAdapter(base_url=base_url or "http://localhost:11434")
        case _:
            raise ValueError(f"Unknown provider: {provider}")
