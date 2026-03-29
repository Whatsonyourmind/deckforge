"""Tests for the /v1/generate endpoint, SSE streaming, and worker task integration.

Tests cover:
- POST /v1/generate request/response validation
- SSE event streaming via Redis pub/sub
- Worker task integration with ContentPipeline
- GenerateRequest/GenerateResponse schema validation
"""

from __future__ import annotations

import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from deckforge.ir.enums import Audience, Purpose, SlideType, Tone


# ===========================================================================
# Schema validation tests
# ===========================================================================


class TestGenerateRequestSchema:
    """GenerateRequest model validates prompt, generation_options, theme, llm_config."""

    def test_valid_request_minimal(self):
        from deckforge.api.schemas.requests import GenerateRequest

        req = GenerateRequest(prompt="Create a board presentation about Q4 results")
        assert req.prompt == "Create a board presentation about Q4 results"
        assert req.theme == "executive-dark"
        assert req.generation_options is None
        assert req.llm_config is None

    def test_valid_request_with_all_fields(self):
        from deckforge.api.schemas.requests import GenerateRequest
        from deckforge.ir.metadata import GenerationOptions
        from deckforge.llm.models import LLMConfig

        req = GenerateRequest(
            prompt="Create an investor update deck",
            generation_options=GenerationOptions(target_slide_count=12),
            theme="corporate-blue",
            llm_config=LLMConfig(provider="openai", api_key="sk-test123"),
            webhook_url="https://example.com/hook",
        )
        assert req.generation_options is not None
        assert req.llm_config is not None
        assert req.webhook_url == "https://example.com/hook"

    def test_prompt_too_short_raises(self):
        from deckforge.api.schemas.requests import GenerateRequest

        with pytest.raises(Exception):
            GenerateRequest(prompt="Short")  # min_length=10

    def test_prompt_too_long_raises(self):
        from deckforge.api.schemas.requests import GenerateRequest

        with pytest.raises(Exception):
            GenerateRequest(prompt="x" * 5001)  # max_length=5000


class TestGenerateResponseSchema:
    """GenerateResponse model includes job_id and status fields."""

    def test_valid_response(self):
        from deckforge.api.schemas.responses import GenerateResponse

        resp = GenerateResponse(
            job_id="abc123",
            status="queued",
            message="Job enqueued successfully",
        )
        assert resp.job_id == "abc123"
        assert resp.status == "queued"

    def test_response_without_message(self):
        from deckforge.api.schemas.responses import GenerateResponse

        resp = GenerateResponse(job_id="abc123", status="queued")
        assert resp.message is None


class TestSSEProgressEventSchema:
    """SSEProgressEvent model validates stage, progress, timestamp."""

    def test_valid_event(self):
        from deckforge.api.schemas.responses import SSEProgressEvent

        event = SSEProgressEvent(
            stage="parsing",
            progress=0.15,
            timestamp="2026-03-29T00:00:00Z",
        )
        assert event.stage == "parsing"
        assert event.progress == 0.15


# ===========================================================================
# Endpoint integration tests (using test app fixtures)
# ===========================================================================


class TestGenerateEndpoint:
    """POST /v1/generate creates job and returns 202."""

    @pytest.mark.asyncio
    async def test_post_generate_returns_202_with_job_id(
        self, async_client, seed_api_key
    ):
        """POST /v1/generate with valid prompt returns 202 with job_id."""
        _, api_key, raw_key = seed_api_key

        with patch("deckforge.api.routes.generate.ArqRedis") as MockArq:
            mock_arq = AsyncMock()
            MockArq.return_value = mock_arq
            mock_arq.enqueue_job = AsyncMock()

            response = await async_client.post(
                "/v1/generate",
                json={"prompt": "Create a board presentation about Q4 financial results"},
                headers={"X-API-Key": raw_key},
            )

        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"

    @pytest.mark.asyncio
    async def test_post_generate_without_auth_returns_401(self, async_client):
        """POST /v1/generate without API key returns 401."""
        response = await async_client.post(
            "/v1/generate",
            json={"prompt": "Create a board presentation about Q4 financial results"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_post_generate_invalid_body_returns_422(
        self, async_client, seed_api_key
    ):
        """POST /v1/generate with invalid body returns 422."""
        _, _, raw_key = seed_api_key

        response = await async_client.post(
            "/v1/generate",
            json={"prompt": "Short"},  # Too short (min 10)
            headers={"X-API-Key": raw_key},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_post_generate_with_llm_config(
        self, async_client, seed_api_key
    ):
        """POST /v1/generate with user API key in llm_config is accepted."""
        _, _, raw_key = seed_api_key

        with patch("deckforge.api.routes.generate.ArqRedis") as MockArq:
            mock_arq = AsyncMock()
            MockArq.return_value = mock_arq
            mock_arq.enqueue_job = AsyncMock()

            response = await async_client.post(
                "/v1/generate",
                json={
                    "prompt": "Create an investor presentation about our Series B raise",
                    "llm_config": {"provider": "openai", "api_key": "sk-test"},
                },
                headers={"X-API-Key": raw_key},
            )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "queued"


# ===========================================================================
# SSE streaming endpoint tests
# ===========================================================================


class TestSSEStreamEndpoint:
    """GET /v1/generate/{job_id}/stream returns SSE content type."""

    @pytest.mark.asyncio
    async def test_sse_endpoint_returns_event_stream_content_type(
        self, async_client, seed_api_key, fake_redis
    ):
        """SSE stream returns text/event-stream content type."""
        _, _, raw_key = seed_api_key
        job_id = str(uuid.uuid4())

        # Publish a complete event so the stream terminates quickly
        async def publish_events():
            await asyncio.sleep(0.05)
            payload = json.dumps({
                "stage": "complete",
                "progress": 1.0,
                "timestamp": "2026-03-29T00:00:00Z",
            })
            await fake_redis.publish(f"job:{job_id}:progress", payload)

        asyncio.create_task(publish_events())

        response = await async_client.get(
            f"/v1/generate/{job_id}/stream",
            headers={"X-API-Key": raw_key},
        )
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "text/event-stream" in content_type


# ===========================================================================
# Worker task integration tests
# ===========================================================================


class TestGenerateContentWorkerTask:
    """generate_content worker task calls ContentPipeline.run() with progress."""

    @pytest.mark.asyncio
    async def test_generate_content_calls_pipeline(self):
        """Worker task runs ContentPipeline and publishes progress."""
        from deckforge.workers.tasks import generate_content

        mock_redis = AsyncMock()
        mock_redis.publish = AsyncMock()

        ctx = {
            "redis": mock_redis,
            "db_factory": None,
            "s3_client": None,
            "s3_bucket": "deckforge",
        }

        job_id = str(uuid.uuid4())

        # Mock ContentPipeline to return a minimal valid IR
        mock_ir = {
            "schema_version": "1.0",
            "metadata": {"title": "Test Presentation"},
            "slides": [
                {
                    "slide_type": "title_slide",
                    "elements": [
                        {"type": "heading", "content": {"text": "Test", "level": "h1"}},
                    ],
                }
            ],
        }

        with (
            patch("deckforge.content.pipeline.ContentPipeline") as MockPipeline,
            patch("deckforge.llm.router.create_router") as MockRouter,
            patch("deckforge.workers.tasks.render_pipeline") as MockRender,
        ):
            mock_pipeline_instance = AsyncMock()
            mock_pipeline_instance.run = AsyncMock(return_value=mock_ir)
            MockPipeline.return_value = mock_pipeline_instance
            MockRouter.return_value = MagicMock()
            MockRender.return_value = (b"fake pptx bytes", MagicMock(quality_score=85, issues=[], fixes=[]))

            result = await generate_content(
                ctx,
                job_id,
                "Create a board presentation about Q4 results",
            )

        assert result["status"] == "complete"
        mock_pipeline_instance.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_content_handles_failure(self):
        """Worker task updates job status to failed on pipeline error."""
        from deckforge.workers.tasks import generate_content

        mock_redis = AsyncMock()
        mock_redis.publish = AsyncMock()

        ctx = {
            "redis": mock_redis,
            "db_factory": None,
            "s3_client": None,
            "s3_bucket": "deckforge",
        }

        job_id = str(uuid.uuid4())

        with (
            patch("deckforge.content.pipeline.ContentPipeline") as MockPipeline,
            patch("deckforge.llm.router.create_router") as MockRouter,
        ):
            mock_pipeline_instance = AsyncMock()
            mock_pipeline_instance.run = AsyncMock(side_effect=ValueError("LLM error"))
            MockPipeline.return_value = mock_pipeline_instance
            MockRouter.return_value = MagicMock()

            with pytest.raises(ValueError, match="LLM error"):
                await generate_content(
                    ctx,
                    job_id,
                    "Create a board deck",
                )


# ===========================================================================
# Router registration test
# ===========================================================================


class TestAppRouterRegistration:
    """App registers the generate router."""

    def test_generate_router_registered(self):
        from deckforge.api.app import create_app

        app = create_app()
        routes = [r.path for r in app.routes]
        assert "/v1/generate" in routes
        assert "/v1/generate/{job_id}/stream" in routes
