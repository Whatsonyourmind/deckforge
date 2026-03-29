"""Repository for API key database operations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from deckforge.db.models.api_key import ApiKey


class ApiKeyRepository:
    """Data access layer for ApiKey operations."""

    async def get_by_hash(
        self,
        session: AsyncSession,
        key_hash: str,
    ) -> ApiKey | None:
        """Look up an API key by its SHA-256 hash."""
        stmt = select(ApiKey).where(ApiKey.key_hash == key_hash)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(
        self,
        session: AsyncSession,
        key_id: uuid.UUID,
    ) -> ApiKey | None:
        """Look up an API key by its UUID."""
        stmt = select(ApiKey).where(ApiKey.id == key_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        session: AsyncSession,
        *,
        user_id: uuid.UUID,
        key_hash: str,
        key_prefix: str,
        name: str,
        scopes: list[str] | None = None,
        tier: str = "starter",
        is_test: bool = False,
    ) -> ApiKey:
        """Create a new API key."""
        api_key = ApiKey(
            user_id=user_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name,
            scopes=scopes or ["read", "generate"],
            tier=tier,
            is_test=is_test,
        )
        session.add(api_key)
        await session.flush()
        return api_key

    async def deactivate(
        self,
        session: AsyncSession,
        key_id: uuid.UUID,
    ) -> bool:
        """Deactivate an API key. Returns True if the key was found and deactivated."""
        stmt = (
            update(ApiKey)
            .where(ApiKey.id == key_id, ApiKey.is_active.is_(True))
            .values(is_active=False)
        )
        result = await session.execute(stmt)
        await session.flush()
        return result.rowcount > 0

    async def update_last_used(
        self,
        session: AsyncSession,
        key_id: uuid.UUID,
    ) -> None:
        """Update the last_used_at timestamp for an API key."""
        stmt = (
            update(ApiKey)
            .where(ApiKey.id == key_id)
            .values(last_used_at=datetime.now(timezone.utc))
        )
        await session.execute(stmt)
        await session.flush()
