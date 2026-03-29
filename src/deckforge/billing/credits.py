"""Credit management: reservation, deduction, and release.

Credits are reserved before a render starts, deducted on completion,
and released if the render fails. This ensures concurrent renders
cannot over-consume credits.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

    from deckforge.db.models.usage import CreditReservation
    from deckforge.db.repositories.usage import UsageRepository

logger = logging.getLogger(__name__)


class InsufficientCreditsError(Exception):
    """Raised when a credit reservation exceeds available balance."""

    def __init__(self, available: int, requested: int) -> None:
        self.available = available
        self.requested = requested
        super().__init__(
            f"Insufficient credits: {available} available, {requested} requested"
        )


class CreditManager:
    """Manages credit reservation, deduction, and release lifecycle.

    Args:
        usage_repo: Repository for usage record operations.
        stripe_client: Optional Stripe client for meter event reporting.
    """

    def __init__(
        self,
        usage_repo: UsageRepository,
        stripe_client: object | None = None,
    ) -> None:
        self._usage_repo = usage_repo
        self._stripe_client = stripe_client

    async def reserve(
        self,
        session: AsyncSession,
        api_key_id: uuid.UUID,
        tier: str,
        estimated_credits: int,
    ) -> CreditReservation:
        """Reserve credits before a render starts.

        1. Get or create current usage record for this billing period.
        2. Calculate available = credit_limit - credits_used - credits_reserved.
        3. If insufficient and not enterprise tier, raise InsufficientCreditsError.
        4. Create reservation record atomically.

        Args:
            session: Database session.
            api_key_id: The API key requesting credits.
            tier: The billing tier name.
            estimated_credits: Number of credits to reserve.

        Returns:
            The CreditReservation record.

        Raises:
            InsufficientCreditsError: When balance is too low (non-enterprise).
        """
        record = await self._usage_repo.get_or_create_current(
            session, api_key_id, tier
        )

        available = record.credit_limit - record.credits_used - record.credits_reserved

        # Enterprise tier allows overage
        if estimated_credits > available and tier != "enterprise":
            raise InsufficientCreditsError(
                available=available,
                requested=estimated_credits,
            )

        reservation = await self._usage_repo.reserve_credits(
            session, record.id, estimated_credits
        )
        return reservation

    async def deduct(
        self,
        session: AsyncSession,
        reservation_id: uuid.UUID,
        actual_credits: int,
        customer_id: str | None = None,
    ) -> None:
        """Convert a reservation to actual usage.

        Decrements reserved credits by the reservation amount, increments
        used credits by the actual amount, and reports to Stripe if configured.

        Args:
            session: Database session.
            reservation_id: The reservation to complete.
            actual_credits: The actual number of credits consumed.
            customer_id: Optional Stripe customer ID for meter reporting.
        """
        await self._usage_repo.deduct_credits(session, reservation_id, actual_credits)

        if self._stripe_client is not None and customer_id is not None:
            try:
                await self._stripe_client.report_usage(customer_id, actual_credits)
            except Exception:
                logger.warning(
                    "Failed to report usage to Stripe for customer %s",
                    customer_id,
                    exc_info=True,
                )

    async def release(
        self,
        session: AsyncSession,
        reservation_id: uuid.UUID,
    ) -> None:
        """Release reserved credits back (failed render path).

        Decrements reserved credits and marks reservation as cancelled.

        Args:
            session: Database session.
            reservation_id: The reservation to cancel.
        """
        await self._usage_repo.release_credits(session, reservation_id)
