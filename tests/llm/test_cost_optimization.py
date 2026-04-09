"""Tests for LLM cost optimization: prompt caching, Batch API, tier routing.

All tests mock the underlying Anthropic / Gemini SDKs -- no real API calls.
Covers the three prongs of the optimization landed in Wave 2:

1. **Prompt caching** -- ``cache_control`` markers are forwarded to the
   Anthropic messages.create() call when static system blocks are supplied.
2. **Batch API** -- BatchLLMJob submits, polls, and iterates results in the
   shape Anthropic expects.
3. **Tier routing** -- LLMRouter.complete() with ``tier=...`` selects the
   right model, falls back when the preferred provider is missing, and logs
   a cost estimate.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from deckforge.llm.adapters.claude import ClaudeAdapter, build_cached_system
from deckforge.llm.batch import BatchLLMJob, BatchResult, BatchState, BatchStatus
from deckforge.llm.models import (
    CompletionResponse,
    LLMUsage,
    RateLimitError,
    ServiceUnavailableError,
    StreamChunk,
)
from deckforge.llm.router import (
    TIER_MODEL_MAP,
    LLMRouter,
    LLMTier,
)
from deckforge.llm.base import LLMAdapter


MESSAGES = [{"role": "user", "content": "Hello"}]


# ===========================================================================
# Step 2: Prompt caching
# ===========================================================================


class TestBuildCachedSystem:
    """Tests for the ``build_cached_system`` helper."""

    def test_empty_returns_empty_list(self):
        assert build_cached_system() == []

    def test_single_block_gets_cache_control(self):
        blocks = build_cached_system("theme spec")
        assert len(blocks) == 1
        assert blocks[0]["type"] == "text"
        assert blocks[0]["text"] == "theme spec"
        assert blocks[0]["cache_control"] == {"type": "ephemeral"}

    def test_multiple_blocks_only_last_cached(self):
        blocks = build_cached_system("theme spec", "ir schema", "few-shot examples")
        assert len(blocks) == 3
        assert "cache_control" not in blocks[0]
        assert "cache_control" not in blocks[1]
        assert blocks[2]["cache_control"] == {"type": "ephemeral"}
        assert blocks[2]["text"] == "few-shot examples"

    def test_cache_last_false_disables_caching(self):
        blocks = build_cached_system("stable text", cache_last=False)
        assert "cache_control" not in blocks[0]


class TestClaudePromptCaching:
    """Tests that ClaudeAdapter forwards cached system blocks to the SDK."""

    @pytest.fixture
    def mock_anthropic(self):
        with patch("deckforge.llm.adapters.claude.anthropic") as mock_mod:
            mock_client = AsyncMock()
            mock_mod.AsyncAnthropic.return_value = mock_client
            mock_mod.RateLimitError = type("RateLimitError", (Exception,), {})
            mock_mod.APIStatusError = type(
                "APIStatusError",
                (Exception,),
                {
                    "__init__": lambda self, message="", *, status_code=500, response=None, body=None: (
                        setattr(self, "status_code", status_code)
                        or setattr(self, "response", response)
                        or setattr(self, "body", body)
                        or Exception.__init__(self, message)
                    )
                },
            )
            yield mock_mod, mock_client

    def _stub_response(self):
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text="ack")],
            model="claude-sonnet-4-20250514",
            usage=SimpleNamespace(input_tokens=100, output_tokens=5),
            stop_reason="end_turn",
        )

    @pytest.mark.asyncio
    async def test_cache_control_is_passed_on_static_blocks(self, mock_anthropic):
        """When system= receives cached blocks, Anthropic SDK sees cache_control."""
        _mock_mod, mock_client = mock_anthropic
        mock_client.messages.create = AsyncMock(return_value=self._stub_response())

        adapter = ClaudeAdapter(api_key="sk-test")
        cached_system = build_cached_system(
            "THEME SPEC: corporate-blue palette...",
            "IR SCHEMA: 32 slide types, discriminated union on slide_type",
        )

        await adapter.complete(MESSAGES, system=cached_system)

        mock_client.messages.create.assert_awaited_once()
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert "system" in call_kwargs
        system_param = call_kwargs["system"]
        assert isinstance(system_param, list)
        assert len(system_param) == 2
        assert system_param[-1]["cache_control"] == {"type": "ephemeral"}
        # Static content preserved
        assert "THEME SPEC" in system_param[0]["text"]
        assert "IR SCHEMA" in system_param[1]["text"]

    @pytest.mark.asyncio
    async def test_plain_string_system_does_not_add_cache_control(
        self, mock_anthropic
    ):
        """A plain string system prompt should pass through unchanged (no caching)."""
        _mock_mod, mock_client = mock_anthropic
        mock_client.messages.create = AsyncMock(return_value=self._stub_response())

        adapter = ClaudeAdapter(api_key="sk-test")
        await adapter.complete(MESSAGES, system="you are a helpful assistant")

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["system"] == "you are a helpful assistant"

    @pytest.mark.asyncio
    async def test_system_role_in_messages_extracted_as_plain_string(
        self, mock_anthropic
    ):
        """Legacy callers that pass role=system inside messages still work."""
        _mock_mod, mock_client = mock_anthropic
        mock_client.messages.create = AsyncMock(return_value=self._stub_response())

        adapter = ClaudeAdapter(api_key="sk-test")
        await adapter.complete(
            [
                {"role": "system", "content": "you are a helpful assistant"},
                {"role": "user", "content": "hi"},
            ]
        )

        call_kwargs = mock_client.messages.create.call_args.kwargs
        # System was extracted
        assert call_kwargs["system"] == "you are a helpful assistant"
        # Only user message remains in messages list
        assert len(call_kwargs["messages"]) == 1
        assert call_kwargs["messages"][0]["role"] == "user"

    @pytest.mark.asyncio
    async def test_no_system_produces_no_system_kwarg(self, mock_anthropic):
        _mock_mod, mock_client = mock_anthropic
        mock_client.messages.create = AsyncMock(return_value=self._stub_response())

        adapter = ClaudeAdapter(api_key="sk-test")
        await adapter.complete(MESSAGES)

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert "system" not in call_kwargs


# ===========================================================================
# Step 3: Batch API
# ===========================================================================


class _AsyncIter:
    """Async iterator helper: wraps a sync iterable into an async one."""

    def __init__(self, items: list[Any]) -> None:
        self._items = list(items)

    def __aiter__(self) -> "_AsyncIter":
        return self

    async def __anext__(self) -> Any:
        if not self._items:
            raise StopAsyncIteration
        return self._items.pop(0)


class TestBatchLLMJob:
    """Tests for the Anthropic Batch API wrapper."""

    def _make_job(self) -> tuple[BatchLLMJob, MagicMock]:
        fake_client = MagicMock()
        fake_client.messages = MagicMock()
        fake_client.messages.batches = MagicMock()
        fake_client.messages.batches.create = AsyncMock()
        fake_client.messages.batches.retrieve = AsyncMock()
        fake_client.messages.batches.results = AsyncMock()
        fake_client.messages.batches.cancel = AsyncMock()
        job = BatchLLMJob(client=fake_client)
        return job, fake_client

    @pytest.mark.asyncio
    async def test_submit_passes_request_shape_to_sdk(self):
        job, client = self._make_job()
        client.messages.batches.create.return_value = SimpleNamespace(
            id="msgbatch_01Abc"
        )

        requests = [
            {
                "custom_id": "deck-001",
                "params": {
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 4096,
                    "messages": [{"role": "user", "content": "Build deck 1"}],
                },
            },
            {
                "custom_id": "deck-002",
                "params": {
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 4096,
                    "messages": [{"role": "user", "content": "Build deck 2"}],
                },
            },
        ]

        batch_id = await job.submit(requests)
        assert batch_id == "msgbatch_01Abc"

        client.messages.batches.create.assert_awaited_once()
        call_kwargs = client.messages.batches.create.call_args.kwargs
        submitted = call_kwargs["requests"]
        assert len(submitted) == 2
        assert submitted[0]["custom_id"] == "deck-001"
        assert submitted[0]["params"]["model"] == "claude-sonnet-4-20250514"
        assert submitted[1]["custom_id"] == "deck-002"

    @pytest.mark.asyncio
    async def test_submit_rejects_empty_request_list(self):
        job, _ = self._make_job()
        with pytest.raises(ValueError, match="at least one"):
            await job.submit([])

    @pytest.mark.asyncio
    async def test_submit_rejects_requests_missing_custom_id(self):
        job, _ = self._make_job()
        with pytest.raises(ValueError, match="custom_id"):
            await job.submit([{"params": {}}])

    @pytest.mark.asyncio
    async def test_submit_rejects_requests_missing_params(self):
        job, _ = self._make_job()
        with pytest.raises(ValueError, match="params"):
            await job.submit([{"custom_id": "x"}])

    @pytest.mark.asyncio
    async def test_poll_returns_processing_state_in_progress(self):
        job, client = self._make_job()
        client.messages.batches.retrieve.return_value = SimpleNamespace(
            id="msgbatch_01Abc",
            processing_status="in_progress",
            request_counts=SimpleNamespace(
                succeeded=3, errored=0, canceled=0, expired=0, processing=7
            ),
        )

        status = await job.poll("msgbatch_01Abc")
        assert isinstance(status, BatchStatus)
        assert status.state == BatchState.PROCESSING
        assert status.is_complete is False
        assert status.is_terminal is False
        assert status.succeeded == 3
        assert status.total == 10

    @pytest.mark.asyncio
    async def test_poll_returns_complete_state_on_ended(self):
        job, client = self._make_job()
        client.messages.batches.retrieve.return_value = SimpleNamespace(
            id="msgbatch_01Abc",
            processing_status="ended",
            request_counts=SimpleNamespace(
                succeeded=10, errored=0, canceled=0, expired=0, processing=0
            ),
        )

        status = await job.poll("msgbatch_01Abc")
        assert status.state == BatchState.COMPLETE
        assert status.is_complete is True
        assert status.is_terminal is True

    @pytest.mark.asyncio
    async def test_fetch_results_iterates_entries(self):
        job, client = self._make_job()
        entries = [
            SimpleNamespace(
                custom_id="deck-001",
                result=SimpleNamespace(
                    type="succeeded",
                    message=SimpleNamespace(content=[{"text": "ok"}]),
                    error=None,
                ),
            ),
            SimpleNamespace(
                custom_id="deck-002",
                result=SimpleNamespace(
                    type="errored",
                    message=None,
                    error={"type": "rate_limit", "message": "slow down"},
                ),
            ),
        ]
        client.messages.batches.results.return_value = _AsyncIter(entries)

        collected: list[BatchResult] = []
        async for r in job.fetch_results("msgbatch_01Abc"):
            collected.append(r)

        assert len(collected) == 2
        assert collected[0].custom_id == "deck-001"
        assert collected[0].result_type == "succeeded"
        assert collected[0].message is not None
        assert collected[1].custom_id == "deck-002"
        assert collected[1].result_type == "errored"
        assert collected[1].error == {"type": "rate_limit", "message": "slow down"}

    def test_requires_api_key_or_client(self):
        with pytest.raises(ValueError, match="api_key or a client"):
            BatchLLMJob()


# ===========================================================================
# Step 4: Tier routing
# ===========================================================================


class _TierMockAdapter(LLMAdapter):
    """Test adapter that records the model it was called with."""

    def __init__(
        self,
        name: str,
        *,
        fail_with: type[Exception] | None = None,
    ) -> None:
        self.name = name
        self._fail_with = fail_with
        self.last_model: str | None = None
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
        self.last_model = model
        if self._fail_with:
            raise self._fail_with(f"{self.name} failed")
        return CompletionResponse(
            content=f"from {self.name}",
            model=model or f"{self.name}-default",
            usage=LLMUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
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
        self.last_model = model
        if self._fail_with:
            raise self._fail_with(f"{self.name} failed")
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
        self.last_model = model
        if self._fail_with:
            raise self._fail_with(f"{self.name} failed")
        yield StreamChunk(content="chunk", finish_reason="stop")


class TestTierRouting:
    """Tier-based model selection on the LLMRouter."""

    def _all_adapters(self) -> dict[str, _TierMockAdapter]:
        return {
            "claude": _TierMockAdapter("claude"),
            "openai": _TierMockAdapter("openai"),
            "gemini": _TierMockAdapter("gemini"),
        }

    def test_tier_model_map_has_all_tiers(self):
        assert LLMTier.STARTER in TIER_MODEL_MAP
        assert LLMTier.PRO in TIER_MODEL_MAP
        assert LLMTier.ENTERPRISE in TIER_MODEL_MAP
        assert LLMTier.BYOK in TIER_MODEL_MAP
        # Starter should route to Gemini Flash
        assert "gemini" in TIER_MODEL_MAP[LLMTier.STARTER].lower()
        assert "sonnet" in TIER_MODEL_MAP[LLMTier.PRO].lower()
        assert "opus" in TIER_MODEL_MAP[LLMTier.ENTERPRISE].lower()

    @pytest.mark.asyncio
    async def test_tier_starter_routes_to_gemini(self):
        adapters = self._all_adapters()
        router = LLMRouter(
            adapters=adapters, fallback_chain=["claude", "openai", "gemini"]
        )
        await router.complete(MESSAGES, tier=LLMTier.STARTER)

        assert adapters["gemini"].call_count == 1
        assert adapters["claude"].call_count == 0
        assert adapters["gemini"].last_model == TIER_MODEL_MAP[LLMTier.STARTER]

    @pytest.mark.asyncio
    async def test_tier_pro_routes_to_claude_sonnet(self):
        adapters = self._all_adapters()
        router = LLMRouter(
            adapters=adapters, fallback_chain=["claude", "openai", "gemini"]
        )
        await router.complete(MESSAGES, tier=LLMTier.PRO)

        assert adapters["claude"].call_count == 1
        assert adapters["claude"].last_model == TIER_MODEL_MAP[LLMTier.PRO]

    @pytest.mark.asyncio
    async def test_tier_enterprise_routes_to_claude_opus(self):
        adapters = self._all_adapters()
        router = LLMRouter(
            adapters=adapters, fallback_chain=["claude", "openai", "gemini"]
        )
        await router.complete(MESSAGES, tier=LLMTier.ENTERPRISE)

        assert adapters["claude"].call_count == 1
        assert "opus" in adapters["claude"].last_model.lower()

    @pytest.mark.asyncio
    async def test_tier_accepts_string_value(self):
        adapters = self._all_adapters()
        router = LLMRouter(
            adapters=adapters, fallback_chain=["claude", "openai", "gemini"]
        )
        await router.complete(MESSAGES, tier="starter")

        assert adapters["gemini"].call_count == 1

    @pytest.mark.asyncio
    async def test_explicit_model_overrides_tier(self):
        adapters = self._all_adapters()
        router = LLMRouter(
            adapters=adapters, fallback_chain=["claude", "openai", "gemini"]
        )
        await router.complete(
            MESSAGES, model="claude-sonnet-4-20250514", tier=LLMTier.STARTER
        )

        # Explicit model wins: claude is called, not gemini
        assert adapters["claude"].call_count == 1
        assert adapters["gemini"].call_count == 0

    @pytest.mark.asyncio
    async def test_tier_byok_does_not_override_model(self):
        adapters = self._all_adapters()
        router = LLMRouter(
            adapters=adapters, fallback_chain=["claude", "openai", "gemini"]
        )
        # BYOK tier with no model -> falls back to first in chain (claude)
        await router.complete(MESSAGES, tier=LLMTier.BYOK)

        assert adapters["claude"].call_count == 1

    @pytest.mark.asyncio
    async def test_tier_starter_falls_back_to_claude_when_gemini_missing(self):
        """If Gemini isn't configured, Starter cascades to the next available tier."""
        adapters = {
            "claude": _TierMockAdapter("claude"),
            "openai": _TierMockAdapter("openai"),
            # Note: no gemini
        }
        router = LLMRouter(adapters=adapters, fallback_chain=["claude", "openai"])
        resolved = router.resolve_tier_model(LLMTier.STARTER)

        # Should cascade to PRO's model (sonnet) or at least a claude model
        assert "claude" in resolved.lower()

    @pytest.mark.asyncio
    async def test_tier_starter_cascades_on_runtime_error(self):
        """If Gemini adapter errors, router falls back through the chain.

        This tests that the fallback_chain mechanism still works after tier
        routing picks gemini-2.0-flash as the target model -- a Gemini rate
        limit cascades to claude via the normal fallback logic.
        """
        adapters = {
            "claude": _TierMockAdapter("claude"),
            "gemini": _TierMockAdapter("gemini", fail_with=RateLimitError),
        }
        router = LLMRouter(
            adapters=adapters, fallback_chain=["gemini", "claude"]
        )
        result = await router.complete(MESSAGES, tier=LLMTier.STARTER)

        # Gemini was called first (tier=starter), then fell back to claude
        assert adapters["gemini"].call_count == 1
        assert adapters["claude"].call_count == 1
        assert result.content == "from claude"

    @pytest.mark.asyncio
    async def test_tier_routing_is_logged(self, caplog):
        adapters = self._all_adapters()
        router = LLMRouter(
            adapters=adapters, fallback_chain=["claude", "openai", "gemini"]
        )
        import logging

        with caplog.at_level(logging.INFO, logger="deckforge.llm.router"):
            await router.complete(MESSAGES, tier=LLMTier.STARTER)

        # Cost log should mention tier + model + cost per MTok
        log_text = " ".join(r.getMessage() for r in caplog.records)
        assert "tier=starter" in log_text
        assert "cost_per_mtok_usd" in log_text

    @pytest.mark.asyncio
    async def test_structured_completion_respects_tier(self):
        class Foo(BaseModel):
            answer: str

        adapters = self._all_adapters()
        router = LLMRouter(
            adapters=adapters, fallback_chain=["claude", "openai", "gemini"]
        )
        result = await router.complete_structured(
            MESSAGES, response_model=Foo, tier=LLMTier.STARTER
        )

        assert isinstance(result, Foo)
        assert adapters["gemini"].call_count == 1
