#!/usr/bin/env python3
"""Configure Stripe products, prices, and webhook for DeckForge.

Creates:
  - 3 products: Starter, Pro, Enterprise
  - Monthly prices: $0, $79, custom
  - Metered usage component
  - Webhook endpoint for /v1/billing/webhook

Usage:
  export STRIPE_SECRET_KEY=sk_test_...
  python scripts/setup-stripe.py
  python scripts/setup-stripe.py --webhook-url https://deckforge.fly.dev/v1/billing/webhook
  python scripts/setup-stripe.py --live  # Use live mode (careful!)
"""

import argparse
import os
import sys

try:
    import stripe
except ImportError:
    print("ERROR: stripe package not installed. Run: pip install stripe")
    sys.exit(1)


def create_products_and_prices(client: stripe.StripeClient) -> dict:
    """Create DeckForge products and prices in Stripe."""
    products = {}

    # Starter (Free)
    starter = client.products.create(params={
        "name": "DeckForge Starter",
        "description": "Free tier: 50 credits/month, 10 req/min",
        "metadata": {"tier": "starter", "credits": "50"},
    })
    starter_price = client.prices.create(params={
        "product": starter.id,
        "unit_amount": 0,
        "currency": "usd",
        "recurring": {"interval": "month"},
        "metadata": {"tier": "starter"},
    })
    products["starter"] = {"product_id": starter.id, "price_id": starter_price.id}
    print(f"  Starter: product={starter.id}, price={starter_price.id}")

    # Pro ($79/mo)
    pro = client.products.create(params={
        "name": "DeckForge Pro",
        "description": "Pro tier: 500 credits/month, 60 req/min, $79/month",
        "metadata": {"tier": "pro", "credits": "500"},
    })
    pro_price = client.prices.create(params={
        "product": pro.id,
        "unit_amount": 7900,
        "currency": "usd",
        "recurring": {"interval": "month"},
        "metadata": {"tier": "pro"},
    })
    products["pro"] = {"product_id": pro.id, "price_id": pro_price.id}
    print(f"  Pro: product={pro.id}, price={pro_price.id}")

    # Enterprise (custom pricing -- create product only)
    enterprise = client.products.create(params={
        "name": "DeckForge Enterprise",
        "description": "Enterprise tier: 10,000 credits/month, 300 req/min, custom pricing",
        "metadata": {"tier": "enterprise", "credits": "10000"},
    })
    products["enterprise"] = {"product_id": enterprise.id, "price_id": None}
    print(f"  Enterprise: product={enterprise.id} (custom pricing)")

    # Metered usage component (overage billing)
    metered_price = client.prices.create(params={
        "product": pro.id,
        "unit_amount": 30,  # $0.30 per overage credit
        "currency": "usd",
        "recurring": {"interval": "month", "usage_type": "metered"},
        "metadata": {"type": "overage"},
    })
    products["overage"] = {"price_id": metered_price.id}
    print(f"  Overage metered price: {metered_price.id}")

    return products


def create_webhook(client: stripe.StripeClient, url: str) -> str:
    """Create webhook endpoint for billing event processing."""
    endpoint = client.webhook_endpoints.create(params={
        "url": url,
        "enabled_events": [
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
            "invoice.payment_succeeded",
            "invoice.payment_failed",
        ],
        "description": "DeckForge billing webhook",
    })
    print(f"  Webhook: {endpoint.id}")
    print(f"  Secret: {endpoint.secret}")
    return endpoint.secret


def main():
    parser = argparse.ArgumentParser(description="Setup Stripe for DeckForge")
    parser.add_argument(
        "--webhook-url",
        default="https://deckforge.fly.dev/v1/billing/webhook",
        help="Webhook endpoint URL",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use live mode (default: test)",
    )
    parser.add_argument(
        "--skip-webhook",
        action="store_true",
        help="Skip webhook creation",
    )
    args = parser.parse_args()

    api_key = os.environ.get("STRIPE_SECRET_KEY") or os.environ.get(
        "DECKFORGE_STRIPE_SECRET_KEY"
    )
    if not api_key:
        print(
            "ERROR: Set STRIPE_SECRET_KEY or DECKFORGE_STRIPE_SECRET_KEY "
            "environment variable"
        )
        print("  Get your key from: https://dashboard.stripe.com/apikeys")
        sys.exit(1)

    if not args.live and not api_key.startswith("sk_test_"):
        print("ERROR: Expected test key (sk_test_...) unless --live flag is set")
        sys.exit(1)

    if args.live and not api_key.startswith("sk_live_"):
        print("ERROR: --live flag requires live key (sk_live_...)")
        sys.exit(1)

    client = stripe.StripeClient(api_key)

    print("=== DeckForge Stripe Setup ===")
    print(f"Mode: {'LIVE' if args.live else 'TEST'}")
    print()

    print("[1/2] Creating products and prices...")
    products = create_products_and_prices(client)
    print()

    webhook_secret = None
    if not args.skip_webhook:
        print("[2/2] Creating webhook endpoint...")
        webhook_secret = create_webhook(client, args.webhook_url)
    else:
        print("[2/2] Skipping webhook creation")
    print()

    print("=== Setup Complete ===")
    print()
    print("Add these to your .env or fly secrets:")
    print(f"  DECKFORGE_STRIPE_SECRET_KEY={api_key}")
    print(f"  DECKFORGE_STRIPE_STARTER_PRICE_ID={products['starter']['price_id']}")
    print(f"  DECKFORGE_STRIPE_PRO_PRICE_ID={products['pro']['price_id']}")
    if webhook_secret:
        print(f"  DECKFORGE_STRIPE_WEBHOOK_SECRET={webhook_secret}")
    print()
    print("For Fly.io:")
    print(f"  fly secrets set DECKFORGE_STRIPE_SECRET_KEY={api_key}")
    print(
        f"  fly secrets set DECKFORGE_STRIPE_STARTER_PRICE_ID="
        f"{products['starter']['price_id']}"
    )
    print(
        f"  fly secrets set DECKFORGE_STRIPE_PRO_PRICE_ID="
        f"{products['pro']['price_id']}"
    )
    if webhook_secret:
        print(
            f"  fly secrets set DECKFORGE_STRIPE_WEBHOOK_SECRET={webhook_secret}"
        )


if __name__ == "__main__":
    main()
