"""Billing API routes: usage dashboard, checkout, portal, and Stripe webhook.

Provides endpoints for:
- GET /v1/billing/usage: Current period credit usage summary
- GET /v1/billing/usage/history: Last 12 months of usage history
- POST /v1/billing/checkout: Create Stripe checkout session for tier upgrade
- POST /v1/billing/portal: Create Stripe billing portal session
- POST /v1/stripe/webhook: Stripe webhook receiver
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Header, Request, status

from deckforge.api.deps import DbSession
from deckforge.api.middleware.auth import CurrentApiKey
from deckforge.api.schemas.billing_schemas import (
    CheckoutResponse,
    PortalResponse,
    UpgradeRequest,
    UsageHistoryResponse,
    UsagePeriod,
    UsageSummaryResponse,
)
from deckforge.billing.tiers import get_tier
from deckforge.db.repositories import usage_repo

logger = logging.getLogger(__name__)

router = APIRouter(tags=["billing"])


@router.get(
    "/billing/usage",
    response_model=UsageSummaryResponse,
    responses={
        200: {"description": "Current billing period usage summary"},
        401: {"description": "Invalid or missing API key"},
    },
)
async def get_usage(
    db: DbSession,
    api_key: CurrentApiKey,
) -> UsageSummaryResponse:
    """Get current billing period credit usage summary.

    Returns the credit limit, usage, reservations, and availability
    for the current calendar month billing period.
    """
    tier_name = api_key.tier
    tier = get_tier(tier_name)

    record = await usage_repo.get_or_create_current(db, api_key.uuid_id, tier_name)

    available = max(0, record.credit_limit - record.credits_used - record.credits_reserved)

    return UsageSummaryResponse(
        tier=tier_name,
        credit_limit=record.credit_limit,
        credits_used=record.credits_used,
        credits_reserved=record.credits_reserved,
        credits_available=available,
        period_start=record.period_start,
        period_end=record.period_end,
        overage_rate=tier.overage_rate_cents,
    )


@router.get(
    "/billing/usage/history",
    response_model=UsageHistoryResponse,
    responses={
        200: {"description": "Historical usage across billing periods"},
        401: {"description": "Invalid or missing API key"},
    },
)
async def get_usage_history(
    db: DbSession,
    api_key: CurrentApiKey,
) -> UsageHistoryResponse:
    """Get usage history for the last 12 billing periods.

    Returns credit usage, limits, and overage costs per period.
    """
    records = await usage_repo.get_usage_history(db, api_key.uuid_id, limit=12)

    periods = []
    for record in records:
        tier = get_tier(record.tier)
        overage_credits = max(0, record.credits_used - record.credit_limit)
        overage_cost = overage_credits * tier.overage_rate_cents

        periods.append(
            UsagePeriod(
                period_start=record.period_start,
                credits_used=record.credits_used,
                credit_limit=record.credit_limit,
                overage_credits=overage_credits,
                overage_cost=overage_cost,
            )
        )

    return UsageHistoryResponse(periods=periods)


@router.post(
    "/billing/checkout",
    response_model=CheckoutResponse,
    responses={
        200: {"description": "Stripe checkout session URL"},
        400: {"description": "Stripe not configured or invalid tier"},
        401: {"description": "Invalid or missing API key"},
    },
)
async def create_checkout(
    body: UpgradeRequest,
    api_key: CurrentApiKey,
) -> CheckoutResponse:
    """Create a Stripe Checkout session for tier upgrade.

    Returns a URL that the user should be redirected to in order to
    complete the subscription purchase.
    """
    from deckforge.config import settings

    stripe_key = getattr(settings, "STRIPE_SECRET_KEY", None)
    if not stripe_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe is not configured. Set DECKFORGE_STRIPE_SECRET_KEY.",
        )

    # Validate target tier
    try:
        tier = get_tier(body.tier)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown tier: {body.tier}",
        )

    if tier.stripe_price_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tier '{body.tier}' does not have a Stripe price configured.",
        )

    from deckforge.billing.stripe_client import StripeClient

    client = StripeClient(stripe_key)

    # Use the user_id from the API key as the customer reference
    customer_id = getattr(api_key, "stripe_customer_id", None) or ""
    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Stripe customer ID associated with this API key. "
            "Contact support to set up billing.",
        )

    checkout_url = await client.create_checkout_session(
        customer_id=customer_id,
        price_id=tier.stripe_price_id,
        success_url=body.success_url,
        cancel_url=body.cancel_url,
    )

    return CheckoutResponse(checkout_url=checkout_url)


@router.post(
    "/billing/portal",
    response_model=PortalResponse,
    responses={
        200: {"description": "Stripe billing portal URL"},
        400: {"description": "Stripe not configured"},
        401: {"description": "Invalid or missing API key"},
    },
)
async def create_portal(
    api_key: CurrentApiKey,
) -> PortalResponse:
    """Create a Stripe Billing Portal session.

    Returns a URL for the user to manage their subscription,
    payment methods, and billing history.
    """
    from deckforge.config import settings

    stripe_key = getattr(settings, "STRIPE_SECRET_KEY", None)
    if not stripe_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe is not configured. Set DECKFORGE_STRIPE_SECRET_KEY.",
        )

    customer_id = getattr(api_key, "stripe_customer_id", None) or ""
    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Stripe customer ID associated with this API key.",
        )

    from deckforge.billing.stripe_client import StripeClient

    client = StripeClient(stripe_key)

    portal_url = await client.create_portal_session(
        customer_id=customer_id,
        return_url="https://app.deckforge.dev/billing",
    )

    return PortalResponse(portal_url=portal_url)


@router.post(
    "/stripe/webhook",
    status_code=200,
    responses={
        200: {"description": "Webhook processed"},
        400: {"description": "Invalid signature or payload"},
    },
)
async def stripe_webhook(
    request: Request,
    db: DbSession,
    stripe_signature: str = Header(alias="Stripe-Signature"),
) -> dict:
    """Receive and process Stripe webhook events.

    Verifies the webhook signature using the webhook secret,
    then dispatches to the appropriate event handler.
    """
    from deckforge.billing.stripe_webhooks import (
        handle_stripe_event,
        verify_stripe_signature,
    )
    from deckforge.config import settings

    webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", None)
    if not webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe webhook secret not configured.",
        )

    payload = await request.body()

    try:
        event = verify_stripe_signature(payload, stripe_signature, webhook_secret)
    except Exception as e:
        logger.warning("Stripe webhook signature verification failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature.",
        )

    await handle_stripe_event(event, db)
    await db.commit()

    return {"status": "ok"}
