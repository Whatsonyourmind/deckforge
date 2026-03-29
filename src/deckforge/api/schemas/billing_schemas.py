"""Billing API response schemas for usage dashboard and Stripe checkout."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class UsageSummaryResponse(BaseModel):
    """Current billing period usage summary."""

    tier: str = Field(description="Current billing tier name")
    credit_limit: int = Field(description="Total credits for this period")
    credits_used: int = Field(description="Credits consumed this period")
    credits_reserved: int = Field(description="Credits reserved for in-flight renders")
    credits_available: int = Field(description="Credits available for new renders")
    period_start: date = Field(description="Billing period start date")
    period_end: date = Field(description="Billing period end date")
    overage_rate: int = Field(description="Overage rate in cents per credit")


class UsagePeriod(BaseModel):
    """Usage summary for a single billing period."""

    period_start: date = Field(description="Period start date")
    credits_used: int = Field(description="Credits consumed")
    credit_limit: int = Field(description="Credit limit for the period")
    overage_credits: int = Field(
        description="Credits used beyond the limit (0 if within limit)"
    )
    overage_cost: int = Field(
        description="Overage cost in cents (overage_credits * overage_rate)"
    )


class UsageHistoryResponse(BaseModel):
    """Historical usage across billing periods."""

    periods: list[UsagePeriod] = Field(description="Usage by billing period")


class UpgradeRequest(BaseModel):
    """Request to upgrade billing tier."""

    tier: str = Field(description="Target tier name (pro, enterprise)")
    success_url: str = Field(
        default="https://app.deckforge.dev/billing?success=true",
        description="URL to redirect after successful checkout",
    )
    cancel_url: str = Field(
        default="https://app.deckforge.dev/billing?cancelled=true",
        description="URL to redirect if checkout is cancelled",
    )


class CheckoutResponse(BaseModel):
    """Response with Stripe checkout session URL."""

    checkout_url: str = Field(description="Stripe checkout session URL")


class PortalResponse(BaseModel):
    """Response with Stripe billing portal URL."""

    portal_url: str = Field(description="Stripe billing portal URL")
