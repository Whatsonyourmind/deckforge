"""Tests for Unkey-based API key authentication and DB fallback."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from deckforge.api.middleware.auth import (
    AuthContext,
    _verify_via_db,
    _verify_via_unkey,
    get_api_key,
)


# ---------------------------------------------------------------------------
# AuthContext creation
# ---------------------------------------------------------------------------

class TestAuthContext:
    def test_create_default(self):
        ctx = AuthContext(key_id="test-key-123")
        assert ctx.key_id == "test-key-123"
        assert ctx.tier == "starter"
        assert ctx.user_id is None
        assert ctx.rate_limited is False
        assert ctx.remaining is None
        assert ctx.source == "unkey"
        assert ctx.payment_settled is False

    def test_create_with_all_fields(self):
        ctx = AuthContext(
            key_id="key-456",
            tier="pro",
            user_id="user-789",
            rate_limited=True,
            remaining=0,
            scopes=["read"],
            payment_settled=False,
            source="db",
        )
        assert ctx.tier == "pro"
        assert ctx.user_id == "user-789"
        assert ctx.rate_limited is True
        assert ctx.remaining == 0
        assert ctx.source == "db"

    def test_x402_source(self):
        ctx = AuthContext(
            key_id="x402:pay-001",
            tier="x402",
            payment_settled=True,
            source="x402",
        )
        assert ctx.source == "x402"
        assert ctx.payment_settled is True


# ---------------------------------------------------------------------------
# Unkey verification
# ---------------------------------------------------------------------------

class TestUnkeyVerification:
    @pytest.mark.asyncio
    async def test_valid_key(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "valid": True,
            "keyId": "key_abc",
            "meta": {"tier": "pro", "user_id": "u-1", "scopes": ["read", "generate"]},
            "ratelimit": {"remaining": 42},
        }

        with patch("deckforge.api.middleware.auth.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_client.return_value = mock_instance

            ctx = await _verify_via_unkey("dk_live_testkey123")

        assert ctx.key_id == "key_abc"
        assert ctx.tier == "pro"
        assert ctx.user_id == "u-1"
        assert ctx.rate_limited is False
        assert ctx.remaining == 42
        assert ctx.source == "unkey"

    @pytest.mark.asyncio
    async def test_invalid_key_returns_401(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "valid": False,
            "code": "KEY_NOT_FOUND",
        }

        with patch("deckforge.api.middleware.auth.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_client.return_value = mock_instance

            with pytest.raises(HTTPException) as exc_info:
                await _verify_via_unkey("dk_live_badkey")

        assert exc_info.value.status_code == 401
        assert "KEY_NOT_FOUND" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_rate_limited_flag(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "valid": True,
            "keyId": "key_rl",
            "meta": {"tier": "starter"},
            "ratelimit": {"remaining": 0},
        }

        with patch("deckforge.api.middleware.auth.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_client.return_value = mock_instance

            ctx = await _verify_via_unkey("dk_live_ratelimited")

        assert ctx.rate_limited is True
        assert ctx.remaining == 0


# ---------------------------------------------------------------------------
# DB fallback
# ---------------------------------------------------------------------------

class TestDbFallback:
    @pytest.mark.asyncio
    async def test_valid_db_key(self):
        db_key = MagicMock()
        db_key.id = uuid.uuid4()
        db_key.user_id = uuid.uuid4()
        db_key.tier = "pro"
        db_key.is_active = True
        db_key.scopes = ["read", "generate"]

        mock_db = AsyncMock()

        with patch(
            "deckforge.api.middleware.auth.api_key_repo.get_by_hash",
            return_value=db_key,
        ), patch(
            "deckforge.api.middleware.auth.api_key_repo.update_last_used",
            return_value=None,
        ):
            ctx = await _verify_via_db(mock_db, "dk_live_dbkey123")

        assert ctx.key_id == str(db_key.id)
        assert ctx.tier == "pro"
        assert ctx.source == "db"

    @pytest.mark.asyncio
    async def test_missing_db_key_returns_401(self):
        mock_db = AsyncMock()

        with patch(
            "deckforge.api.middleware.auth.api_key_repo.get_by_hash",
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await _verify_via_db(mock_db, "dk_live_nonexistent")

        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# get_api_key routing
# ---------------------------------------------------------------------------

class TestGetApiKeyRouting:
    @pytest.mark.asyncio
    async def test_missing_header_raises_401(self):
        mock_db = AsyncMock()
        with pytest.raises(HTTPException) as exc_info:
            await get_api_key(mock_db, None)
        assert exc_info.value.status_code == 401
        assert "Missing API key" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_bad_prefix_raises_401(self):
        mock_db = AsyncMock()
        with pytest.raises(HTTPException) as exc_info:
            await get_api_key(mock_db, "sk_live_wrongprefix")
        assert exc_info.value.status_code == 401
        assert "dk_live_" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_routes_to_unkey_when_configured(self):
        ctx = AuthContext(key_id="unkey-routed", source="unkey")

        with patch(
            "deckforge.api.middleware.auth.settings"
        ) as mock_settings, patch(
            "deckforge.api.middleware.auth._verify_via_unkey",
            return_value=ctx,
        ) as mock_unkey:
            mock_settings.UNKEY_ROOT_KEY = "root_key_123"
            mock_db = AsyncMock()
            result = await get_api_key(mock_db, "dk_live_test")

        mock_unkey.assert_called_once_with("dk_live_test")
        assert result.source == "unkey"

    @pytest.mark.asyncio
    async def test_falls_back_to_db_when_unkey_not_set(self):
        ctx = AuthContext(key_id="db-routed", source="db")

        with patch(
            "deckforge.api.middleware.auth.settings"
        ) as mock_settings, patch(
            "deckforge.api.middleware.auth._verify_via_db",
            return_value=ctx,
        ) as mock_db_verify:
            mock_settings.UNKEY_ROOT_KEY = None
            mock_db = AsyncMock()
            result = await get_api_key(mock_db, "dk_live_test")

        mock_db_verify.assert_called_once_with(mock_db, "dk_live_test")
        assert result.source == "db"
