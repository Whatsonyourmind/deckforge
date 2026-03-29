"""Stripe API wrapper for subscriptions and metered usage.

Handles customer creation, subscription management, checkout sessions,
billing portal, and credit usage meter reporting.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import stripe

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class StripeClient:
    """Wrapper around the Stripe Python SDK for billing operations.

    Args:
        api_key: Stripe secret API key (sk_test_... or sk_live_...).
    """

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client = stripe.StripeClient(api_key)

    async def create_customer(
        self,
        email: str,
        name: str,
        tier: str,
    ) -> Any:
        """Create a Stripe customer.

        Args:
            email: Customer email address.
            name: Customer display name.
            tier: The DeckForge billing tier.

        Returns:
            The Stripe Customer object.
        """
        try:
            customer = self._client.customers.create(
                params={
                    "email": email,
                    "name": name,
                    "metadata": {"tier": tier, "source": "deckforge"},
                }
            )
            return customer
        except stripe.StripeError as e:
            logger.error("Stripe create_customer failed: %s", e)
            raise

    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
    ) -> Any:
        """Create a subscription for a customer.

        Args:
            customer_id: The Stripe customer ID.
            price_id: The Stripe price ID for the tier.

        Returns:
            The Stripe Subscription object.
        """
        try:
            subscription = self._client.subscriptions.create(
                params={
                    "customer": customer_id,
                    "items": [{"price": price_id}],
                }
            )
            return subscription
        except stripe.StripeError as e:
            logger.error("Stripe create_subscription failed: %s", e)
            raise

    async def cancel_subscription(self, subscription_id: str) -> None:
        """Cancel a subscription.

        Args:
            subscription_id: The Stripe subscription ID.
        """
        try:
            self._client.subscriptions.cancel(subscription_id)
        except stripe.StripeError as e:
            logger.error("Stripe cancel_subscription failed: %s", e)
            raise

    async def report_usage(
        self,
        customer_id: str,
        credits_used: int,
    ) -> None:
        """Report credit usage to Stripe billing meter.

        Creates a meter event for the deckforge_credit_usage meter.

        Args:
            customer_id: The Stripe customer ID.
            credits_used: Number of credits consumed.
        """
        try:
            self._client.billing.meter_events.create(
                params={
                    "event_name": "deckforge_credit_usage",
                    "payload": {
                        "value": str(credits_used),
                        "stripe_customer_id": customer_id,
                    },
                }
            )
        except stripe.StripeError as e:
            logger.warning(
                "Stripe meter event failed for customer %s: %s",
                customer_id,
                e,
            )
            raise

    async def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
    ) -> str:
        """Create a Stripe Checkout session for tier upgrade.

        Args:
            customer_id: The Stripe customer ID.
            price_id: The Stripe price ID for the target tier.
            success_url: URL to redirect on successful checkout.
            cancel_url: URL to redirect on cancelled checkout.

        Returns:
            The checkout session URL.
        """
        try:
            session = self._client.checkout.sessions.create(
                params={
                    "customer": customer_id,
                    "mode": "subscription",
                    "line_items": [{"price": price_id, "quantity": 1}],
                    "success_url": success_url,
                    "cancel_url": cancel_url,
                }
            )
            return session.url or ""
        except stripe.StripeError as e:
            logger.error("Stripe checkout session failed: %s", e)
            raise

    async def create_portal_session(
        self,
        customer_id: str,
        return_url: str,
    ) -> str:
        """Create a Stripe Billing Portal session.

        Args:
            customer_id: The Stripe customer ID.
            return_url: URL to redirect when user exits the portal.

        Returns:
            The billing portal URL.
        """
        try:
            session = self._client.billing_portal.sessions.create(
                params={
                    "customer": customer_id,
                    "return_url": return_url,
                }
            )
            return session.url or ""
        except stripe.StripeError as e:
            logger.error("Stripe portal session failed: %s", e)
            raise
