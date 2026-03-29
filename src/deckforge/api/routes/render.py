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

from arq.connections import ArqRedis
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Query, status
from fastapi.responses import Response, StreamingResponse

from deckforge.api.deps import DbSession, RedisClient
from deckforge.api.middleware.auth import CurrentApiKey
from deckforge.api.middleware.rate_limit import RateLimited
from deckforge.api.schemas.responses import GoogleSlidesRenderResponse, RenderResponse
from deckforge.config import settings
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
    output_format: str = Query(default="pptx", pattern="^(pptx|gslides)$"),
) -> Response:
    """Validate an IR payload and return a rendered presentation.

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

    ir_dict = body.model_dump(mode="json")
    slide_count = len(body.slides)

    # ── Google Slides output path ──────────────────────────────────────
    if output_format == "gslides":
        return await _render_gslides(body, db, api_key, ir_dict, slide_count, x_request_id)

    # ── PPTX output path (default) ────────────────────────────────────
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
    body: Presentation,
    db: DbSession,
    api_key: CurrentApiKey,
    ir_dict: dict,
    slide_count: int,
    x_request_id: str | None,
) -> Response:
    """Handle Google Slides output format rendering.

    Validates OAuth configuration, builds credentials from stored refresh token,
    and renders via GoogleSlidesRenderer.
    """
    # Check Google OAuth is configured
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Slides output is not configured. "
            "Set DECKFORGE_GOOGLE_CLIENT_ID and DECKFORGE_GOOGLE_CLIENT_SECRET.",
        )

    # Check user has connected Google account
    refresh_token = api_key.google_refresh_token
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account not connected. "
            "Call GET /v1/auth/google/authorize first.",
        )

    # Build credentials
    from deckforge.rendering.gslides.oauth import GoogleOAuthHandler

    handler = GoogleOAuthHandler(
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )
    credentials = handler.build_credentials(
        access_token="",  # Will be refreshed automatically
        refresh_token=refresh_token,
    )

    # Render
    result = render_pipeline(body, output_format="gslides", credentials=credentials)

    # Store the deck record
    deck = await deck_repo.create(
        db,
        api_key_id=api_key.id,
        ir_snapshot=ir_dict,
        request_id=x_request_id,
    )
    await deck_repo.update_status(db, deck.id, "complete", file_url=result.presentation_url)
    await db.commit()

    return GoogleSlidesRenderResponse(
        id=str(deck.id),
        status="complete",
        presentation_id=result.presentation_id,
        presentation_url=result.presentation_url,
        title=result.title,
        slide_count=result.slide_count,
    )
