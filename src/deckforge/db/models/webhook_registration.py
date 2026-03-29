"""WebhookRegistration model for storing user webhook subscriptions."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from deckforge.db.base import Base


class WebhookRegistration(Base):
    """A registered webhook endpoint for async event delivery.

    Users register URLs with a list of event types they want to receive.
    Each registration gets an auto-generated HMAC secret for payload signing.
    """

    __tablename__ = "webhook_registrations"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    api_key_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("api_keys.id"),
    )
    url: Mapped[str] = mapped_column(String(512))
    events: Mapped[list] = mapped_column(JSON, default=list)
    secret: Mapped[str] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    def __repr__(self) -> str:
        return f"<WebhookRegistration {self.id} url={self.url}>"
