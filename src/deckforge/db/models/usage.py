"""Usage tracking models for billing: UsageRecord and CreditReservation.

UsageRecord tracks per-API-key credit usage within a monthly billing period.
CreditReservation tracks individual credit reservations for renders.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from deckforge.db.base import Base


class UsageRecord(Base):
    """Monthly credit usage record for an API key.

    Tracks credit limits, usage, and reservations within a billing period.
    The unique constraint on (api_key_id, period_start) ensures one record per
    API key per billing cycle.
    """

    __tablename__ = "usage_records"
    __table_args__ = (
        UniqueConstraint(
            "api_key_id",
            "period_start",
            name="uq_usage_records_api_key_id_period_start",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    api_key_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("api_keys.id"),
    )
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    credit_limit: Mapped[int] = mapped_column()
    credits_used: Mapped[int] = mapped_column(insert_default=0)
    credits_reserved: Mapped[int] = mapped_column(insert_default=0)
    tier: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    def __init__(self, **kwargs):
        kwargs.setdefault("credits_used", 0)
        kwargs.setdefault("credits_reserved", 0)
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return (
            f"<UsageRecord {self.api_key_id} "
            f"period={self.period_start} "
            f"used={self.credits_used}/{self.credit_limit}>"
        )


class CreditReservation(Base):
    """Individual credit reservation for a render job.

    Status lifecycle: reserved -> completed | cancelled | expired.
    """

    __tablename__ = "credit_reservations"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    api_key_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("api_keys.id"),
    )
    usage_record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usage_records.id"),
    )
    amount: Mapped[int] = mapped_column()
    status: Mapped[str] = mapped_column(String(20), default="reserved")
    deck_id: Mapped[uuid.UUID | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(default=None)

    def __repr__(self) -> str:
        return (
            f"<CreditReservation {self.id} "
            f"amount={self.amount} status={self.status}>"
        )
