"""Tests for LLM router with fallback chains, BYO key support, config integration.

Uses MockAdapter instances -- no real API calls.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import patch

import pytest
from pydantic import BaseModel

from deckforge.llm.base import LLMAdapter
from deckforge.llm.models import (
    AllProvidersFailedError,
    CompletionResponse,
    LLMConfig,
    LLMUsage,
    RateLimitError,
    ServiceUnavailableError,
    StreamChunk,
)
from deckforge.llm.router import LLMRouter, create_router


# ---------------------------------------------------------------------------
# Mock adapter for testing
# ---------------------------------------------------------------------------


class MockAdapter(LLMAdapter):
    """Test adapter that can be configured to succeed or raise specific errors."""

    def __init__(
        self,
        name: str = "mock",
        *,
        fail_with: type[Exception] | None = None,
        response_content: str = "mock response",
    ) -> None:
        self.name = name
        self._fail_with = fail_with
        self._response_content = response_content
        self.call_count = 0

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        response_format: dict[str, Any] | None = None,
    ) -> CompletionResponse:
        self.call_count += 1
        if self._fail_with:
            raise self._fail_with(f"{self.name} failed")
        return CompletionResponse(
            content=self._response_content,
            model=model or "mock-model",
            usage=LLMUsage(prompt_tokens=5, completion_tokens=3, total_tokens=8),
            finish_reason="stop",
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
        self.call_count += 1
        if self._fail_with:
            raise self._fail_with(f"{self.name} failed")
        # Return a generic valid model instance
        fields = {name: "test" for name in response_model.model_fields}
        return response_model.model_validate(fields)

    async def stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> AsyncIterator[StreamChunk]:
        self.call_count += 1
        if self._fail_with:
            raise self._fail_with(f"{self.name} failed")
        yield StreamChunk(content="chunk", finish_reason="stop")


# ---------------------------------------------------------------------------
# Test model
# ---------------------------------------------------------------------------


class SimpleResponse(BaseModel):
    answer: str


# ===========================================================================
# LLMRouter tests
# ===========================================================================


MESSAGES = [{"role": "user", "content": "Hello"}]


class TestLLMRouterRouting:
    """Tests that the router dispatches to the correct adapter by model prefix."""

    def _make_router(self) -> tuple[LLMRouter, dict[str, MockAdapter]]:
        adapters = {
            "claude": MockAdapter("claude", response_content="from claude"),
            "openai": MockAdapter("openai", response_content="from openai"),
            "gemini": MockAdapter("gemini", response_content="from gemini"),
        }
        router = LLMRouter(
            adapters=adapters,
            fallback_chain=["claude", "openai", "gemini"],
        )
        return router, adapters

    @pytest.mark.asyncio
    async def test_routes_claude_model_to_claude_adapter(self):
        router, adapters = self._make_router()
        result = await router.complete(MESSAGES, model="claude-sonnet-4-20250514")

        assert result.content == "from claude"
        assert adapters["claude"].call_count == 1
        assert adapters["openai"].call_count == 0

    @pytest.mark.asyncio
    async def test_routes_gpt_model_to_openai_adapter(self):
        router, adapters = self._make_router()
        result = await router.complete(MESSAGES, model="gpt-4o")

        assert result.content == "from openai"
        assert adapters["openai"].call_count == 1

    @pytest.mark.asyncio
    async def test_routes_gemini_model_to_gemini_adapter(self):
        router, adapters = self._make_router()
        result = await router.complete(MESSAGES, model="gemini-2.0-flash")

        assert result.content == "from gemini"
        assert adapters["gemini"].call_count == 1

    @pytest.mark.asyncio
    async def test_routes_unknown_model_to_first_in_fallback_chain(self):
        router, adapters = self._make_router()
        result = await router.complete(MESSAGES, model="unknown-model-v1")

        assert result.content == "from claude"
        assert adapters["claude"].call_count == 1


class TestLLMRouterFallback:
    """Tests that the router falls back correctly on RateLimitError and ServiceUnavailableError."""

    @pytest.mark.asyncio
    async def test_falls_back_on_rate_limit_error(self):
        adapters = {
            "claude": MockAdapter("claude", fail_with=RateLimitError),
            "openai": MockAdapter("openai", response_content="fallback openai"),
        }
        router = LLMRouter(adapters=adapters, fallback_chain=["claude", "openai"])

        result = await router.complete(MESSAGES)
        assert result.content == "fallback openai"
        assert adapters["claude"].call_count == 1
        assert adapters["openai"].call_count == 1

    @pytest.mark.asyncio
    async def test_falls_back_on_service_unavailable_error(self):
        adapters = {
            "claude": MockAdapter("claude", fail_with=ServiceUnavailableError),
            "openai": MockAdapter("openai", response_content="fallback openai"),
        }
        router = LLMRouter(adapters=adapters, fallback_chain=["claude", "openai"])

        result = await router.complete(MESSAGES)
        assert result.content == "fallback openai"

    @pytest.mark.asyncio
    async def test_raises_all_providers_failed_when_all_fail(self):
        adapters = {
            "claude": MockAdapter("claude", fail_with=RateLimitError),
            "openai": MockAdapter("openai", fail_with=ServiceUnavailableError),
            "gemini": MockAdapter("gemini", fail_with=RateLimitError),
        }
        router = LLMRouter(
            adapters=adapters, fallback_chain=["claude", "openai", "gemini"]
        )

        with pytest.raises(AllProvidersFailedError):
            await router.complete(MESSAGES)

    @pytest.mark.asyncio
    async def test_complete_structured_routes_and_falls_back(self):
        adapters = {
            "claude": MockAdapter("claude", fail_with=RateLimitError),
            "openai": MockAdapter("openai"),
        }
        router = LLMRouter(adapters=adapters, fallback_chain=["claude", "openai"])

        result = await router.complete_structured(
            MESSAGES, response_model=SimpleResponse
        )
        assert isinstance(result, SimpleResponse)
        assert adapters["claude"].call_count == 1
        assert adapters["openai"].call_count == 1


# ===========================================================================
# create_router() tests
# ===========================================================================


class TestCreateRouter:
    """Tests for create_router() factory with BYO key and settings defaults."""

    @pytest.mark.asyncio
    async def test_byo_key_creates_adapter_with_user_key(self):
        """create_router() with LLMConfig(api_key=...) creates adapter with user's key."""
        config = LLMConfig(provider="claude", api_key="user-sk-123")

        with patch("deckforge.llm.router.ClaudeAdapter") as MockClaude:
            mock_instance = MockAdapter("claude")
            MockClaude.return_value = mock_instance

            router = create_router(llm_config=config)
            MockClaude.assert_called_once_with(api_key="user-sk-123")
            assert "claude" in router._adapters

    @pytest.mark.asyncio
    async def test_ollama_custom_base_url(self):
        """create_router() with Ollama provider uses custom base_url."""
        config = LLMConfig(provider="ollama", base_url="http://custom:11434")

        with patch("deckforge.llm.router.OllamaAdapter") as MockOllama:
            mock_instance = MockAdapter("ollama")
            MockOllama.return_value = mock_instance

            router = create_router(llm_config=config)
            MockOllama.assert_called_once_with(base_url="http://custom:11434")

    @pytest.mark.asyncio
    async def test_no_config_uses_settings_defaults(self):
        """create_router() without LLMConfig uses settings defaults and full fallback chain."""
        mock_settings = type(
            "MockSettings",
            (),
            {
                "ANTHROPIC_API_KEY": "default-anthropic",
                "OPENAI_API_KEY": "default-openai",
                "GEMINI_API_KEY": None,
                "OLLAMA_BASE_URL": "http://localhost:11434",
                "LLM_DEFAULT_PROVIDER": "claude",
                "LLM_FALLBACK_CHAIN": "claude,openai",
                "llm_fallback_list": ["claude", "openai"],
            },
        )()

        with (
            patch("deckforge.llm.router.ClaudeAdapter") as MockClaude,
            patch("deckforge.llm.router.OpenAIAdapter") as MockOpenAI,
        ):
            MockClaude.return_value = MockAdapter("claude")
            MockOpenAI.return_value = MockAdapter("openai")

            router = create_router(settings=mock_settings)

            MockClaude.assert_called_once_with(api_key="default-anthropic")
            MockOpenAI.assert_called_once_with(api_key="default-openai")
            assert router._fallback_chain == ["claude", "openai"]


# ===========================================================================
# Settings integration tests
# ===========================================================================


class TestSettingsLLMFields:
    """Tests that Settings includes all required LLM fields."""

    def test_settings_has_llm_fields(self):
        from deckforge.config import Settings

        s = Settings()
        assert hasattr(s, "LLM_DEFAULT_PROVIDER")
        assert hasattr(s, "LLM_FALLBACK_CHAIN")
        assert hasattr(s, "ANTHROPIC_API_KEY")
        assert hasattr(s, "OPENAI_API_KEY")
        assert hasattr(s, "GEMINI_API_KEY")
        assert hasattr(s, "OLLAMA_BASE_URL")

    def test_settings_llm_defaults(self):
        from deckforge.config import Settings

        s = Settings()
        assert s.LLM_DEFAULT_PROVIDER == "claude"
        assert s.LLM_FALLBACK_CHAIN == "claude,openai,gemini"
        assert s.OLLAMA_BASE_URL == "http://localhost:11434"

    def test_settings_llm_fallback_list(self):
        from deckforge.config import Settings

        s = Settings()
        assert s.llm_fallback_list == ["claude", "openai", "gemini"]
