"""Usage analytics routes.

Provides dashboard endpoints for monitoring API usage and revenue.
All endpoints require enterprise tier or admin API key.

GET /v1/analytics          - Full dashboard (overview + breakdown + consumers + revenue)
GET /v1/analytics/overview - High-level metrics
GET /v1/analytics/endpoints - Breakdown by endpoint
GET /v1/analytics/consumers - Top consumers by call count
GET /v1/analytics/revenue  - Revenue timeseries
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from deckforge.api.deps import DbSession
from deckforge.api.middleware.auth import CurrentApiKey
from deckforge.api.schemas.analytics_schemas import (
    AnalyticsResponse,
    ConsumerBreakdown,
    EndpointBreakdown,
    OverviewResponse,
    RevenueDatapoint,
)
from deckforge.db.repositories.analytics import AnalyticsRepository

router = APIRouter(tags=["analytics"])

analytics_repo = AnalyticsRepository()


def _require_admin(api_key: CurrentApiKey) -> None:
    """Enforce admin/enterprise access for analytics endpoints.

    Raises 403 if the API key tier is not enterprise and the key
    does not have the 'admin' scope.
    """
    is_enterprise = api_key.tier == "enterprise"
    is_admin = "admin" in (api_key.scopes or [])

    if not is_enterprise and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analytics access requires enterprise tier or admin scope.",
        )


@router.get(
    "/analytics/overview",
    response_model=OverviewResponse,
    summary="Analytics overview metrics",
)
async def get_overview(
    api_key: CurrentApiKey,
    db: DbSession,
    days: int = Query(default=30, ge=1, le=365),
) -> OverviewResponse:
    """Get high-level analytics: total calls, revenue split, active consumers."""
    _require_admin(api_key)
    data = await analytics_repo.get_overview(db, days=days)
    return OverviewResponse(**data)


@router.get(
    "/analytics/endpoints",
    response_model=list[EndpointBreakdown],
    summary="Endpoint usage breakdown",
)
async def get_endpoints(
    api_key: CurrentApiKey,
    db: DbSession,
    days: int = Query(default=30, ge=1, le=365),
) -> list[EndpointBreakdown]:
    """Get API call breakdown grouped by endpoint."""
    _require_admin(api_key)
    data = await analytics_repo.get_endpoint_breakdown(db, days=days)
    return [EndpointBreakdown(**row) for row in data]


@router.get(
    "/analytics/consumers",
    response_model=list[ConsumerBreakdown],
    summary="Top API consumers",
)
async def get_consumers(
    api_key: CurrentApiKey,
    db: DbSession,
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[ConsumerBreakdown]:
    """Get top API consumers ranked by call count."""
    _require_admin(api_key)
    data = await analytics_repo.get_top_consumers(db, days=days, limit=limit)
    return [ConsumerBreakdown(**row) for row in data]


@router.get(
    "/analytics/revenue",
    response_model=list[RevenueDatapoint],
    summary="Revenue timeseries",
)
async def get_revenue(
    api_key: CurrentApiKey,
    db: DbSession,
    days: int = Query(default=30, ge=1, le=365),
    granularity: str = Query(default="daily", pattern="^(daily|weekly|monthly)$"),
) -> list[RevenueDatapoint]:
    """Get revenue timeseries with Stripe/x402 split."""
    _require_admin(api_key)
    data = await analytics_repo.get_revenue_timeseries(
        db, days=days, granularity=granularity
    )
    return [RevenueDatapoint(**row) for row in data]


@router.get(
    "/analytics",
    response_model=AnalyticsResponse,
    summary="Full analytics dashboard",
)
async def get_full_analytics(
    api_key: CurrentApiKey,
    db: DbSession,
    days: int = Query(default=30, ge=1, le=365),
) -> AnalyticsResponse:
    """Get the complete analytics dashboard in a single call.

    Combines overview, endpoint breakdown, top consumers, and revenue trend.
    """
    _require_admin(api_key)

    overview = await analytics_repo.get_overview(db, days=days)
    endpoints = await analytics_repo.get_endpoint_breakdown(db, days=days)
    consumers = await analytics_repo.get_top_consumers(db, days=days)
    revenue = await analytics_repo.get_revenue_timeseries(db, days=days)

    return AnalyticsResponse(
        overview=OverviewResponse(**overview),
        endpoints=[EndpointBreakdown(**row) for row in endpoints],
        top_consumers=[ConsumerBreakdown(**row) for row in consumers],
        revenue_trend=[RevenueDatapoint(**row) for row in revenue],
    )
