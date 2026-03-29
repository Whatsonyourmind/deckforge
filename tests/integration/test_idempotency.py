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


def _extract_deck_id(resp) -> str:
    """Extract deck ID from either PPTX or JSON response."""
    content_type = resp.headers.get("content-type", "")
    if "openxmlformats" in content_type:
        return resp.headers["x-deck-id"]
    return resp.json()["id"]


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
    deck_id = _extract_deck_id(resp)
    assert deck_id is not None


@pytest.mark.asyncio
async def test_duplicate_request_id_returns_existing(async_client: AsyncClient, seed_api_key):
    """Repeated POST with same X-Request-Id returns the original result."""
    _, _, raw_key = seed_api_key
    headers = {"X-API-Key": raw_key, "X-Request-Id": "req_idempotent_002"}

    # First request creates the deck
    resp1 = await async_client.post("/v1/render", json=VALID_IR, headers=headers)
    assert resp1.status_code == 200
    first_id = _extract_deck_id(resp1)

    # Second request with same request_id returns the same deck (JSON idempotency response)
    resp2 = await async_client.post("/v1/render", json=VALID_IR, headers=headers)
    assert resp2.status_code == 200
    second_id = _extract_deck_id(resp2)
    assert second_id == first_id, "Duplicate request_id should return the same deck"


@pytest.mark.asyncio
async def test_no_request_id_creates_new_each_time(async_client: AsyncClient, seed_api_key):
    """POST without X-Request-Id creates a new deck each time."""
    _, _, raw_key = seed_api_key
    headers = {"X-API-Key": raw_key}

    resp1 = await async_client.post("/v1/render", json=VALID_IR, headers=headers)
    assert resp1.status_code == 200
    id1 = _extract_deck_id(resp1)

    resp2 = await async_client.post("/v1/render", json=VALID_IR, headers=headers)
    assert resp2.status_code == 200
    id2 = _extract_deck_id(resp2)

    assert id1 != id2, "Requests without X-Request-Id should create separate decks"
