"""Deck model for storing generated presentations."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from deckforge.db.base import Base


class Deck(Base):
    """A generated presentation deck.

    The ir_snapshot stores the full Intermediate Representation (IR) as JSONB,
    enabling deterministic re-rendering and version tracking.
    """

    __tablename__ = "decks"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    request_id: Mapped[str | None] = mapped_column(
        String(64),
        unique=True,
        index=True,
        default=None,
    )
    api_key_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("api_keys.id"),
    )
    ir_snapshot: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
    )
    file_url: Mapped[str | None] = mapped_column(
        String(512),
        default=None,
    )
    quality_score: Mapped[int | None] = mapped_column(default=None)
    error_message: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(default=None)

    def __repr__(self) -> str:
        return f"<Deck {self.id} status={self.status}>"
