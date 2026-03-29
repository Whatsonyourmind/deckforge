"""Analytics repository for aggregated usage and revenue queries.

Provides efficient SQL aggregations for the analytics dashboard:
overview metrics, endpoint breakdown, top consumers, and revenue timeseries.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from deckforge.db.models.payment_event import PaymentEvent
from deckforge.db.models.usage import UsageRecord


class AnalyticsRepository:
    """Data access layer for analytics aggregate queries.

    All methods return plain dicts (not ORM models) for serialization.
    """

    async def get_overview(
        self,
        session: AsyncSession,
        days: int = 30,
    ) -> dict:
        """Get high-level overview metrics for the analytics dashboard.

        Returns total API calls, Stripe revenue, x402 revenue, and active consumers
        for the specified period.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Total API calls and Stripe credit usage from usage_records
        usage_stmt = select(
            func.count(UsageRecord.id).label("total_records"),
            func.coalesce(func.sum(UsageRecord.credits_used), 0).label(
                "total_credits"
            ),
            func.count(func.distinct(UsageRecord.api_key_id)).label(
                "active_consumers"
            ),
        ).where(UsageRecord.created_at >= cutoff)

        usage_result = await session.execute(usage_stmt)
        usage_row = usage_result.one()

        # x402 revenue from payment_events
        x402_stmt = select(
            func.coalesce(func.sum(PaymentEvent.amount_usd), Decimal("0")).label(
                "x402_revenue"
            ),
        ).where(
            PaymentEvent.created_at >= cutoff,
            PaymentEvent.status == "settled",
        )

        x402_result = await session.execute(x402_stmt)
        x402_row = x402_result.one()

        total_credits = int(usage_row.total_credits)
        # Estimate Stripe revenue: credits_used * average overage rate ($0.30)
        stripe_revenue = round(float(total_credits) * 0.30, 2)
        x402_revenue = round(float(x402_row.x402_revenue), 2)

        return {
            "total_calls": int(usage_row.total_records),
            "stripe_revenue_usd": stripe_revenue,
            "x402_revenue_usd": x402_revenue,
            "total_revenue_usd": round(stripe_revenue + x402_revenue, 2),
            "active_consumers": int(usage_row.active_consumers),
            "period_days": days,
        }

    async def get_endpoint_breakdown(
        self,
        session: AsyncSession,
        days: int = 30,
    ) -> list[dict]:
        """Get API call and credit breakdown grouped by endpoint.

        Uses payment_events endpoint field for x402 calls and
        a fixed 'subscription' label for credit-based usage.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # x402 endpoint breakdown from payment_events
        x402_stmt = (
            select(
                PaymentEvent.endpoint.label("endpoint"),
                func.count(PaymentEvent.id).label("calls"),
                func.coalesce(func.sum(PaymentEvent.amount_usd), 0).label(
                    "credits_used"
                ),
            )
            .where(
                PaymentEvent.created_at >= cutoff,
                PaymentEvent.status == "settled",
            )
            .group_by(PaymentEvent.endpoint)
            .order_by(func.count(PaymentEvent.id).desc())
        )

        x402_result = await session.execute(x402_stmt)
        rows = x402_result.all()

        breakdown: list[dict] = []

        # Add subscription usage as a single entry
        usage_stmt = select(
            func.count(UsageRecord.id).label("calls"),
            func.coalesce(func.sum(UsageRecord.credits_used), 0).label(
                "credits_used"
            ),
        ).where(UsageRecord.created_at >= cutoff)

        usage_result = await session.execute(usage_stmt)
        usage_row = usage_result.one()

        if int(usage_row.calls) > 0:
            breakdown.append(
                {
                    "endpoint": "subscription (all endpoints)",
                    "calls": int(usage_row.calls),
                    "credits_used": int(usage_row.credits_used),
                }
            )

        for row in rows:
            breakdown.append(
                {
                    "endpoint": row.endpoint,
                    "calls": int(row.calls),
                    "credits_used": int(row.credits_used),
                }
            )

        return breakdown

    async def get_top_consumers(
        self,
        session: AsyncSession,
        days: int = 30,
        limit: int = 20,
    ) -> list[dict]:
        """Get top API consumers ranked by call count.

        Groups by api_key_id from usage_records.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = (
            select(
                UsageRecord.api_key_id.label("api_key_id"),
                func.count(UsageRecord.id).label("calls"),
                func.coalesce(func.sum(UsageRecord.credits_used), 0).label(
                    "credits_used"
                ),
                UsageRecord.tier.label("tier"),
            )
            .where(UsageRecord.created_at >= cutoff)
            .group_by(UsageRecord.api_key_id, UsageRecord.tier)
            .order_by(func.count(UsageRecord.id).desc())
            .limit(limit)
        )

        result = await session.execute(stmt)
        rows = result.all()

        return [
            {
                "api_key_id": str(row.api_key_id),
                "calls": int(row.calls),
                "credits_used": int(row.credits_used),
                "tier": row.tier,
            }
            for row in rows
        ]

    async def get_revenue_timeseries(
        self,
        session: AsyncSession,
        days: int = 30,
        granularity: str = "daily",
    ) -> list[dict]:
        """Get revenue timeseries data for charting.

        Returns Stripe and x402 revenue per day/week/month.
        Uses Python-side date grouping for SQLite compatibility.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Fetch all payment events in range
        x402_stmt = (
            select(PaymentEvent.created_at, PaymentEvent.amount_usd)
            .where(
                PaymentEvent.created_at >= cutoff,
                PaymentEvent.status == "settled",
            )
            .order_by(PaymentEvent.created_at)
        )
        x402_result = await session.execute(x402_stmt)
        x402_rows = x402_result.all()

        # Fetch all usage records in range
        usage_stmt = (
            select(UsageRecord.created_at, UsageRecord.credits_used)
            .where(UsageRecord.created_at >= cutoff)
            .order_by(UsageRecord.created_at)
        )
        usage_result = await session.execute(usage_stmt)
        usage_rows = usage_result.all()

        # Aggregate by date key
        def _date_key(dt: datetime) -> str:
            if granularity == "weekly":
                # ISO week start (Monday)
                start = dt - timedelta(days=dt.weekday())
                return start.strftime("%Y-%m-%d")
            elif granularity == "monthly":
                return dt.strftime("%Y-%m-01")
            else:
                return dt.strftime("%Y-%m-%d")

        buckets: dict[str, dict] = {}

        for row in usage_rows:
            key = _date_key(row.created_at)
            if key not in buckets:
                buckets[key] = {"stripe": 0.0, "x402": 0.0}
            buckets[key]["stripe"] += float(row.credits_used) * 0.30

        for row in x402_rows:
            key = _date_key(row.created_at)
            if key not in buckets:
                buckets[key] = {"stripe": 0.0, "x402": 0.0}
            buckets[key]["x402"] += float(row.amount_usd)

        timeseries: list[dict] = []
        for date_str in sorted(buckets.keys()):
            b = buckets[date_str]
            timeseries.append(
                {
                    "date": date_str,
                    "stripe_revenue_usd": round(b["stripe"], 2),
                    "x402_revenue_usd": round(b["x402"], 2),
                    "total_revenue_usd": round(b["stripe"] + b["x402"], 2),
                }
            )

        return timeseries
