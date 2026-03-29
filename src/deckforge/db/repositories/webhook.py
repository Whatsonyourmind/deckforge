"""Repository for webhook registration database operations."""

from __future__ import annotations

import secrets
import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from deckforge.db.models.webhook_registration import WebhookRegistration


class WebhookRepository:
    """Data access layer for WebhookRegistration operations."""

    async def create(
        self,
        session: AsyncSession,
        *,
        api_key_id: uuid.UUID,
        url: str,
        events: list[str],
        secret: str | None = None,
    ) -> WebhookRegistration:
        """Create a new webhook registration.

        Auto-generates a 64-char hex HMAC secret if not provided.
        """
        if secret is None:
            secret = secrets.token_hex(32)

        reg = WebhookRegistration(
            api_key_id=api_key_id,
            url=url,
            events=events,
            secret=secret,
        )
        session.add(reg)
        await session.flush()
        return reg

    async def get_by_id(
        self,
        session: AsyncSession,
        webhook_id: uuid.UUID,
    ) -> WebhookRegistration | None:
        """Look up a webhook registration by its UUID."""
        stmt = select(WebhookRegistration).where(
            WebhookRegistration.id == webhook_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_api_key(
        self,
        session: AsyncSession,
        api_key_id: uuid.UUID,
    ) -> list[WebhookRegistration]:
        """List all webhook registrations for an API key."""
        stmt = (
            select(WebhookRegistration)
            .where(
                WebhookRegistration.api_key_id == api_key_id,
                WebhookRegistration.is_active.is_(True),
            )
            .order_by(WebhookRegistration.created_at.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_event(
        self,
        session: AsyncSession,
        api_key_id: uuid.UUID,
        event_type: str,
    ) -> list[WebhookRegistration]:
        """Get active webhooks subscribed to a specific event type.

        Uses JSON contains check on the events column. For SQLite
        compatibility, falls back to loading all webhooks for the key
        and filtering in Python.
        """
        # Load all active webhooks for this key and filter in Python
        # This approach is portable across SQLite and PostgreSQL
        all_hooks = await self.get_by_api_key(session, api_key_id)
        return [h for h in all_hooks if event_type in (h.events or [])]

    async def delete(
        self,
        session: AsyncSession,
        webhook_id: uuid.UUID,
    ) -> None:
        """Delete a webhook registration."""
        stmt = delete(WebhookRegistration).where(
            WebhookRegistration.id == webhook_id
        )
        await session.execute(stmt)
        await session.flush()
