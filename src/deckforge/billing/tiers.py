"""Billing tier definitions for DeckForge.

Three tiers: Starter (free), Pro ($79/mo), Enterprise (custom).
Each tier has credit limits, overage rates, and rate limits.
"""

from __future__ import annotations

from pydantic import BaseModel


class Tier(BaseModel):
    """A billing tier with credit limits and pricing."""

    name: str
    display_name: str
    credit_limit: int
    price_cents: int
    overage_rate_cents: int
    rate_limit: int  # requests per minute
    stripe_price_id: str | None = None


TIERS: dict[str, Tier] = {
    "starter": Tier(
        name="starter",
        display_name="Starter",
        credit_limit=50,
        price_cents=0,
        overage_rate_cents=50,
        rate_limit=10,
    ),
    "pro": Tier(
        name="pro",
        display_name="Pro",
        credit_limit=500,
        price_cents=7900,
        overage_rate_cents=30,
        rate_limit=60,
    ),
    "enterprise": Tier(
        name="enterprise",
        display_name="Enterprise",
        credit_limit=10000,
        price_cents=0,
        overage_rate_cents=10,
        rate_limit=300,
    ),
}


def get_tier(name: str) -> Tier:
    """Look up a tier by name.

    Args:
        name: Tier name (starter, pro, enterprise).

    Returns:
        The Tier configuration.

    Raises:
        KeyError: If tier name is not recognized.
    """
    return TIERS[name]
