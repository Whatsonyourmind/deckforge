"""Repository for job database operations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from deckforge.db.models.job import Job


class JobRepository:
    """Data access layer for Job operations."""

    async def get_by_id(
        self,
        session: AsyncSession,
        job_id: uuid.UUID,
    ) -> Job | None:
        """Look up a job by its UUID."""
        stmt = select(Job).where(Job.id == job_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        session: AsyncSession,
        *,
        api_key_id: uuid.UUID,
        job_type: str,
        queue_name: str,
        deck_id: uuid.UUID | None = None,
    ) -> Job:
        """Create a new job record."""
        job = Job(
            api_key_id=api_key_id,
            job_type=job_type,
            queue_name=queue_name,
            deck_id=deck_id,
        )
        session.add(job)
        await session.flush()
        return job

    async def update_status(
        self,
        session: AsyncSession,
        job_id: uuid.UUID,
        status: str,
        *,
        progress: float | None = None,
        result: dict | None = None,
        error: str | None = None,
    ) -> None:
        """Update job status and optional progress/result fields."""
        values: dict = {"status": status}
        if progress is not None:
            values["progress"] = progress
        if result is not None:
            values["result"] = result
        if error is not None:
            values["error_message"] = error
        if status == "running":
            values["started_at"] = datetime.now(timezone.utc)
        if status in ("complete", "failed"):
            values["completed_at"] = datetime.now(timezone.utc)

        stmt = update(Job).where(Job.id == job_id).values(**values)
        await session.execute(stmt)
        await session.flush()

    async def get_active_jobs(
        self,
        session: AsyncSession,
        api_key_id: uuid.UUID,
    ) -> list[Job]:
        """Get all active (queued or running) jobs for an API key."""
        stmt = (
            select(Job)
            .where(
                Job.api_key_id == api_key_id,
                Job.status.in_(["queued", "running"]),
            )
            .order_by(Job.created_at.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
