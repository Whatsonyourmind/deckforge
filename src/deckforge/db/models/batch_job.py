"""BatchJob model for tracking batch render operations."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from deckforge.db.base import Base


class BatchJob(Base):
    """A batch of render jobs processed as a group.

    Tracks total, completed, and failed sub-job counts. Status
    transitions: pending -> running -> complete | partial_failure | failed.
    """

    __tablename__ = "batch_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    api_key_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("api_keys.id"),
    )
    total_items: Mapped[int] = mapped_column()
    completed_items: Mapped[int] = mapped_column(default=0)
    failed_items: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    webhook_url: Mapped[str | None] = mapped_column(
        String(512), default=None
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(default=None)

    def __repr__(self) -> str:
        return (
            f"<BatchJob {self.id} "
            f"status={self.status} "
            f"{self.completed_items}/{self.total_items}>"
        )
