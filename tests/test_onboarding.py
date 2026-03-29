"""Tests for the developer onboarding flow.

Tests POST /v1/onboard/signup and GET /v1/onboard/status/{user_id}.
Uses in-memory SQLite with test fixtures from conftest.py.
"""

from __future__ import annotations

import uuid

import pytest


@pytest.mark.asyncio
async def test_signup_creates_user_and_returns_api_key(async_client, session):
    """Signup should create a user and return a dk_live_ API key."""
    resp = await async_client.post(
        "/v1/onboard/signup",
        json={
            "email": "developer@example.com",
            "name": "Test Developer",
            "tier": "starter",
        },
    )
    assert resp.status_code == 201
    data = resp.json()

    assert "user_id" in data
    assert data["api_key"].startswith("dk_live_")
    assert data["tier"] == "starter"
    assert data["credits"] == 50
    assert isinstance(data["next_steps"], list)
    assert len(data["next_steps"]) == 3


@pytest.mark.asyncio
async def test_signup_with_missing_email_returns_422(async_client):
    """Signup without email should return 422 validation error."""
    resp = await async_client.post(
        "/v1/onboard/signup",
        json={
            "name": "No Email User",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_signup_with_invalid_email_returns_422(async_client):
    """Signup with invalid email format should return 422."""
    resp = await async_client.post(
        "/v1/onboard/signup",
        json={
            "email": "not-an-email",
            "name": "Bad Email User",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_signup_duplicate_email_returns_409(async_client):
    """Signup with an existing email should return 409 conflict."""
    payload = {
        "email": "duplicate@example.com",
        "name": "First User",
    }
    resp1 = await async_client.post("/v1/onboard/signup", json=payload)
    assert resp1.status_code == 201

    resp2 = await async_client.post("/v1/onboard/signup", json=payload)
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_onboarding_status_returns_steps(async_client):
    """Onboarding status should return completed steps for a new user."""
    # Create user first
    signup_resp = await async_client.post(
        "/v1/onboard/signup",
        json={
            "email": "status-test@example.com",
            "name": "Status Test",
        },
    )
    assert signup_resp.status_code == 201
    user_id = signup_resp.json()["user_id"]

    # Check status
    status_resp = await async_client.get(f"/v1/onboard/status/{user_id}")
    assert status_resp.status_code == 200
    data = status_resp.json()

    assert "account_created" in data["steps_completed"]
    assert "api_key_created" in data["steps_completed"]
    assert isinstance(data["time_elapsed_seconds"], int)
    assert data["time_elapsed_seconds"] >= 0
    assert "next_step" in data


@pytest.mark.asyncio
async def test_onboarding_status_unknown_user_returns_404(async_client):
    """Onboarding status for nonexistent user should return 404."""
    fake_id = str(uuid.uuid4())
    resp = await async_client.get(f"/v1/onboard/status/{fake_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_signup_pro_tier(async_client):
    """Signup with pro tier should return 500 credits."""
    resp = await async_client.post(
        "/v1/onboard/signup",
        json={
            "email": "pro-user@example.com",
            "name": "Pro User",
            "tier": "pro",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["tier"] == "pro"
    assert data["credits"] == 500
