"""Integration tests for idempotent POST /v1/render via X-Request-Id."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import TEST_RAW_KEY

VALID_IR = {
    "schema_version": "1.0",
    "metadata": {"title": "Idempotency Test"},
    "slides": [{"slide_type": "title_slide", "title": "Test"}],
}


@pytest.mark.asyncio
async def test_request_id_stored(async_client: AsyncClient, seed_api_key):
    """POST /v1/render with X-Request-Id stores the request_id on the deck."""
    _, _, raw_key = seed_api_key
    resp = await async_client.post(
        "/v1/render",
        json=VALID_IR,
        headers={"X-API-Key": raw_key, "X-Request-Id": "req_unique_001"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "validated"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_duplicate_request_id_returns_existing(async_client: AsyncClient, seed_api_key):
    """Repeated POST with same X-Request-Id returns the original result."""
    _, _, raw_key = seed_api_key
    headers = {"X-API-Key": raw_key, "X-Request-Id": "req_idempotent_002"}

    # First request creates the deck
    resp1 = await async_client.post("/v1/render", json=VALID_IR, headers=headers)
    assert resp1.status_code == 200
    data1 = resp1.json()
    first_id = data1["id"]

    # Second request with same request_id returns the same deck
    resp2 = await async_client.post("/v1/render", json=VALID_IR, headers=headers)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["id"] == first_id, "Duplicate request_id should return the same deck"


@pytest.mark.asyncio
async def test_no_request_id_creates_new_each_time(async_client: AsyncClient, seed_api_key):
    """POST without X-Request-Id creates a new deck each time."""
    _, _, raw_key = seed_api_key
    headers = {"X-API-Key": raw_key}

    resp1 = await async_client.post("/v1/render", json=VALID_IR, headers=headers)
    assert resp1.status_code == 200
    id1 = resp1.json()["id"]

    resp2 = await async_client.post("/v1/render", json=VALID_IR, headers=headers)
    assert resp2.status_code == 200
    id2 = resp2.json()["id"]

    assert id1 != id2, "Requests without X-Request-Id should create separate decks"
