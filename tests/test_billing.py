"""Tests for billing: tier definitions, credit management, and usage models.

Covers:
- Tier lookup and credit limits
- CreditManager reserve/deduct/release cycle
- InsufficientCreditsError when balance too low
- Available credits calculation
- Overage tracking
- UsageRecord monthly period tracking
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── Tier Definition Tests ────────────────────────────────────────────────────


class TestTierDefinitions:
    """Tests for billing tier lookup and configuration."""

    def test_get_tier_starter_returns_correct_limits(self):
        """get_tier('starter') returns Tier with credit_limit=50, overage_rate=50 cents."""
        from deckforge.billing.tiers import get_tier

        tier = get_tier("starter")
        assert tier.name == "starter"
        assert tier.credit_limit == 50
        assert tier.overage_rate_cents == 50

    def test_get_tier_pro_returns_correct_limits(self):
        """get_tier('pro') returns Tier with credit_limit=500, overage_rate=30 cents."""
        from deckforge.billing.tiers import get_tier

        tier = get_tier("pro")
        assert tier.name == "pro"
        assert tier.credit_limit == 500
        assert tier.overage_rate_cents == 30

    def test_get_tier_enterprise_returns_correct_limits(self):
        """get_tier('enterprise') returns Tier with credit_limit=10000."""
        from deckforge.billing.tiers import get_tier

        tier = get_tier("enterprise")
        assert tier.name == "enterprise"
        assert tier.credit_limit == 10000
        assert tier.overage_rate_cents == 10

    def test_get_tier_starter_price_is_zero(self):
        """Starter tier is free ($0)."""
        from deckforge.billing.tiers import get_tier

        tier = get_tier("starter")
        assert tier.price_cents == 0

    def test_get_tier_pro_price_is_7900(self):
        """Pro tier is $79/mo (7900 cents)."""
        from deckforge.billing.tiers import get_tier

        tier = get_tier("pro")
        assert tier.price_cents == 7900

    def test_get_tier_unknown_raises_key_error(self):
        """Requesting an unknown tier raises KeyError."""
        from deckforge.billing.tiers import get_tier

        with pytest.raises(KeyError):
            get_tier("nonexistent")

    def test_tiers_dict_has_three_entries(self):
        """TIERS dict contains exactly starter, pro, enterprise."""
        from deckforge.billing.tiers import TIERS

        assert set(TIERS.keys()) == {"starter", "pro", "enterprise"}

    def test_tier_rate_limits(self):
        """Each tier has correct rate limits."""
        from deckforge.billing.tiers import get_tier

        assert get_tier("starter").rate_limit == 10
        assert get_tier("pro").rate_limit == 60
        assert get_tier("enterprise").rate_limit == 300


# ── CreditManager Tests ─────────────────────────────────────────────────────


class TestCreditManager:
    """Tests for credit reservation, deduction, and release."""

    def _make_usage_record(
        self,
        credit_limit: int = 50,
        credits_used: int = 0,
        credits_reserved: int = 0,
    ):
        """Create a mock UsageRecord."""
        record = MagicMock()
        record.id = uuid.uuid4()
        record.credit_limit = credit_limit
        record.credits_used = credits_used
        record.credits_reserved = credits_reserved
        record.tier = "starter"
        return record

    def _make_reservation(self, amount: int = 5, status: str = "reserved"):
        """Create a mock CreditReservation."""
        reservation = MagicMock()
        reservation.id = uuid.uuid4()
        reservation.amount = amount
        reservation.status = status
        return reservation

    @pytest.mark.asyncio
    async def test_reserve_decrements_available_credits(self):
        """CreditManager.reserve() calls usage_repo.reserve_credits atomically."""
        from deckforge.billing.credits import CreditManager

        usage_repo = AsyncMock()
        record = self._make_usage_record(credit_limit=50, credits_used=10, credits_reserved=5)
        reservation = self._make_reservation(amount=5)

        usage_repo.get_or_create_current.return_value = record
        usage_repo.reserve_credits.return_value = reservation

        manager = CreditManager(usage_repo=usage_repo)
        session = AsyncMock()

        result = await manager.reserve(
            session=session,
            api_key_id=uuid.uuid4(),
            tier="starter",
            estimated_credits=5,
        )

        assert result == reservation
        usage_repo.reserve_credits.assert_called_once_with(session, record.id, 5)

    @pytest.mark.asyncio
    async def test_reserve_raises_insufficient_credits_error(self):
        """CreditManager.reserve() raises InsufficientCreditsError when balance too low."""
        from deckforge.billing.credits import CreditManager, InsufficientCreditsError

        usage_repo = AsyncMock()
        record = self._make_usage_record(credit_limit=50, credits_used=45, credits_reserved=3)
        usage_repo.get_or_create_current.return_value = record

        manager = CreditManager(usage_repo=usage_repo)
        session = AsyncMock()

        with pytest.raises(InsufficientCreditsError) as exc_info:
            await manager.reserve(
                session=session,
                api_key_id=uuid.uuid4(),
                tier="starter",
                estimated_credits=5,
            )

        assert exc_info.value.available == 2  # 50 - 45 - 3
        assert exc_info.value.requested == 5

    @pytest.mark.asyncio
    async def test_deduct_converts_reservation_to_usage(self):
        """CreditManager.deduct() calls usage_repo.deduct_credits."""
        from deckforge.billing.credits import CreditManager

        usage_repo = AsyncMock()
        manager = CreditManager(usage_repo=usage_repo)
        session = AsyncMock()
        reservation_id = uuid.uuid4()

        await manager.deduct(session=session, reservation_id=reservation_id, actual_credits=3)

        usage_repo.deduct_credits.assert_called_once_with(session, reservation_id, 3)

    @pytest.mark.asyncio
    async def test_deduct_reports_to_stripe_when_configured(self):
        """CreditManager.deduct() reports meter event to Stripe when client configured."""
        from deckforge.billing.credits import CreditManager

        usage_repo = AsyncMock()
        stripe_client = AsyncMock()
        manager = CreditManager(usage_repo=usage_repo, stripe_client=stripe_client)
        session = AsyncMock()
        reservation_id = uuid.uuid4()

        await manager.deduct(
            session=session,
            reservation_id=reservation_id,
            actual_credits=3,
            customer_id="cus_test123",
        )

        stripe_client.report_usage.assert_called_once_with("cus_test123", 3)

    @pytest.mark.asyncio
    async def test_release_restores_reserved_credits(self):
        """CreditManager.release() calls usage_repo.release_credits (failed job path)."""
        from deckforge.billing.credits import CreditManager

        usage_repo = AsyncMock()
        manager = CreditManager(usage_repo=usage_repo)
        session = AsyncMock()
        reservation_id = uuid.uuid4()

        await manager.release(session=session, reservation_id=reservation_id)

        usage_repo.release_credits.assert_called_once_with(session, reservation_id)

    @pytest.mark.asyncio
    async def test_available_credits_calculation(self):
        """Available credits = credit_limit - used - reserved."""
        from deckforge.billing.credits import CreditManager

        usage_repo = AsyncMock()
        # 50 limit, 20 used, 10 reserved -> 20 available
        record = self._make_usage_record(credit_limit=50, credits_used=20, credits_reserved=10)
        usage_repo.get_or_create_current.return_value = record

        manager = CreditManager(usage_repo=usage_repo)
        session = AsyncMock()

        # Request exactly 20 -- should succeed
        reservation = self._make_reservation(amount=20)
        usage_repo.reserve_credits.return_value = reservation

        result = await manager.reserve(
            session=session,
            api_key_id=uuid.uuid4(),
            tier="starter",
            estimated_credits=20,
        )
        assert result == reservation

    @pytest.mark.asyncio
    async def test_overage_allowed_for_enterprise(self):
        """Enterprise tier allows overage (used can exceed credit_limit)."""
        from deckforge.billing.credits import CreditManager

        usage_repo = AsyncMock()
        # Enterprise with 10000 limit, 9999 used, 0 reserved -> 1 available
        # But requesting 100 should still succeed because enterprise allows overage
        record = self._make_usage_record(credit_limit=10000, credits_used=9999, credits_reserved=0)
        record.tier = "enterprise"
        usage_repo.get_or_create_current.return_value = record

        reservation = self._make_reservation(amount=100)
        usage_repo.reserve_credits.return_value = reservation

        manager = CreditManager(usage_repo=usage_repo)
        session = AsyncMock()

        result = await manager.reserve(
            session=session,
            api_key_id=uuid.uuid4(),
            tier="enterprise",
            estimated_credits=100,
        )

        assert result == reservation

    @pytest.mark.asyncio
    async def test_overage_not_allowed_for_starter(self):
        """Starter tier does NOT allow overage beyond limit."""
        from deckforge.billing.credits import CreditManager, InsufficientCreditsError

        usage_repo = AsyncMock()
        record = self._make_usage_record(credit_limit=50, credits_used=50, credits_reserved=0)
        usage_repo.get_or_create_current.return_value = record

        manager = CreditManager(usage_repo=usage_repo)
        session = AsyncMock()

        with pytest.raises(InsufficientCreditsError):
            await manager.reserve(
                session=session,
                api_key_id=uuid.uuid4(),
                tier="starter",
                estimated_credits=1,
            )


# ── UsageRecord Model Tests ─────────────────────────────────────────────────


class TestUsageRecordModel:
    """Tests for the UsageRecord database model."""

    def test_usage_record_stores_period_start(self):
        """UsageRecord correctly stores period_start for monthly billing."""
        from deckforge.db.models.usage import UsageRecord

        record = UsageRecord(
            api_key_id=uuid.uuid4(),
            period_start=date(2026, 3, 1),
            period_end=date(2026, 3, 31),
            credit_limit=500,
            credits_used=100,
            credits_reserved=20,
            tier="pro",
        )

        assert record.period_start == date(2026, 3, 1)
        assert record.period_end == date(2026, 3, 31)
        assert record.credit_limit == 500
        assert record.tier == "pro"

    def test_usage_record_default_credits(self):
        """UsageRecord defaults credits_used and credits_reserved to 0."""
        from deckforge.db.models.usage import UsageRecord

        record = UsageRecord(
            api_key_id=uuid.uuid4(),
            period_start=date(2026, 3, 1),
            period_end=date(2026, 3, 31),
            credit_limit=50,
            tier="starter",
        )

        assert record.credits_used == 0
        assert record.credits_reserved == 0

    def test_credit_reservation_model(self):
        """CreditReservation stores reservation details."""
        from deckforge.db.models.usage import CreditReservation

        reservation = CreditReservation(
            api_key_id=uuid.uuid4(),
            usage_record_id=uuid.uuid4(),
            amount=5,
            status="reserved",
        )

        assert reservation.amount == 5
        assert reservation.status == "reserved"
        assert reservation.deck_id is None
