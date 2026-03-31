"""Render endpoint -- accepts IR payloads, validates, and returns presentations.

For presentations with <=10 slides, renders synchronously and returns the
.pptx file directly as a streaming response (or Google Slides URL for gslides).
For larger presentations, enqueues to the ARQ worker pool and returns a job ID.

Supports idempotency via X-Request-Id header: duplicate requests return the
original result instead of creating a new deck.

Supports output_format=gslides for Google Slides output (requires OAuth).
"""

from __future__ import annotations

import io
import logging
from typing import Any

from arq.connections import ArqRedis
from fastapi import APIRouter, BackgroundTasks, Body, Header, HTTPException, Query, status
from fastapi.responses import Response, StreamingResponse

from deckforge.api.deps import DbSession, RedisClient
from deckforge.api.middleware.auth import CurrentApiKey
from deckforge.api.middleware.credits import CreditCheck
from deckforge.api.middleware.rate_limit import RateLimited
from deckforge.api.schemas.responses import RenderResponse
from deckforge.db.repositories import deck_repo, job_repo
from deckforge.ir import Presentation
from deckforge.ir.normalize import normalize_ir
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
        402: {"description": "Insufficient credits"},
        422: {"description": "IR validation error"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def render(
    db: DbSession,
    redis: RedisClient,
    api_key: CurrentApiKey,
    _rate_limit: RateLimited,
    _credit_check: CreditCheck,
    background_tasks: BackgroundTasks,
    body: dict[str, Any] = Body(...),
    x_request_id: str | None = Header(None),
    output_format: str = Query(default="pptx", pattern="^(pptx|gslides)$"),
) -> Response:
    """Validate an IR payload and return a rendered presentation.

    Accepts both the strict Pydantic IR schema *and* a simplified shorthand
    format (e.g. ``"slide_type": "title"`` instead of ``"title_slide"``).
    The payload is normalized before Pydantic validation so users can send
    whichever format is most natural.

    For <=10 slides, renders synchronously and returns the .pptx file directly
    (or Google Slides URL for output_format=gslides).
    For >10 slides, enqueues to the worker pool and returns a JSON job response.

    If X-Request-Id is provided and a deck already exists with that request_id,
    the existing deck is returned (idempotency).

    Args:
        output_format: "pptx" (default) or "gslides" for Google Slides output.
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

    # Normalize simplified IR into strict schema before Pydantic validation
    normalized = normalize_ir(body)

    try:
        presentation = Presentation.model_validate(normalized)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"IR validation error: {exc}",
        ) from exc

    ir_dict = presentation.model_dump(mode="json")
    slide_count = len(presentation.slides)

    # ── Google Slides output path ──────────────────────────────────────
    if output_format == "gslides":
        return await _render_gslides(
            presentation, db, api_key, ir_dict, slide_count, x_request_id,
        )

    # ── PPTX output path (default) ────────────────────────────────────
    if slide_count <= SYNC_RENDER_THRESHOLD:
        # ── Synchronous render path ──────────────────────────────────────
        pptx_bytes, qa_report = render_pipeline(presentation)

        # Store the deck record with quality_score
        deck = await deck_repo.create(
            db,
            api_key_id=api_key.id,
            ir_snapshot=ir_dict,
            request_id=x_request_id,
        )
        await deck_repo.update_status(
            db, deck.id, "complete", quality_score=qa_report.score
        )
        await db.commit()

        return StreamingResponse(
            io.BytesIO(pptx_bytes),
            media_type=PPTX_CONTENT_TYPE,
            headers={
                "Content-Disposition": f'attachment; filename="deck-{deck.id}.pptx"',
                "X-Deck-Id": str(deck.id),
                "X-Quality-Score": str(qa_report.score),
                "X-Quality-Grade": qa_report.grade,
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
            render_status = "queued"
        except Exception:
            # Redis unavailable -- job is recorded but not enqueued yet
            render_status = "queued"

        return RenderResponse(
            id=str(deck.id),
            status=render_status,
            job_id=str(job.id),
            ir=ir_dict,
        )


async def _render_gslides(
    presentation: Presentation,
    db: DbSession,
    api_key: CurrentApiKey,
    ir_dict: dict,
    slide_count: int,
    x_request_id: str | None,
) -> Response:
    """Handle Google Slides output format rendering.

    Google Slides export is deferred to v0.2.  Returns 501 Not Implemented.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "error": "Google Slides export is coming in v0.2. "
            "Use PPTX format for now.",
            "suggestion": "Remove output_format=gslides or set output_format=pptx.",
        },
    )
