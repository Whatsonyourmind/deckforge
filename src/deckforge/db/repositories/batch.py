"""Repository for batch job database operations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from deckforge.db.models.batch_job import BatchJob


class BatchRepository:
    """Data access layer for BatchJob operations."""

    async def create(
        self,
        session: AsyncSession,
        *,
        api_key_id: uuid.UUID,
        total_items: int,
        webhook_url: str | None = None,
    ) -> BatchJob:
        """Create a new batch job record."""
        batch = BatchJob(
            api_key_id=api_key_id,
            total_items=total_items,
            webhook_url=webhook_url,
        )
        session.add(batch)
        await session.flush()
        return batch

    async def get_by_id(
        self,
        session: AsyncSession,
        batch_id: uuid.UUID,
    ) -> BatchJob | None:
        """Look up a batch job by its UUID."""
        stmt = select(BatchJob).where(BatchJob.id == batch_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def increment_completed(
        self,
        session: AsyncSession,
        batch_id: uuid.UUID,
    ) -> BatchJob:
        """Atomically increment completed_items.

        If completed_items + failed_items == total_items, set status to
        'complete' (all succeeded) or 'partial_failure' (some failed) and
        record completed_at.
        """
        # Atomic increment
        stmt = (
            update(BatchJob)
            .where(BatchJob.id == batch_id)
            .values(completed_items=BatchJob.completed_items + 1)
        )
        await session.execute(stmt)
        await session.flush()

        # Reload to check completion
        batch = await self.get_by_id(session, batch_id)
        if batch is None:
            raise ValueError(f"BatchJob {batch_id} not found")

        # Check if all items are done
        total_done = batch.completed_items + batch.failed_items
        if total_done >= batch.total_items:
            new_status = (
                "complete" if batch.failed_items == 0 else "partial_failure"
            )
            finish_stmt = (
                update(BatchJob)
                .where(BatchJob.id == batch_id)
                .values(
                    status=new_status,
                    completed_at=datetime.now(timezone.utc),
                )
            )
            await session.execute(finish_stmt)
            await session.flush()
            batch = await self.get_by_id(session, batch_id)
        elif batch.status == "pending":
            # First completion -- mark as running
            run_stmt = (
                update(BatchJob)
                .where(BatchJob.id == batch_id)
                .values(status="running")
            )
            await session.execute(run_stmt)
            await session.flush()
            batch = await self.get_by_id(session, batch_id)

        return batch  # type: ignore[return-value]

    async def increment_failed(
        self,
        session: AsyncSession,
        batch_id: uuid.UUID,
    ) -> BatchJob:
        """Atomically increment failed_items.

        If completed_items + failed_items == total_items, set status to
        'failed' (all failed) or 'partial_failure' (some succeeded).
        """
        stmt = (
            update(BatchJob)
            .where(BatchJob.id == batch_id)
            .values(failed_items=BatchJob.failed_items + 1)
        )
        await session.execute(stmt)
        await session.flush()

        batch = await self.get_by_id(session, batch_id)
        if batch is None:
            raise ValueError(f"BatchJob {batch_id} not found")

        total_done = batch.completed_items + batch.failed_items
        if total_done >= batch.total_items:
            new_status = (
                "failed" if batch.completed_items == 0 else "partial_failure"
            )
            finish_stmt = (
                update(BatchJob)
                .where(BatchJob.id == batch_id)
                .values(
                    status=new_status,
                    completed_at=datetime.now(timezone.utc),
                )
            )
            await session.execute(finish_stmt)
            await session.flush()
            batch = await self.get_by_id(session, batch_id)

        return batch  # type: ignore[return-value]

    async def list_by_api_key(
        self,
        session: AsyncSession,
        api_key_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> list[BatchJob]:
        """List batch jobs belonging to an API key, paginated."""
        stmt = (
            select(BatchJob)
            .where(BatchJob.api_key_id == api_key_id)
            .order_by(BatchJob.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
