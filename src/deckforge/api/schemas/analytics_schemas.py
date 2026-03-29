"""Pydantic schemas for usage analytics endpoints.

Covers overview metrics, endpoint breakdown, consumer ranking,
and revenue timeseries for the analytics dashboard.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class OverviewResponse(BaseModel):
    """High-level analytics overview for a given period."""

    total_calls: int = Field(description="Total API calls in period")
    stripe_revenue_usd: float = Field(description="Revenue from Stripe subscriptions")
    x402_revenue_usd: float = Field(description="Revenue from x402 machine payments")
    total_revenue_usd: float = Field(description="Combined revenue")
    active_consumers: int = Field(description="Distinct API keys active in period")
    period_days: int = Field(description="Number of days in analysis window")


class EndpointBreakdown(BaseModel):
    """API call breakdown for a single endpoint."""

    endpoint: str = Field(description="API endpoint path")
    calls: int = Field(description="Number of calls")
    credits_used: int = Field(description="Total credits consumed")


class ConsumerBreakdown(BaseModel):
    """Usage breakdown for a single API consumer."""

    api_key_id: str = Field(description="API key identifier")
    calls: int = Field(description="Number of API calls")
    credits_used: int = Field(description="Total credits consumed")
    tier: str = Field(description="Billing tier")


class RevenueDatapoint(BaseModel):
    """A single point in the revenue timeseries."""

    date: str = Field(description="Date string (YYYY-MM-DD)")
    stripe_revenue_usd: float = Field(description="Stripe revenue for this period")
    x402_revenue_usd: float = Field(description="x402 revenue for this period")
    total_revenue_usd: float = Field(description="Combined revenue for this period")


class AnalyticsResponse(BaseModel):
    """Full analytics dashboard response combining all metrics."""

    overview: OverviewResponse
    endpoints: list[EndpointBreakdown]
    top_consumers: list[ConsumerBreakdown]
    revenue_trend: list[RevenueDatapoint]
