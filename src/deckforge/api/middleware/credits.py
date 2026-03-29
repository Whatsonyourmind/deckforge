"""Credit check middleware for gating API endpoints by credit balance.

CreditCheck is a FastAPI dependency that reserves credits before a render
starts. CreditDeduct and CreditRelease handle post-render accounting.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, HTTPException, Request, status

from deckforge.api.deps import DbSession
from deckforge.api.middleware.auth import CurrentApiKey
from deckforge.billing.credits import CreditManager, InsufficientCreditsError
from deckforge.db.repositories import usage_repo

if TYPE_CHECKING:
    import uuid

    from deckforge.db.models.usage import CreditReservation

logger = logging.getLogger(__name__)


def _get_credit_manager() -> CreditManager:
    """Create a CreditManager with the usage repository singleton."""
    return CreditManager(usage_repo=usage_repo)


async def credit_check(
    request: Request,
    db: DbSession,
    api_key: CurrentApiKey,
) -> None:
    """FastAPI dependency that reserves credits before processing.

    Steps:
    1. Estimate credit cost from the request body (uses slide count heuristic).
    2. Call CreditManager.reserve() to atomically reserve credits.
    3. Store the reservation in request.state for later deduction.
    4. Raise 402 Payment Required if insufficient credits.

    This dependency should be added to render and generate route signatures.
    """
    # Estimate credits from request body
    # For render: body is a Presentation IR, count slides
    # For generate: use a default estimate (will be refined after generation)
    body = await request.body()

    try:
        import json

        body_data = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        body_data = {}

    slides = body_data.get("slides", [])
    slide_count = len(slides)

    # Quick estimate: 1 credit per 10 slides, minimum 1
    import math

    estimated_credits = max(1, math.ceil(slide_count / 10)) if slide_count > 0 else 1

    manager = _get_credit_manager()
    tier = api_key.tier

    try:
        reservation = await manager.reserve(
            session=db,
            api_key_id=api_key.id,
            tier=tier,
            estimated_credits=estimated_credits,
        )
        # Store reservation for later deduction/release
        request.state.credit_reservation = reservation
        request.state.credit_manager = manager
        request.state.estimated_credits = estimated_credits
    except InsufficientCreditsError as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "insufficient_credits",
                "available": e.available,
                "requested": e.requested,
                "message": str(e),
                "upgrade_url": "/v1/billing/checkout",
            },
        )


CreditCheck = Annotated[None, Depends(credit_check)]


async def credit_deduct(
    request: Request,
    db: DbSession,
    actual_credits: int,
    customer_id: str | None = None,
) -> None:
    """Deduct credits after a successful render.

    Converts the reservation to actual usage. Call this after
    the render completes successfully.

    Args:
        request: The FastAPI request (must have credit_reservation on state).
        db: Database session.
        actual_credits: The actual number of credits consumed.
        customer_id: Optional Stripe customer ID for meter reporting.
    """
    reservation = getattr(request.state, "credit_reservation", None)
    manager = getattr(request.state, "credit_manager", None)

    if reservation is None or manager is None:
        logger.warning("credit_deduct called without active reservation")
        return

    await manager.deduct(
        session=db,
        reservation_id=reservation.id,
        actual_credits=actual_credits,
        customer_id=customer_id,
    )


async def credit_release(
    request: Request,
    db: DbSession,
) -> None:
    """Release reserved credits on render failure.

    Restores the reserved credits back to the user's balance.

    Args:
        request: The FastAPI request (must have credit_reservation on state).
        db: Database session.
    """
    reservation = getattr(request.state, "credit_reservation", None)
    manager = getattr(request.state, "credit_manager", None)

    if reservation is None or manager is None:
        logger.warning("credit_release called without active reservation")
        return

    await manager.release(
        session=db,
        reservation_id=reservation.id,
    )
