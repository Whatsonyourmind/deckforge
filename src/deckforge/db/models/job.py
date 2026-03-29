"""Job model for tracking async task execution."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from deckforge.db.base import Base


class Job(Base):
    """An async job tracked by the task queue.

    Jobs are created when a render or generate request is queued to ARQ.
    Status progression: queued -> running -> complete | failed.
    """

    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    deck_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("decks.id"),
        default=None,
    )
    api_key_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("api_keys.id"),
    )
    job_type: Mapped[str] = mapped_column(String(20))
    queue_name: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), default="queued")
    progress: Mapped[float] = mapped_column(default=0.0)
    result: Mapped[dict | None] = mapped_column(JSON, default=None)
    error_message: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(default=None)
    completed_at: Mapped[datetime | None] = mapped_column(default=None)

    def __repr__(self) -> str:
        return f"<Job {self.id} type={self.job_type} status={self.status}>"
