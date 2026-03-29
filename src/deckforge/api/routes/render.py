"""Render endpoint -- accepts IR payloads, validates, enqueues to worker.

Supports idempotency via X-Request-Id header: duplicate requests return the
original result instead of creating a new deck.
"""

from __future__ import annotations

from arq.connections import ArqRedis
from fastapi import APIRouter, Header

from deckforge.api.deps import DbSession, RedisClient
from deckforge.api.middleware.auth import CurrentApiKey
from deckforge.api.middleware.rate_limit import RateLimited
from deckforge.api.schemas.responses import RenderResponse
from deckforge.db.repositories import deck_repo, job_repo
from deckforge.ir import Presentation

router = APIRouter(tags=["render"])


@router.post(
    "/render",
    response_model=RenderResponse,
    responses={
        401: {"description": "Invalid or missing API key"},
        422: {"description": "IR validation error"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def render(
    body: Presentation,
    db: DbSession,
    redis: RedisClient,
    api_key: CurrentApiKey,
    _rate_limit: RateLimited,
    x_request_id: str | None = Header(None),
) -> RenderResponse:
    """Validate an IR payload, store as a deck, create a job, and enqueue rendering.

    If X-Request-Id is provided and a deck already exists with that request_id,
    the existing deck is returned (idempotency).
    """
    # Idempotency check
    if x_request_id:
        existing = await deck_repo.get_by_request_id(db, x_request_id)
        if existing is not None:
            return RenderResponse(
                id=str(existing.id),
                status=existing.status,
                ir=existing.ir_snapshot,
                download_url=existing.file_url,
                quality_score=existing.quality_score,
            )

    # Store the validated IR
    ir_dict = body.model_dump(mode="json")
    deck = await deck_repo.create(
        db,
        api_key_id=api_key.id,
        ir_snapshot=ir_dict,
        request_id=x_request_id,
    )

    # Create a job record and enqueue rendering
    job = await job_repo.create(
        db,
        api_key_id=api_key.id,
        job_type="render",
        queue_name="arq:render",
        deck_id=deck.id,
    )
    await db.commit()

    # Enqueue to ARQ render worker pool
    try:
        arq = ArqRedis(pool_or_conn=redis.connection_pool)
        await arq.enqueue_job(
            "render_presentation",
            job_id=str(job.id),
            ir_data=ir_dict,
            _queue_name="arq:render",
        )
        status = "queued"
    except Exception:
        # Redis unavailable — job is recorded but not enqueued yet
        status = "queued"

    return RenderResponse(
        id=str(deck.id),
        status=status,
        job_id=str(job.id),
        ir=ir_dict,
    )
