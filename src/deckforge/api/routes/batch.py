"""Batch render endpoints -- fan out multiple IR payloads to individual ARQ jobs.

POST /v1/batch/render  -- Submit N IRs as individual render jobs
POST /v1/batch/variations -- Submit 1 IR x N themes as individual render jobs
GET  /v1/batch/{batch_id} -- Check batch status
"""

from __future__ import annotations

import logging
import uuid

from arq.connections import ArqRedis
from fastapi import APIRouter, HTTPException, status

from deckforge.api.deps import DbSession, RedisClient
from deckforge.api.middleware.auth import CurrentApiKey
from deckforge.api.middleware.rate_limit import RateLimited
from deckforge.api.schemas.batch_schemas import (
    BatchJobItem,
    BatchRenderRequest,
    BatchResponse,
    BatchStatusResponse,
    BatchVariationsRequest,
)
from deckforge.db.repositories import batch_repo, deck_repo, job_repo

logger = logging.getLogger(__name__)

router = APIRouter(tags=["batch"])


@router.post("/batch/render", response_model=BatchResponse)
async def batch_render(
    body: BatchRenderRequest,
    db: DbSession,
    redis: RedisClient,
    api_key: CurrentApiKey,
    _rate_limit: RateLimited,
) -> BatchResponse:
    """Submit a batch of IR payloads for parallel rendering.

    Creates a BatchJob record, then individual Job records for each item,
    and enqueues each to the ARQ render worker pool.
    """
    # Create batch record
    batch = await batch_repo.create(
        db,
        api_key_id=api_key.uuid_id,
        total_items=len(body.items),
        webhook_url=body.webhook_url,
    )

    jobs: list[BatchJobItem] = []
    arq = ArqRedis(pool_or_conn=redis.connection_pool)

    for item in body.items:
        # Apply theme override if specified
        ir_data = item.ir.copy()
        if item.theme:
            ir_data["theme"] = item.theme

        # Create deck and job records
        deck = await deck_repo.create(
            db,
            api_key_id=api_key.uuid_id,
            ir_snapshot=ir_data,
        )
        job = await job_repo.create(
            db,
            api_key_id=api_key.uuid_id,
            job_type="render",
            queue_name="arq:render",
            deck_id=deck.id,
            batch_id=batch.id,
        )
        jobs.append(BatchJobItem(job_id=str(job.id), deck_id=str(deck.id)))

    await db.commit()

    # Enqueue all jobs to ARQ
    for job_item in jobs:
        try:
            ir_data = body.items[jobs.index(job_item)].ir
            if body.items[jobs.index(job_item)].theme:
                ir_data = ir_data.copy()
                ir_data["theme"] = body.items[jobs.index(job_item)].theme
            await arq.enqueue_job(
                "render_presentation",
                job_id=job_item.job_id,
                ir_data=ir_data,
                _queue_name="arq:render",
            )
        except Exception:
            logger.warning(
                "Failed to enqueue job %s in batch %s",
                job_item.job_id,
                batch.id,
            )

    return BatchResponse(
        batch_id=str(batch.id),
        jobs=jobs,
        total_items=len(body.items),
    )


@router.post("/batch/variations", response_model=BatchResponse)
async def batch_variations(
    body: BatchVariationsRequest,
    db: DbSession,
    redis: RedisClient,
    api_key: CurrentApiKey,
    _rate_limit: RateLimited,
) -> BatchResponse:
    """Submit one IR with multiple themes for parallel rendering.

    Expands the single IR + themes list into N individual render jobs,
    then processes identically to batch/render.
    """
    batch = await batch_repo.create(
        db,
        api_key_id=api_key.uuid_id,
        total_items=len(body.themes),
        webhook_url=body.webhook_url,
    )

    jobs: list[BatchJobItem] = []
    arq = ArqRedis(pool_or_conn=redis.connection_pool)

    for theme_name in body.themes:
        ir_data = body.ir.copy()
        ir_data["theme"] = theme_name

        deck = await deck_repo.create(
            db,
            api_key_id=api_key.uuid_id,
            ir_snapshot=ir_data,
        )
        job = await job_repo.create(
            db,
            api_key_id=api_key.uuid_id,
            job_type="render",
            queue_name="arq:render",
            deck_id=deck.id,
            batch_id=batch.id,
        )
        jobs.append(BatchJobItem(job_id=str(job.id), deck_id=str(deck.id)))

    await db.commit()

    # Enqueue all
    for idx, job_item in enumerate(jobs):
        try:
            ir_data = body.ir.copy()
            ir_data["theme"] = body.themes[idx]
            await arq.enqueue_job(
                "render_presentation",
                job_id=job_item.job_id,
                ir_data=ir_data,
                _queue_name="arq:render",
            )
        except Exception:
            logger.warning(
                "Failed to enqueue variation job %s in batch %s",
                job_item.job_id,
                batch.id,
            )

    return BatchResponse(
        batch_id=str(batch.id),
        jobs=jobs,
        total_items=len(body.themes),
    )


@router.get("/batch/{batch_id}", response_model=BatchStatusResponse)
async def batch_status(
    batch_id: str,
    db: DbSession,
    api_key: CurrentApiKey,
    _rate_limit: RateLimited,
) -> BatchStatusResponse:
    """Get the current status of a batch job."""
    try:
        bid = uuid.UUID(batch_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid batch_id format",
        )

    batch = await batch_repo.get_by_id(db, bid)
    if batch is None or batch.api_key_id != api_key.uuid_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found",
        )

    return BatchStatusResponse(
        batch_id=str(batch.id),
        status=batch.status,
        total=batch.total_items,
        completed=batch.completed_items,
        failed=batch.failed_items,
    )
