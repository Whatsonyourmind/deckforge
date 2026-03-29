"""Tests for x402 payment middleware and pricing configuration."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from deckforge.api.middleware.auth import AuthContext
from deckforge.billing.x402_config import get_all_prices, get_x402_price


# ---------------------------------------------------------------------------
# x402_config price lookup
# ---------------------------------------------------------------------------

class TestX402PriceLookup:
    def test_render_price(self):
        price = get_x402_price("POST", "/v1/render")
        assert price == "0.05"

    def test_generate_price(self):
        price = get_x402_price("POST", "/v1/generate")
        assert price == "0.10"

    def test_batch_price(self):
        price = get_x402_price("POST", "/v1/batch")
        assert price == "0.08"

    def test_preview_price(self):
        price = get_x402_price("POST", "/v1/render/preview")
        assert price == "0.02"

    def test_unknown_route_returns_none(self):
        price = get_x402_price("GET", "/v1/health")
        assert price is None

    def test_wrong_method_returns_none(self):
        price = get_x402_price("GET", "/v1/render")
        assert price is None

    def test_case_insensitive_method(self):
        price = get_x402_price("post", "/v1/render")
        assert price == "0.05"


class TestGetAllPrices:
    def test_returns_all_endpoints(self):
        prices = get_all_prices()
        assert "POST /v1/render" in prices
        assert "POST /v1/generate" in prices
        assert "POST /v1/batch" in prices
        assert "POST /v1/render/preview" in prices

    def test_price_structure(self):
        prices = get_all_prices()
        render_price = prices["POST /v1/render"]
        assert "price_usd" in render_price
        assert "description" in render_price
        assert render_price["price_usd"] == "0.05"

    def test_all_prices_have_descriptions(self):
        prices = get_all_prices()
        for key, val in prices.items():
            assert val["description"], f"Missing description for {key}"


# ---------------------------------------------------------------------------
# x402_or_apikey_auth preference logic
# ---------------------------------------------------------------------------

class TestDualAuthPreference:
    @pytest.mark.asyncio
    async def test_payment_sig_preferred_over_api_key(self):
        """When both headers are present and x402 is enabled, payment wins."""
        from deckforge.api.middleware.x402 import x402_or_apikey_auth

        mock_request = MagicMock()
        mock_request.method = "POST"
        mock_request.url.path = "/v1/render"

        x402_ctx = AuthContext(
            key_id="x402:pay-001",
            tier="x402",
            payment_settled=True,
            source="x402",
        )

        with patch(
            "deckforge.api.middleware.x402.settings"
        ) as mock_settings, patch(
            "deckforge.api.middleware.x402._verify_x402_payment",
            return_value=x402_ctx,
        ) as mock_verify:
            mock_settings.X402_ENABLED = True
            mock_settings.X402_WALLET_ADDRESS = "0x123"
            mock_settings.X402_FACILITATOR_URL = "https://x402.org/facilitator"
            mock_settings.X402_NETWORK = "eip155:8453"

            result = await x402_or_apikey_auth(
                request=mock_request,
                payment_sig="sig-data-here",
                api_key_header="dk_live_test",
            )

        assert result.source == "x402"
        assert result.payment_settled is True
        mock_verify.assert_called_once()

    @pytest.mark.asyncio
    async def test_api_key_used_when_no_payment_sig(self):
        """When only X-API-Key is present, delegate to standard auth."""
        from deckforge.api.middleware.x402 import x402_or_apikey_auth

        mock_request = MagicMock()
        mock_request.method = "POST"
        mock_request.url.path = "/v1/render"

        api_ctx = AuthContext(key_id="key-123", tier="pro", source="unkey")

        with patch(
            "deckforge.api.middleware.x402.get_api_key",
            return_value=api_ctx,
        ), patch(
            "deckforge.api.middleware.x402.get_db",
        ) as mock_get_db:
            # Mock the async generator
            async def fake_get_db():
                yield AsyncMock()

            mock_get_db.side_effect = fake_get_db

            result = await x402_or_apikey_auth(
                request=mock_request,
                payment_sig=None,
                api_key_header="dk_live_test",
            )

        assert result.source == "unkey"
        assert result.tier == "pro"

    @pytest.mark.asyncio
    async def test_missing_both_headers_returns_402(self):
        """When neither header is present, return 402 with pricing info."""
        from deckforge.api.middleware.x402 import x402_or_apikey_auth

        mock_request = MagicMock()
        mock_request.method = "POST"
        mock_request.url.path = "/v1/render"

        with patch(
            "deckforge.api.middleware.x402.settings"
        ) as mock_settings:
            mock_settings.X402_ENABLED = False
            mock_settings.X402_WALLET_ADDRESS = "0x123"
            mock_settings.X402_FACILITATOR_URL = "https://x402.org/facilitator"
            mock_settings.X402_NETWORK = "eip155:8453"

            with pytest.raises(HTTPException) as exc_info:
                await x402_or_apikey_auth(
                    request=mock_request,
                    payment_sig=None,
                    api_key_header=None,
                )

        assert exc_info.value.status_code == 402
        detail = exc_info.value.detail
        assert detail["error"] == "payment_required"
        assert "x402" in detail
        assert "api_key" in detail

    @pytest.mark.asyncio
    async def test_x402_disabled_falls_through_to_api_key(self):
        """When x402 is disabled, PAYMENT-SIGNATURE is ignored; API key used."""
        from deckforge.api.middleware.x402 import x402_or_apikey_auth

        mock_request = MagicMock()
        mock_request.method = "POST"
        mock_request.url.path = "/v1/render"

        api_ctx = AuthContext(key_id="key-456", tier="starter", source="db")

        with patch(
            "deckforge.api.middleware.x402.settings"
        ) as mock_settings, patch(
            "deckforge.api.middleware.x402.get_api_key",
            return_value=api_ctx,
        ), patch(
            "deckforge.api.middleware.x402.get_db",
        ) as mock_get_db:
            mock_settings.X402_ENABLED = False

            async def fake_get_db():
                yield AsyncMock()

            mock_get_db.side_effect = fake_get_db

            result = await x402_or_apikey_auth(
                request=mock_request,
                payment_sig="sig-ignored",
                api_key_header="dk_live_test",
            )

        assert result.source == "db"
