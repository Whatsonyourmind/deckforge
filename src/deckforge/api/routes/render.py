"""Render endpoint -- accepts IR payloads, validates, and returns PPTX files.

For presentations with <=10 slides, renders synchronously and returns the
.pptx file directly as a streaming response. For larger presentations,
enqueues to the ARQ worker pool and returns a job ID for polling.

Supports idempotency via X-Request-Id header: duplicate requests return the
original result instead of creating a new deck.
"""

from __future__ import annotations

import io
import logging

from arq.connections import ArqRedis
from fastapi import APIRouter, BackgroundTasks, Header
from fastapi.responses import Response, StreamingResponse

from deckforge.api.deps import DbSession, RedisClient
from deckforge.api.middleware.auth import CurrentApiKey
from deckforge.api.middleware.rate_limit import RateLimited
from deckforge.api.schemas.responses import RenderResponse
from deckforge.db.repositories import deck_repo, job_repo
from deckforge.ir import Presentation
from deckforge.workers.tasks import render_pipeline

logger = logging.getLogger(__name__)

# Maximum slide count for synchronous rendering
SYNC_RENDER_THRESHOLD = 10

PPTX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument"
    ".presentationml.presentation"
)

router = APIRouter(tags=["render"])


@router.post(
    "/render",
    responses={
        200: {
            "description": "Synchronous PPTX file (<=10 slides) or async job response",
            "content": {
                PPTX_CONTENT_TYPE: {},
                "application/json": {"model": RenderResponse},
            },
        },
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
    background_tasks: BackgroundTasks,
    x_request_id: str | None = Header(None),
) -> Response:
    """Validate an IR payload and return a rendered presentation.

    For <=10 slides, renders synchronously and returns the .pptx file directly.
    For >10 slides, enqueues to the worker pool and returns a JSON job response.

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

    ir_dict = body.model_dump(mode="json")
    slide_count = len(body.slides)

    if slide_count <= SYNC_RENDER_THRESHOLD:
        # ── Synchronous render path ──────────────────────────────────────
        pptx_bytes = render_pipeline(body)

        # Store the deck record
        deck = await deck_repo.create(
            db,
            api_key_id=api_key.id,
            ir_snapshot=ir_dict,
            request_id=x_request_id,
        )
        await deck_repo.update_status(db, deck.id, "complete")
        await db.commit()

        return StreamingResponse(
            io.BytesIO(pptx_bytes),
            media_type=PPTX_CONTENT_TYPE,
            headers={
                "Content-Disposition": f'attachment; filename="deck-{deck.id}.pptx"',
                "X-Deck-Id": str(deck.id),
            },
        )
    else:
        # ── Asynchronous render path (>10 slides) ────────────────────────
        deck = await deck_repo.create(
            db,
            api_key_id=api_key.id,
            ir_snapshot=ir_dict,
            request_id=x_request_id,
        )

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
            # Redis unavailable -- job is recorded but not enqueued yet
            status = "queued"

        return RenderResponse(
            id=str(deck.id),
            status=status,
            job_id=str(job.id),
            ir=ir_dict,
        )
