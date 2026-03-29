"""x402 per-call pricing configuration.

Maps API route patterns to USD prices for machine-to-machine payments.
AI agents pay per-call in USDC on Base L2 via the x402 protocol.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class X402Price:
    """A per-call price for an API route."""

    method: str
    path_pattern: str
    price_usd: str
    description: str


# Route-to-price mapping for x402 per-call payments.
# Prices are strings representing USD amounts (USDC equivalent on Base L2).
X402_PRICES: list[X402Price] = [
    X402Price(
        method="POST",
        path_pattern="/v1/render",
        price_usd="0.05",
        description="Render IR to PPTX/Google Slides",
    ),
    X402Price(
        method="POST",
        path_pattern="/v1/generate",
        price_usd="0.10",
        description="Generate presentation from natural language",
    ),
    X402Price(
        method="POST",
        path_pattern="/v1/batch",
        price_usd="0.08",
        description="Batch render multiple decks",
    ),
    X402Price(
        method="POST",
        path_pattern="/v1/render/preview",
        price_usd="0.02",
        description="Generate slide preview thumbnails",
    ),
]


def get_x402_price(method: str, path: str) -> str | None:
    """Look up the x402 per-call price for a given HTTP method and path.

    Args:
        method: HTTP method (e.g., "POST", "GET").
        path: Request path (e.g., "/v1/render").

    Returns:
        Price as a USD string (e.g., "0.05") or None if no price defined.
    """
    method_upper = method.upper()
    for price in X402_PRICES:
        if price.method == method_upper and re.match(
            f"^{re.escape(price.path_pattern)}$", path
        ):
            return price.price_usd
    return None


def get_all_prices() -> dict[str, dict[str, str]]:
    """Return all x402 prices as a dict for the /v1/pricing endpoint.

    Returns:
        Dict mapping "METHOD /path" to {price_usd, description}.
    """
    return {
        f"{p.method} {p.path_pattern}": {
            "price_usd": p.price_usd,
            "description": p.description,
        }
        for p in X402_PRICES
    }
