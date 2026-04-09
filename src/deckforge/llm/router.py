"""LLM router with model-prefix dispatch, tier routing, and fallback chains.

Routes requests to the correct provider adapter based on:

1. **Explicit model** (``model="claude-sonnet-4..."``) — prefix match.
2. **Tier** (``tier="starter"``) — picks the cheapest model for that tier,
   see :data:`TIER_MODEL_MAP`.
3. **Default** — first provider in the fallback chain.

Falls back through a configurable chain on rate limit or service errors. When
a tier's primary model is unavailable (provider not configured), steps down
to the next tier's model.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from enum import Enum
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


class LLMTier(str, Enum):
    """Customer tier — drives model selection for cost optimization.

    * ``starter``    -> Gemini Flash 2.0 (cheapest, good quality)
    * ``pro``        -> Claude Sonnet (balanced, default)
    * ``enterprise`` -> Claude Opus (best quality)
    * ``byok``       -> user-provided config (no routing override)
    """

    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    BYOK = "byok"


# Primary model per tier. On miss, we cascade through the fallback tiers
# in ``_TIER_FALLBACK_ORDER`` to pick the next-best supported provider.
TIER_MODEL_MAP: dict[LLMTier, str] = {
    LLMTier.STARTER: "gemini-2.0-flash",
    LLMTier.PRO: "claude-sonnet-4-20250514",
    LLMTier.ENTERPRISE: "claude-opus-4-20250514",
    LLMTier.BYOK: "claude-sonnet-4-20250514",  # default for byok
}

# Approximate USD cost per 1M tokens (input) — used for Pino-style logging.
# Numbers reflect April 2026 published rates.
_TIER_COST_PER_MTOK: dict[LLMTier, float] = {
    LLMTier.STARTER: 0.10,  # gemini flash
    LLMTier.PRO: 3.00,  # claude sonnet
    LLMTier.ENTERPRISE: 15.00,  # claude opus
    LLMTier.BYOK: 3.00,  # assume sonnet-class
}

# When a tier's primary model isn't available, cascade in this order.
_TIER_FALLBACK_ORDER: list[LLMTier] = [
    LLMTier.STARTER,
    LLMTier.PRO,
    LLMTier.ENTERPRISE,
]

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

    def resolve_tier_model(self, tier: LLMTier | str) -> str:
        """Return the best available model for a given customer tier.

        If the tier's primary provider is not configured, cascades through
        adjacent tiers in ``_TIER_FALLBACK_ORDER``. Raises ``AllProvidersFailedError``
        if no tier's primary provider is available.
        """
        if isinstance(tier, str):
            tier = LLMTier(tier)

        primary_model = TIER_MODEL_MAP[tier]
        primary_provider = self._provider_for_model(primary_model)
        if primary_provider in self._adapters:
            return primary_model

        logger.warning(
            "Tier %s primary provider %s unavailable, stepping down",
            tier.value,
            primary_provider,
        )

        # Cascade: try each tier in the fallback order
        try:
            start_idx = _TIER_FALLBACK_ORDER.index(tier)
        except ValueError:
            start_idx = 0
        for next_tier in _TIER_FALLBACK_ORDER[start_idx + 1 :]:
            candidate = TIER_MODEL_MAP[next_tier]
            if self._provider_for_model(candidate) in self._adapters:
                return candidate
        # Final safety net: if nothing matched, try cheaper haiku on claude
        if "claude" in self._adapters:
            return "claude-haiku-4-20250514"
        # Otherwise return whatever the first provider in the chain is
        raise AllProvidersFailedError(
            f"No provider available for tier={tier.value} "
            f"(configured providers: {sorted(self._adapters.keys())})"
        )

    @staticmethod
    def _provider_for_model(model: str) -> str:
        """Return the provider key (e.g. 'claude', 'gemini') for a model name."""
        model_lower = model.lower()
        for prefix, provider in _PREFIX_MAP.items():
            if model_lower.startswith(prefix):
                return provider
        return "claude"  # safe default

    def _apply_tier(
        self, model: str | None, tier: LLMTier | str | None
    ) -> str | None:
        """If ``tier`` is set and no explicit model, resolve via tier routing.

        Logs estimated cost per request for observability (matches Pino-style
        structured logging in the rest of the platform).
        """
        if tier is None:
            return model
        if isinstance(tier, str):
            try:
                tier = LLMTier(tier)
            except ValueError:
                logger.warning("Unknown tier %r, ignoring", tier)
                return model
        if tier == LLMTier.BYOK or model is not None:
            # BYOK respects explicit config; explicit model always wins
            return model
        chosen = self.resolve_tier_model(tier)
        logger.info(
            "llm.tier_route tier=%s model=%s cost_per_mtok_usd=%.2f",
            tier.value,
            chosen,
            _TIER_COST_PER_MTOK[tier],
        )
        return chosen

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
        *,
        tier: LLMTier | str | None = None,
        **kwargs: Any,
    ) -> CompletionResponse:
        """Route a completion request with fallback on transient errors.

        If ``tier`` is provided and ``model`` is None, the model is resolved
        via :meth:`resolve_tier_model`. Explicit ``model`` always wins.
        """
        model = self._apply_tier(model, tier)
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
        tier: LLMTier | str | None = None,
        **kwargs: Any,
    ) -> BaseModel:
        """Route a structured completion request with fallback on transient errors."""
        model = self._apply_tier(model, tier)
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
        *,
        tier: LLMTier | str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Route a streaming request (no mid-stream fallback)."""
        model = self._apply_tier(model, tier)
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
