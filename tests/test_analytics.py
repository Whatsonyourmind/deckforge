"""Tests for usage analytics endpoints.

Tests GET /v1/analytics/* endpoints with seeded usage and payment data.
Verifies admin access restriction, response shapes, and data correctness.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from deckforge.db.models.api_key import ApiKey
from deckforge.db.models.payment_event import PaymentEvent
from deckforge.db.models.usage import UsageRecord
from deckforge.db.models.user import User


ADMIN_RAW_KEY = "dk_test_admin_analytics_key"
ADMIN_KEY_HASH = hashlib.sha256(ADMIN_RAW_KEY.encode()).hexdigest()

NON_ADMIN_RAW_KEY = "dk_test_starter_basic_key"
NON_ADMIN_KEY_HASH = hashlib.sha256(NON_ADMIN_RAW_KEY.encode()).hexdigest()


@pytest.fixture
async def seed_analytics_data(session: AsyncSession):
    """Seed usage_records and payment_events for analytics tests.

    Creates:
    - An enterprise user with admin API key
    - A starter user with non-admin API key
    - 3 usage records with credit usage
    - 2 payment events (x402 payments)
    """
    # Admin user + key
    admin_user = User(email="admin@example.com", name="Admin User")
    session.add(admin_user)
    await session.flush()

    admin_key = ApiKey(
        user_id=admin_user.id,
        key_hash=ADMIN_KEY_HASH,
        key_prefix="dk_test_admin_a",
        name="Admin Key",
        scopes=["read", "generate", "admin"],
        tier="enterprise",
        is_test=True,
    )
    session.add(admin_key)
    await session.flush()

    # Non-admin user + key
    basic_user = User(email="basic@example.com", name="Basic User")
    session.add(basic_user)
    await session.flush()

    basic_key = ApiKey(
        user_id=basic_user.id,
        key_hash=NON_ADMIN_KEY_HASH,
        key_prefix="dk_test_starter",
        name="Basic Key",
        scopes=["read", "generate"],
        tier="starter",
        is_test=True,
    )
    session.add(basic_key)
    await session.flush()

    # Usage records -- each in a different month to avoid UNIQUE constraint
    today = date.today()
    for i in range(3):
        # Use current month, previous month, 2 months ago
        month = today.month - i
        year = today.year
        if month < 1:
            month += 12
            year -= 1
        period_start = date(year, month, 1)
        # Last day of that month
        import calendar
        _, last_day = calendar.monthrange(year, month)
        period_end = date(year, month, last_day)

        record = UsageRecord(
            api_key_id=admin_key.id,
            period_start=period_start,
            period_end=period_end,
            credit_limit=10000,
            credits_used=100 * (i + 1),
            tier="enterprise",
        )
        session.add(record)

    # Payment events (x402)
    pe1 = PaymentEvent(
        payment_hash=f"0xhash_test_{uuid.uuid4().hex[:16]}",
        endpoint="/v1/render",
        amount_usd=Decimal("0.05"),
        currency="USDC",
        network="eip155:8453",
        payer_address="0xagent1_test_address",
        wallet_address="0xdeckforge_wallet",
        status="settled",
    )
    pe2 = PaymentEvent(
        payment_hash=f"0xhash_test_{uuid.uuid4().hex[:16]}",
        endpoint="/v1/generate",
        amount_usd=Decimal("0.10"),
        currency="USDC",
        network="eip155:8453",
        payer_address="0xagent2_test_address",
        wallet_address="0xdeckforge_wallet",
        status="settled",
    )
    session.add(pe1)
    session.add(pe2)

    await session.commit()
    return admin_key, basic_key


@pytest.mark.asyncio
async def test_overview_returns_all_fields(async_client, seed_analytics_data):
    """GET /v1/analytics/overview should return all required metric fields."""
    resp = await async_client.get(
        "/v1/analytics/overview",
        headers={"X-API-Key": ADMIN_RAW_KEY},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert "total_calls" in data
    assert "stripe_revenue_usd" in data
    assert "x402_revenue_usd" in data
    assert "total_revenue_usd" in data
    assert "active_consumers" in data
    assert "period_days" in data
    assert isinstance(data["total_calls"], int)
    assert isinstance(data["stripe_revenue_usd"], (int, float))
    assert isinstance(data["x402_revenue_usd"], (int, float))


@pytest.mark.asyncio
async def test_endpoint_breakdown_groups_by_endpoint(
    async_client, seed_analytics_data
):
    """GET /v1/analytics/endpoints should return grouped endpoint data."""
    resp = await async_client.get(
        "/v1/analytics/endpoints",
        headers={"X-API-Key": ADMIN_RAW_KEY},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)

    # Should have at least subscription entry + x402 endpoints
    assert len(data) >= 1
    for entry in data:
        assert "endpoint" in entry
        assert "calls" in entry
        assert "credits_used" in entry


@pytest.mark.asyncio
async def test_top_consumers_ordered_by_calls(async_client, seed_analytics_data):
    """GET /v1/analytics/consumers should return consumers ordered by calls desc."""
    resp = await async_client.get(
        "/v1/analytics/consumers",
        headers={"X-API-Key": ADMIN_RAW_KEY},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)

    if len(data) > 1:
        for i in range(len(data) - 1):
            assert data[i]["calls"] >= data[i + 1]["calls"]

    for entry in data:
        assert "api_key_id" in entry
        assert "calls" in entry
        assert "credits_used" in entry
        assert "tier" in entry


@pytest.mark.asyncio
async def test_revenue_timeseries_returns_daily_datapoints(
    async_client, seed_analytics_data
):
    """GET /v1/analytics/revenue should return daily revenue datapoints."""
    resp = await async_client.get(
        "/v1/analytics/revenue?days=30&granularity=daily",
        headers={"X-API-Key": ADMIN_RAW_KEY},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)

    for entry in data:
        assert "date" in entry
        assert "stripe_revenue_usd" in entry
        assert "x402_revenue_usd" in entry
        assert "total_revenue_usd" in entry


@pytest.mark.asyncio
async def test_full_analytics_returns_all_sections(
    async_client, seed_analytics_data
):
    """GET /v1/analytics should return the full dashboard response."""
    resp = await async_client.get(
        "/v1/analytics",
        headers={"X-API-Key": ADMIN_RAW_KEY},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert "overview" in data
    assert "endpoints" in data
    assert "top_consumers" in data
    assert "revenue_trend" in data
    assert isinstance(data["overview"]["total_calls"], int)


@pytest.mark.asyncio
async def test_non_admin_key_returns_403(async_client, seed_analytics_data):
    """Non-admin/non-enterprise key should get 403 on analytics endpoints."""
    resp = await async_client.get(
        "/v1/analytics/overview",
        headers={"X-API-Key": NON_ADMIN_RAW_KEY},
    )
    assert resp.status_code == 403
    assert "enterprise" in resp.json()["detail"].lower() or "admin" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_overview_with_custom_days(async_client, seed_analytics_data):
    """GET /v1/analytics/overview?days=7 should accept custom period."""
    resp = await async_client.get(
        "/v1/analytics/overview?days=7",
        headers={"X-API-Key": ADMIN_RAW_KEY},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["period_days"] == 7
