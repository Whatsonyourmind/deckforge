"""Repository for usage record and credit reservation database operations.

Provides atomic credit reservation, deduction, and release using
SELECT FOR UPDATE to prevent race conditions on concurrent renders.
"""

from __future__ import annotations

import calendar
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from deckforge.billing.tiers import get_tier
from deckforge.db.models.usage import CreditReservation, UsageRecord


class UsageRepository:
    """Data access layer for usage records and credit reservations."""

    async def get_or_create_current(
        self,
        session: AsyncSession,
        api_key_id: uuid.UUID,
        tier: str,
    ) -> UsageRecord:
        """Get or create the usage record for the current billing period.

        The billing period is the current calendar month.

        Args:
            session: Database session.
            api_key_id: The API key to track usage for.
            tier: The billing tier name (used for credit limit lookup).

        Returns:
            The current month's UsageRecord.
        """
        today = date.today()
        period_start = today.replace(day=1)

        stmt = select(UsageRecord).where(
            UsageRecord.api_key_id == api_key_id,
            UsageRecord.period_start == period_start,
        )
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()

        if record is not None:
            return record

        # Create new record for this billing period
        tier_config = get_tier(tier)
        _, last_day = calendar.monthrange(today.year, today.month)
        period_end = today.replace(day=last_day)

        record = UsageRecord(
            api_key_id=api_key_id,
            period_start=period_start,
            period_end=period_end,
            credit_limit=tier_config.credit_limit,
            tier=tier,
        )
        session.add(record)
        await session.flush()
        return record

    async def reserve_credits(
        self,
        session: AsyncSession,
        usage_record_id: uuid.UUID,
        amount: int,
    ) -> CreditReservation:
        """Atomically reserve credits on a usage record.

        Uses SELECT FOR UPDATE to prevent race conditions when multiple
        renders are submitted concurrently.

        Args:
            session: Database session.
            usage_record_id: The usage record to reserve against.
            amount: Number of credits to reserve.

        Returns:
            The new CreditReservation record.
        """
        # Lock the usage record for update
        stmt = (
            select(UsageRecord)
            .where(UsageRecord.id == usage_record_id)
            .with_for_update()
        )
        result = await session.execute(stmt)
        record = result.scalar_one()

        # Increment reserved credits
        record.credits_reserved += amount
        await session.flush()

        # Create reservation record
        reservation = CreditReservation(
            api_key_id=record.api_key_id,
            usage_record_id=usage_record_id,
            amount=amount,
            status="reserved",
        )
        session.add(reservation)
        await session.flush()
        return reservation

    async def deduct_credits(
        self,
        session: AsyncSession,
        reservation_id: uuid.UUID,
        actual_amount: int,
    ) -> None:
        """Convert a reservation to actual usage.

        Decrements credits_reserved by the reservation amount,
        increments credits_used by the actual amount, and marks
        the reservation as completed.

        Args:
            session: Database session.
            reservation_id: The reservation to complete.
            actual_amount: The actual credits consumed.
        """
        # Get the reservation
        stmt = select(CreditReservation).where(CreditReservation.id == reservation_id)
        result = await session.execute(stmt)
        reservation = result.scalar_one()

        # Update the usage record
        usage_stmt = (
            select(UsageRecord)
            .where(UsageRecord.id == reservation.usage_record_id)
            .with_for_update()
        )
        usage_result = await session.execute(usage_stmt)
        record = usage_result.scalar_one()

        record.credits_reserved -= reservation.amount
        record.credits_used += actual_amount
        await session.flush()

        # Mark reservation completed
        reservation.status = "completed"
        reservation.completed_at = datetime.now(timezone.utc)
        await session.flush()

    async def release_credits(
        self,
        session: AsyncSession,
        reservation_id: uuid.UUID,
    ) -> None:
        """Release reserved credits back (failed render).

        Decrements credits_reserved and marks reservation as cancelled.

        Args:
            session: Database session.
            reservation_id: The reservation to cancel.
        """
        # Get the reservation
        stmt = select(CreditReservation).where(CreditReservation.id == reservation_id)
        result = await session.execute(stmt)
        reservation = result.scalar_one()

        # Update the usage record
        usage_stmt = (
            select(UsageRecord)
            .where(UsageRecord.id == reservation.usage_record_id)
            .with_for_update()
        )
        usage_result = await session.execute(usage_stmt)
        record = usage_result.scalar_one()

        record.credits_reserved -= reservation.amount
        await session.flush()

        # Mark reservation cancelled
        reservation.status = "cancelled"
        reservation.completed_at = datetime.now(timezone.utc)
        await session.flush()

    async def get_usage_history(
        self,
        session: AsyncSession,
        api_key_id: uuid.UUID,
        limit: int = 12,
    ) -> list[UsageRecord]:
        """Get usage history for an API key.

        Returns the last N months of usage records, most recent first.

        Args:
            session: Database session.
            api_key_id: The API key to get history for.
            limit: Maximum number of periods to return.

        Returns:
            List of UsageRecord objects, most recent first.
        """
        stmt = (
            select(UsageRecord)
            .where(UsageRecord.api_key_id == api_key_id)
            .order_by(UsageRecord.period_start.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
