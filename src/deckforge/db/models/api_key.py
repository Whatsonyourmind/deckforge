"""API key model for authentication and authorization."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from deckforge.db.base import Base


class ApiKey(Base):
    """An API key belonging to a user.

    Keys are stored as SHA-256 hashes. The key_prefix (e.g. "dk_live_abc...")
    is stored for display purposes so users can identify which key is which
    without exposing the full key.
    """

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
    )
    key_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
    )
    key_prefix: Mapped[str] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(100))
    scopes: Mapped[list[str]] = mapped_column(
        JSON,
        default=lambda: ["read", "generate"],
    )
    tier: Mapped[str] = mapped_column(String(20), default="starter")
    is_active: Mapped[bool] = mapped_column(default=True)
    is_test: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    last_used_at: Mapped[datetime | None] = mapped_column(default=None)
    google_refresh_token: Mapped[str | None] = mapped_column(
        String(512), default=None
    )

    def __repr__(self) -> str:
        return f"<ApiKey {self.key_prefix}>"
