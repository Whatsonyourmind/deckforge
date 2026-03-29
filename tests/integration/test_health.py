"""Integration tests for the /v1/health endpoint."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200_with_checks(async_client: AsyncClient):
    """GET /v1/health returns 200 with status and connectivity checks."""
    resp = await async_client.get("/v1/health")
    assert resp.status_code == 200

    data = resp.json()
    assert data["status"] in ("healthy", "degraded")
    assert "postgres" in data["checks"]
    assert "redis" in data["checks"]
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_health_redis_check_passes(async_client: AsyncClient):
    """Health check reports redis as ok when fakeredis is available."""
    resp = await async_client.get("/v1/health")
    data = resp.json()
    assert data["checks"]["redis"] == "ok"
