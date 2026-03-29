"""Integration tests for API key authentication middleware."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import TEST_RAW_KEY

# Minimal valid IR payload for POST /v1/render
VALID_IR = {
    "schema_version": "1.0",
    "metadata": {
        "title": "Auth Test Deck",
    },
    "slides": [
        {
            "slide_type": "title_slide",
            "title": "Test Slide",
        }
    ],
}


@pytest.mark.asyncio
async def test_missing_api_key_returns_401(async_client: AsyncClient):
    """Request without X-API-Key header returns 401."""
    resp = await async_client.post("/v1/render", json=VALID_IR)
    assert resp.status_code == 401
    assert "Missing API key" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_invalid_format_key_returns_401(async_client: AsyncClient):
    """Request with key that doesn't start with dk_live_ or dk_test_ returns 401."""
    resp = await async_client.post(
        "/v1/render",
        json=VALID_IR,
        headers={"X-API-Key": "invalid_prefix_key_123"},
    )
    assert resp.status_code == 401
    assert "Invalid API key format" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_unknown_key_hash_returns_401(async_client: AsyncClient):
    """Request with correctly formatted but unknown key returns 401."""
    resp = await async_client.post(
        "/v1/render",
        json=VALID_IR,
        headers={"X-API-Key": "dk_live_unknown_key_that_does_not_exist"},
    )
    assert resp.status_code == 401
    assert "Invalid or deactivated" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_valid_key_returns_200(async_client: AsyncClient, seed_api_key):
    """Request with a valid seeded API key authenticates and returns 200.

    The sync render path (<=10 slides) returns a PPTX binary with
    application/vnd.openxmlformats-officedocument.presentationml.presentation
    content type and X-Deck-Id header.
    """
    _, _, raw_key = seed_api_key
    resp = await async_client.post(
        "/v1/render",
        json=VALID_IR,
        headers={"X-API-Key": raw_key},
    )
    assert resp.status_code == 200
    # Sync render returns PPTX binary or JSON depending on slide count
    content_type = resp.headers.get("content-type", "")
    if "openxmlformats" in content_type:
        # PPTX binary response — check it starts with PK (zip header)
        assert resp.content[:2] == b"PK"
        assert resp.headers.get("x-deck-id") is not None
    else:
        # JSON response (async path or fallback)
        data = resp.json()
        assert data["status"] in ("validated", "queued")
        assert data["id"] is not None
