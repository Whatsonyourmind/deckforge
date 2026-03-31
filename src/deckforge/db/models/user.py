"""User model for DeckForge accounts."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from deckforge.db.base import Base


class User(Base):
    """A registered DeckForge user."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(unique=True, index=True)
    name: Mapped[str | None] = mapped_column(default=None)
    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(64), default=None
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        default=None,
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
