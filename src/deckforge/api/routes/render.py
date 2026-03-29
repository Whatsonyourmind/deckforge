"""Render endpoint -- accepts IR payloads, validates, and stores in the database.

Supports idempotency via X-Request-Id header: duplicate requests return the
original result instead of creating a new deck.
"""

from __future__ import annotations

from fastapi import APIRouter, Header
from pydantic import ValidationError

from deckforge.api.deps import DbSession
from deckforge.api.middleware.auth import CurrentApiKey
from deckforge.api.middleware.rate_limit import RateLimited
from deckforge.api.schemas.responses import RenderResponse
from deckforge.db.repositories import deck_repo
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
    api_key: CurrentApiKey,
    _rate_limit: RateLimited,
    x_request_id: str | None = Header(None),
) -> RenderResponse:
    """Validate an IR payload and store it as a deck.

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
    await db.commit()

    return RenderResponse(
        id=str(deck.id),
        status="validated",
        ir=ir_dict,
    )
