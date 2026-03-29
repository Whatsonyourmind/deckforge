"""Tests for LLM provider adapters: Claude, OpenAI, Gemini, Ollama.

All tests mock the underlying SDKs -- no real API calls.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from deckforge.llm.models import (
    CompletionResponse,
    LLMConfig,
    LLMUsage,
    RateLimitError,
    ServiceUnavailableError,
)
from deckforge.llm.adapters.claude import ClaudeAdapter
from deckforge.llm.adapters.openai import OpenAIAdapter
from deckforge.llm.adapters.gemini import GeminiAdapter
from deckforge.llm.adapters.ollama import OllamaAdapter


# ---------------------------------------------------------------------------
# Test Pydantic model for complete_structured() tests
# ---------------------------------------------------------------------------


class MovieReview(BaseModel):
    title: str
    rating: float
    summary: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MESSAGES = [{"role": "user", "content": "Hello"}]


# ===========================================================================
# Claude adapter tests
# ===========================================================================


class TestClaudeAdapter:
    """Tests for ClaudeAdapter wrapping the anthropic SDK."""

    @pytest.fixture
    def mock_anthropic(self):
        with patch("deckforge.llm.adapters.claude.anthropic") as mock_mod:
            mock_client = AsyncMock()
            mock_mod.AsyncAnthropic.return_value = mock_client
            # RateLimitError and APIStatusError used for error mapping
            mock_mod.RateLimitError = type("RateLimitError", (Exception,), {})
            mock_mod.APIStatusError = type(
                "APIStatusError",
                (Exception,),
                {"__init__": lambda self, message="", *, status_code=500, response=None, body=None: (
                    setattr(self, "status_code", status_code) or
                    setattr(self, "response", response) or
                    setattr(self, "body", body) or
                    Exception.__init__(self, message)
                )},
            )
            yield mock_mod, mock_client

    @pytest.mark.asyncio
    async def test_complete_returns_completion_response(self, mock_anthropic):
        mock_mod, mock_client = mock_anthropic
        # Build mock response
        mock_response = SimpleNamespace(
            content=[SimpleNamespace(type="text", text="Hello back!")],
            model="claude-sonnet-4-20250514",
            usage=SimpleNamespace(input_tokens=10, output_tokens=5),
            stop_reason="end_turn",
        )
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        adapter = ClaudeAdapter(api_key="test-key")
        result = await adapter.complete(MESSAGES, model="claude-sonnet-4-20250514")

        assert isinstance(result, CompletionResponse)
        assert result.content == "Hello back!"
        assert result.model == "claude-sonnet-4-20250514"
        assert result.usage.prompt_tokens == 10
        assert result.usage.completion_tokens == 5
        assert result.finish_reason == "end_turn"

    @pytest.mark.asyncio
    async def test_complete_structured_returns_validated_model(self, mock_anthropic):
        mock_mod, mock_client = mock_anthropic
        tool_input = {"title": "Inception", "rating": 9.5, "summary": "Mind-bending thriller"}
        mock_response = SimpleNamespace(
            content=[
                SimpleNamespace(type="tool_use", name="structured_output", input=tool_input),
            ],
            model="claude-sonnet-4-20250514",
            usage=SimpleNamespace(input_tokens=20, output_tokens=15),
            stop_reason="tool_use",
        )
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        adapter = ClaudeAdapter(api_key="test-key")
        result = await adapter.complete_structured(
            MESSAGES, model="claude-sonnet-4-20250514", response_model=MovieReview
        )

        assert isinstance(result, MovieReview)
        assert result.title == "Inception"
        assert result.rating == 9.5

    @pytest.mark.asyncio
    async def test_raises_rate_limit_error_on_429(self, mock_anthropic):
        mock_mod, mock_client = mock_anthropic
        mock_client.messages.create = AsyncMock(
            side_effect=mock_mod.RateLimitError("Rate limited")
        )

        adapter = ClaudeAdapter(api_key="test-key")
        with pytest.raises(RateLimitError):
            await adapter.complete(MESSAGES)

    @pytest.mark.asyncio
    async def test_raises_service_unavailable_on_500(self, mock_anthropic):
        mock_mod, mock_client = mock_anthropic
        err = mock_mod.APIStatusError(
            "Server error", status_code=500, response=None, body=None
        )
        mock_client.messages.create = AsyncMock(side_effect=err)

        adapter = ClaudeAdapter(api_key="test-key")
        with pytest.raises(ServiceUnavailableError):
            await adapter.complete(MESSAGES)


# ===========================================================================
# OpenAI adapter tests
# ===========================================================================


class TestOpenAIAdapter:
    """Tests for OpenAIAdapter wrapping the openai SDK."""

    @pytest.fixture
    def mock_openai(self):
        with patch("deckforge.llm.adapters.openai.openai") as mock_mod:
            mock_client = AsyncMock()
            mock_mod.AsyncOpenAI.return_value = mock_client
            mock_mod.RateLimitError = type("RateLimitError", (Exception,), {})
            mock_mod.APIStatusError = type(
                "APIStatusError",
                (Exception,),
                {"__init__": lambda self, message="", *, status_code=500, response=None, body=None: (
                    setattr(self, "status_code", status_code) or
                    setattr(self, "response", response) or
                    setattr(self, "body", body) or
                    Exception.__init__(self, message)
                )},
            )
            yield mock_mod, mock_client

    @pytest.mark.asyncio
    async def test_complete_returns_completion_response(self, mock_openai):
        mock_mod, mock_client = mock_openai
        mock_choice = SimpleNamespace(
            message=SimpleNamespace(content="Hello from GPT!"),
            finish_reason="stop",
        )
        mock_response = SimpleNamespace(
            choices=[mock_choice],
            model="gpt-4o",
            usage=SimpleNamespace(prompt_tokens=8, completion_tokens=6),
        )
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        adapter = OpenAIAdapter(api_key="test-key")
        result = await adapter.complete(MESSAGES, model="gpt-4o")

        assert isinstance(result, CompletionResponse)
        assert result.content == "Hello from GPT!"
        assert result.model == "gpt-4o"
        assert result.usage.prompt_tokens == 8
        assert result.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_complete_structured_returns_validated_model(self, mock_openai):
        mock_mod, mock_client = mock_openai
        json_str = json.dumps({"title": "Matrix", "rating": 9.0, "summary": "Red pill"})
        mock_choice = SimpleNamespace(
            message=SimpleNamespace(content=json_str),
            finish_reason="stop",
        )
        mock_response = SimpleNamespace(
            choices=[mock_choice],
            model="gpt-4o",
            usage=SimpleNamespace(prompt_tokens=15, completion_tokens=12),
        )
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        adapter = OpenAIAdapter(api_key="test-key")
        result = await adapter.complete_structured(
            MESSAGES, model="gpt-4o", response_model=MovieReview
        )

        assert isinstance(result, MovieReview)
        assert result.title == "Matrix"

    @pytest.mark.asyncio
    async def test_raises_rate_limit_error_on_429(self, mock_openai):
        mock_mod, mock_client = mock_openai
        mock_client.chat.completions.create = AsyncMock(
            side_effect=mock_mod.RateLimitError("Rate limited")
        )

        adapter = OpenAIAdapter(api_key="test-key")
        with pytest.raises(RateLimitError):
            await adapter.complete(MESSAGES)

    @pytest.mark.asyncio
    async def test_raises_service_unavailable_on_500(self, mock_openai):
        mock_mod, mock_client = mock_openai
        err = mock_mod.APIStatusError(
            "Server error", status_code=500, response=None, body=None
        )
        mock_client.chat.completions.create = AsyncMock(side_effect=err)

        adapter = OpenAIAdapter(api_key="test-key")
        with pytest.raises(ServiceUnavailableError):
            await adapter.complete(MESSAGES)


# ===========================================================================
# Gemini adapter tests
# ===========================================================================


class TestGeminiAdapter:
    """Tests for GeminiAdapter wrapping google-generativeai SDK."""

    @pytest.fixture
    def mock_genai(self):
        with patch("deckforge.llm.adapters.gemini.genai") as mock_mod:
            mock_model = AsyncMock()
            mock_mod.GenerativeModel.return_value = mock_model
            # Simulate google.api_core.exceptions
            mock_mod._rate_limit_exc = type("ResourceExhausted", (Exception,), {})
            mock_mod._server_exc = type("InternalServerError", (Exception,), {})
            yield mock_mod, mock_model

    @pytest.mark.asyncio
    async def test_complete_returns_completion_response(self, mock_genai):
        mock_mod, mock_model = mock_genai
        mock_response = SimpleNamespace(
            text="Hello from Gemini!",
            usage_metadata=SimpleNamespace(
                prompt_token_count=7, candidates_token_count=5, total_token_count=12
            ),
            candidates=[SimpleNamespace(finish_reason=SimpleNamespace(name="STOP"))],
        )
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)

        adapter = GeminiAdapter(api_key="test-key")
        result = await adapter.complete(MESSAGES, model="gemini-2.0-flash")

        assert isinstance(result, CompletionResponse)
        assert result.content == "Hello from Gemini!"
        assert result.usage.prompt_tokens == 7
        assert result.usage.completion_tokens == 5

    @pytest.mark.asyncio
    async def test_complete_structured_returns_validated_model(self, mock_genai):
        mock_mod, mock_model = mock_genai
        json_str = json.dumps({"title": "Dune", "rating": 8.5, "summary": "Desert epic"})
        mock_response = SimpleNamespace(
            text=json_str,
            usage_metadata=SimpleNamespace(
                prompt_token_count=10, candidates_token_count=8, total_token_count=18
            ),
            candidates=[SimpleNamespace(finish_reason=SimpleNamespace(name="STOP"))],
        )
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)

        adapter = GeminiAdapter(api_key="test-key")
        result = await adapter.complete_structured(
            MESSAGES, model="gemini-2.0-flash", response_model=MovieReview
        )

        assert isinstance(result, MovieReview)
        assert result.title == "Dune"

    @pytest.mark.asyncio
    async def test_raises_rate_limit_error_on_429(self, mock_genai):
        mock_mod, mock_model = mock_genai
        with patch(
            "deckforge.llm.adapters.gemini.resource_exhausted_exc",
            mock_mod._rate_limit_exc,
        ):
            mock_model.generate_content_async = AsyncMock(
                side_effect=mock_mod._rate_limit_exc("Rate limited")
            )
            adapter = GeminiAdapter(api_key="test-key")
            with pytest.raises(RateLimitError):
                await adapter.complete(MESSAGES)

    @pytest.mark.asyncio
    async def test_raises_service_unavailable_on_500(self, mock_genai):
        mock_mod, mock_model = mock_genai
        with patch(
            "deckforge.llm.adapters.gemini.server_error_exc",
            mock_mod._server_exc,
        ):
            mock_model.generate_content_async = AsyncMock(
                side_effect=mock_mod._server_exc("Server error")
            )
            adapter = GeminiAdapter(api_key="test-key")
            with pytest.raises(ServiceUnavailableError):
                await adapter.complete(MESSAGES)


# ===========================================================================
# Ollama adapter tests
# ===========================================================================


class TestOllamaAdapter:
    """Tests for OllamaAdapter using httpx REST calls."""

    @pytest.fixture
    def mock_httpx(self):
        with patch("deckforge.llm.adapters.ollama.httpx") as mock_mod:
            mock_client = AsyncMock()
            mock_mod.AsyncClient.return_value = mock_client
            # Make AsyncClient usable as context manager
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            yield mock_mod, mock_client

    @pytest.mark.asyncio
    async def test_complete_returns_completion_response(self, mock_httpx):
        mock_mod, mock_client = mock_httpx
        response_json = {
            "model": "llama3.1:8b",
            "message": {"role": "assistant", "content": "Hello from Ollama!"},
            "done": True,
            "prompt_eval_count": 12,
            "eval_count": 8,
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = response_json
        mock_resp.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_resp)

        adapter = OllamaAdapter(base_url="http://localhost:11434")
        result = await adapter.complete(MESSAGES, model="llama3.1:8b")

        assert isinstance(result, CompletionResponse)
        assert result.content == "Hello from Ollama!"
        assert result.model == "llama3.1:8b"
        assert result.usage.prompt_tokens == 12
        assert result.usage.completion_tokens == 8

    @pytest.mark.asyncio
    async def test_complete_structured_returns_validated_model(self, mock_httpx):
        mock_mod, mock_client = mock_httpx
        response_json = {
            "model": "llama3.1:8b",
            "message": {
                "role": "assistant",
                "content": json.dumps(
                    {"title": "Interstellar", "rating": 9.2, "summary": "Space epic"}
                ),
            },
            "done": True,
            "prompt_eval_count": 15,
            "eval_count": 10,
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = response_json
        mock_resp.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_resp)

        adapter = OllamaAdapter(base_url="http://localhost:11434")
        result = await adapter.complete_structured(
            MESSAGES, model="llama3.1:8b", response_model=MovieReview
        )

        assert isinstance(result, MovieReview)
        assert result.title == "Interstellar"

    @pytest.mark.asyncio
    async def test_complete_structured_retries_on_validation_error(self, mock_httpx):
        """Ollama retries up to 3 times on Pydantic ValidationError with error feedback."""
        mock_mod, mock_client = mock_httpx

        # First call returns invalid JSON (missing required field), second succeeds
        bad_response_json = {
            "model": "llama3.1:8b",
            "message": {"role": "assistant", "content": json.dumps({"title": "Bad"})},
            "done": True,
            "prompt_eval_count": 10,
            "eval_count": 5,
        }
        good_response_json = {
            "model": "llama3.1:8b",
            "message": {
                "role": "assistant",
                "content": json.dumps(
                    {"title": "Good", "rating": 8.0, "summary": "Fixed"}
                ),
            },
            "done": True,
            "prompt_eval_count": 15,
            "eval_count": 10,
        }
        bad_resp = MagicMock()
        bad_resp.status_code = 200
        bad_resp.json.return_value = bad_response_json
        bad_resp.raise_for_status = MagicMock()

        good_resp = MagicMock()
        good_resp.status_code = 200
        good_resp.json.return_value = good_response_json
        good_resp.raise_for_status = MagicMock()

        mock_client.post = AsyncMock(side_effect=[bad_resp, good_resp])

        adapter = OllamaAdapter(base_url="http://localhost:11434")
        result = await adapter.complete_structured(
            MESSAGES, model="llama3.1:8b", response_model=MovieReview
        )

        assert isinstance(result, MovieReview)
        assert result.title == "Good"
        assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_raises_rate_limit_error_on_429(self, mock_httpx):
        mock_mod, mock_client = mock_httpx
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_resp)

        adapter = OllamaAdapter(base_url="http://localhost:11434")
        with pytest.raises(RateLimitError):
            await adapter.complete(MESSAGES)

    @pytest.mark.asyncio
    async def test_raises_service_unavailable_on_500(self, mock_httpx):
        mock_mod, mock_client = mock_httpx
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_resp)

        adapter = OllamaAdapter(base_url="http://localhost:11434")
        with pytest.raises(ServiceUnavailableError):
            await adapter.complete(MESSAGES)


# ===========================================================================
# LLMConfig model tests
# ===========================================================================


class TestLLMConfig:
    """Tests for LLMConfig Pydantic model."""

    def test_validates_provider_model_api_key_base_url(self):
        config = LLMConfig(
            provider="claude",
            model="claude-sonnet-4-20250514",
            api_key="sk-test",
            base_url="https://api.anthropic.com",
        )
        assert config.provider == "claude"
        assert config.model == "claude-sonnet-4-20250514"
        assert config.api_key == "sk-test"
        assert config.base_url == "https://api.anthropic.com"

    def test_optional_fields_default_to_none(self):
        config = LLMConfig(provider="ollama")
        assert config.model is None
        assert config.api_key is None
        assert config.base_url is None
