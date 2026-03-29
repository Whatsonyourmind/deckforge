"""GET /v1/pricing -- public pricing endpoint.

Returns machine-readable JSON with subscription tier details and x402
per-call prices. No authentication required; this is what agents call
first to decide whether to pay per-call or obtain an API key.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from deckforge.api.schemas.pricing_schemas import (
    PricingResponse,
    PricingTier,
    X402PerCallPricing,
)
from deckforge.billing.tiers import TIERS
from deckforge.billing.x402_config import get_all_prices
from deckforge.config import settings

router = APIRouter(tags=["pricing"])


@router.get(
    "/pricing",
    response_model=PricingResponse,
    summary="Get pricing tiers and per-call rates",
    description=(
        "Returns subscription tiers and x402 per-call pricing. "
        "Public endpoint -- no authentication required. "
        "Agents use this to discover payment options."
    ),
)
async def get_pricing() -> JSONResponse:
    """Build and return the complete pricing response."""
    tiers = [
        PricingTier(
            name=tier.name,
            display_name=tier.display_name,
            price_monthly_usd=tier.price_cents / 100.0 if tier.price_cents > 0 else None,
            credits_included=tier.credit_limit,
            rate_limit_per_min=tier.rate_limit,
            overage_rate_usd=tier.overage_rate_cents / 100.0,
        )
        for tier in TIERS.values()
    ]

    x402_pricing = X402PerCallPricing(
        currency="USDC",
        network=settings.X402_NETWORK,
        facilitator=settings.X402_FACILITATOR_URL,
        prices=get_all_prices(),
    )

    response = PricingResponse(tiers=tiers, x402_per_call=x402_pricing)

    return JSONResponse(
        content=response.model_dump(),
        headers={"Cache-Control": "public, max-age=3600"},
    )
