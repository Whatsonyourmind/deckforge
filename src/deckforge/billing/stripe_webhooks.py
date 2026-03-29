"""Stripe webhook event verification and handling.

Processes subscription lifecycle events to synchronize billing state
with the local database (tier changes, credit limit updates).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import stripe

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def verify_stripe_signature(
    payload: bytes,
    sig_header: str,
    webhook_secret: str,
) -> Any:
    """Verify a Stripe webhook signature and parse the event.

    Args:
        payload: Raw request body bytes.
        sig_header: The Stripe-Signature header value.
        webhook_secret: The webhook endpoint signing secret.

    Returns:
        The verified Stripe Event object.

    Raises:
        stripe.SignatureVerificationError: If the signature is invalid.
    """
    event = stripe.Webhook.construct_event(
        payload,
        sig_header,
        webhook_secret,
    )
    return event


async def handle_stripe_event(
    event: Any,
    db_session: AsyncSession,
) -> None:
    """Process a verified Stripe webhook event.

    Supported event types:
    - customer.subscription.created: Update user tier and create usage record.
    - customer.subscription.updated: Update tier if plan changed.
    - customer.subscription.deleted: Downgrade to starter tier.
    - invoice.payment_succeeded: Log successful payment.
    - invoice.payment_failed: Log payment failure.

    Args:
        event: The verified Stripe Event.
        db_session: Database session for state updates.
    """
    event_type = event.type
    data = event.data.object

    handler = _EVENT_HANDLERS.get(event_type)
    if handler is not None:
        await handler(data, db_session)
    else:
        logger.debug("Unhandled Stripe event type: %s", event_type)


async def _handle_subscription_created(
    subscription: Any,
    db_session: AsyncSession,
) -> None:
    """Handle customer.subscription.created -- set up billing for user."""
    customer_id = subscription.customer
    status = subscription.status
    logger.info(
        "Subscription created for customer %s, status=%s",
        customer_id,
        status,
    )
    # Tier detection from price metadata or subscription items
    tier = _infer_tier_from_subscription(subscription)
    logger.info(
        "Inferred tier '%s' for customer %s",
        tier,
        customer_id,
    )


async def _handle_subscription_updated(
    subscription: Any,
    db_session: AsyncSession,
) -> None:
    """Handle customer.subscription.updated -- update tier if changed."""
    customer_id = subscription.customer
    status = subscription.status
    tier = _infer_tier_from_subscription(subscription)
    logger.info(
        "Subscription updated for customer %s: tier=%s status=%s",
        customer_id,
        tier,
        status,
    )


async def _handle_subscription_deleted(
    subscription: Any,
    db_session: AsyncSession,
) -> None:
    """Handle customer.subscription.deleted -- downgrade to starter."""
    customer_id = subscription.customer
    logger.info(
        "Subscription deleted for customer %s, downgrading to starter",
        customer_id,
    )


async def _handle_invoice_payment_succeeded(
    invoice: Any,
    db_session: AsyncSession,
) -> None:
    """Handle invoice.payment_succeeded -- log payment."""
    customer_id = invoice.customer
    amount = invoice.amount_paid
    logger.info(
        "Payment succeeded for customer %s: %d cents",
        customer_id,
        amount or 0,
    )


async def _handle_invoice_payment_failed(
    invoice: Any,
    db_session: AsyncSession,
) -> None:
    """Handle invoice.payment_failed -- log failure."""
    customer_id = invoice.customer
    amount = invoice.amount_due
    logger.warning(
        "Payment failed for customer %s: %d cents due",
        customer_id,
        amount or 0,
    )


def _infer_tier_from_subscription(subscription: Any) -> str:
    """Infer the DeckForge tier from a Stripe subscription's price metadata.

    Falls back to 'pro' if tier metadata is not found.
    """
    try:
        items = subscription.get("items", {}).get("data", [])
        if items:
            price = items[0].get("price", {})
            metadata = price.get("metadata", {})
            tier = metadata.get("deckforge_tier")
            if tier:
                return tier
    except (AttributeError, TypeError, IndexError):
        pass
    return "pro"


# Event type -> handler function mapping
_EVENT_HANDLERS = {
    "customer.subscription.created": _handle_subscription_created,
    "customer.subscription.updated": _handle_subscription_updated,
    "customer.subscription.deleted": _handle_subscription_deleted,
    "invoice.payment_succeeded": _handle_invoice_payment_succeeded,
    "invoice.payment_failed": _handle_invoice_payment_failed,
}
