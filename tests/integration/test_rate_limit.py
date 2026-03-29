"""Integration tests for Redis token-bucket rate limiting."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import TEST_RAW_KEY

VALID_IR = {
    "schema_version": "1.0",
    "metadata": {"title": "Rate Limit Test"},
    "slides": [{"slide_type": "title_slide", "title": "Test"}],
}


@pytest.mark.asyncio
async def test_requests_within_limit_succeed(async_client: AsyncClient, seed_api_key):
    """Sending requests within the starter tier limit (10/min) succeeds."""
    _, _, raw_key = seed_api_key
    headers = {"X-API-Key": raw_key}

    # First few requests should succeed (starter tier = 10/min capacity)
    for i in range(5):
        resp = await async_client.post("/v1/render", json=VALID_IR, headers=headers)
        assert resp.status_code == 200, f"Request {i + 1} failed with {resp.status_code}"


@pytest.mark.asyncio
async def test_exceeding_limit_returns_429(async_client: AsyncClient, seed_api_key):
    """Exceeding the starter tier rate limit returns 429 with Retry-After header."""
    _, _, raw_key = seed_api_key
    headers = {"X-API-Key": raw_key}

    # Exhaust the starter tier limit (10 requests)
    got_429 = False
    for i in range(15):
        resp = await async_client.post("/v1/render", json=VALID_IR, headers=headers)
        if resp.status_code == 429:
            got_429 = True
            assert "Retry-After" in resp.headers
            assert int(resp.headers["Retry-After"]) >= 1
            break

    assert got_429, "Expected 429 after exhausting rate limit, but all requests succeeded"
