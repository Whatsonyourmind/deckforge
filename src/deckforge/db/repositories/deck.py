"""Repository for deck database operations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from deckforge.db.models.deck import Deck


class DeckRepository:
    """Data access layer for Deck operations."""

    async def get_by_id(
        self,
        session: AsyncSession,
        deck_id: uuid.UUID,
    ) -> Deck | None:
        """Look up a deck by its UUID."""
        stmt = select(Deck).where(Deck.id == deck_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_request_id(
        self,
        session: AsyncSession,
        request_id: str,
    ) -> Deck | None:
        """Look up a deck by its idempotency request_id."""
        stmt = select(Deck).where(Deck.request_id == request_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        session: AsyncSession,
        *,
        api_key_id: uuid.UUID,
        ir_snapshot: dict,
        request_id: str | None = None,
    ) -> Deck:
        """Create a new deck record."""
        deck = Deck(
            api_key_id=api_key_id,
            ir_snapshot=ir_snapshot,
            request_id=request_id,
        )
        session.add(deck)
        await session.flush()
        return deck

    async def update_status(
        self,
        session: AsyncSession,
        deck_id: uuid.UUID,
        status: str,
        *,
        file_url: str | None = None,
        quality_score: int | None = None,
        error: str | None = None,
    ) -> None:
        """Update deck status and optional completion fields."""
        values: dict = {"status": status}
        if file_url is not None:
            values["file_url"] = file_url
        if quality_score is not None:
            values["quality_score"] = quality_score
        if error is not None:
            values["error_message"] = error
        if status in ("complete", "failed"):
            values["completed_at"] = datetime.now(timezone.utc)

        stmt = update(Deck).where(Deck.id == deck_id).values(**values)
        await session.execute(stmt)
        await session.flush()
