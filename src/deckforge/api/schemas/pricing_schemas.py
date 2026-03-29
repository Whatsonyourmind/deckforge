"""Pydantic schemas for the GET /v1/pricing endpoint.

Machine-readable pricing response consumed by AI agents to decide
between per-call x402 payment and subscription-based API key access.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PricingTier(BaseModel):
    """A subscription tier with limits and pricing."""

    name: str = Field(description="Tier identifier (starter, pro, enterprise)")
    display_name: str = Field(description="Human-readable tier name")
    price_monthly_usd: float | None = Field(
        description="Monthly subscription price in USD (None for enterprise/custom)"
    )
    credits_included: int = Field(description="Credits included per month")
    rate_limit_per_min: int = Field(description="API requests per minute")
    overage_rate_usd: float = Field(
        description="Cost per credit beyond included amount, in USD"
    )


class X402PerCallPricing(BaseModel):
    """x402 protocol per-call pricing for machine-to-machine payments."""

    currency: str = Field(default="USDC", description="Payment currency")
    network: str = Field(
        default="eip155:8453", description="Blockchain network (Base Mainnet)"
    )
    facilitator: str = Field(description="x402 facilitator service URL")
    prices: dict[str, dict[str, str]] = Field(
        description="Endpoint-to-price mapping: {'METHOD /path': {price_usd, description}}"
    )


class PricingResponse(BaseModel):
    """Complete pricing response for the GET /v1/pricing endpoint.

    Designed for agent consumption: an AI can parse this response
    to decide whether to pay per-call (x402) or obtain an API key.
    """

    tiers: list[PricingTier] = Field(description="Available subscription tiers")
    x402_per_call: X402PerCallPricing = Field(
        description="Per-call payment pricing via x402 protocol"
    )
