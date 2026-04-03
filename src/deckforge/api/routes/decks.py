"""Deck CRUD and mutation endpoints.

Provides list, get, delete, get IR, and composable mutation operations
(append, replace, reorder, retheme, export) on stored decks.
"""

from __future__ import annotations

import io
import logging
import uuid

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from deckforge.api.deps import DbSession
from deckforge.api.middleware.auth import CurrentApiKey
from deckforge.api.schemas.deck_schemas import (
    AppendSlidesRequest,
    DeckDetailResponse,
    DeckListResponse,
    DeckSummary,
    ExportRequest,
    ReorderSlidesRequest,
    ReplaceSlidesRequest,
    RethemeRequest,
)
from deckforge.db.repositories import deck_repo
from deckforge.services.deck_ops import DeckOperations

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/decks", tags=["decks"])

deck_ops = DeckOperations()

PPTX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument"
    ".presentationml.presentation"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _deck_summary(deck) -> DeckSummary:
    """Convert a Deck model to a DeckSummary response."""
    ir = deck.ir_snapshot or {}
    slide_count = len(ir.get("slides", []))
    theme = ir.get("theme", "unknown")
    return DeckSummary(
        id=str(deck.id),
        status=deck.status,
        theme=theme,
        slide_count=slide_count,
        quality_score=deck.quality_score,
        created_at=deck.created_at.isoformat() if deck.created_at else "",
        download_url=deck.file_url,
    )


def _deck_detail(deck) -> DeckDetailResponse:
    """Convert a Deck model to a DeckDetailResponse."""
    return DeckDetailResponse(
        id=str(deck.id),
        status=deck.status,
        ir=deck.ir_snapshot or {},
        download_url=deck.file_url,
        quality_score=deck.quality_score,
        created_at=deck.created_at.isoformat() if deck.created_at else "",
    )


async def _get_owned_deck(db: DbSession, api_key: CurrentApiKey, deck_id: str):
    """Load a deck and verify ownership. Raises HTTPException if not found or not owned."""
    try:
        uid = uuid.UUID(deck_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid deck ID format.",
        )
    deck = await deck_repo.get_by_id(db, uid)
    if deck is None or deck.status == "deleted":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found.",
        )
    if deck.api_key_id != api_key.uuid_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this deck.",
        )
    return deck


# ---------------------------------------------------------------------------
# CRUD endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=DeckListResponse)
async def list_decks(
    db: DbSession,
    api_key: CurrentApiKey,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> DeckListResponse:
    """List decks for the authenticated API key, paginated."""
    decks = await deck_repo.list_by_api_key(db, api_key.uuid_id, offset=offset, limit=limit)
    total = await deck_repo.count_by_api_key(db, api_key.uuid_id)
    return DeckListResponse(
        items=[_deck_summary(d) for d in decks],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{deck_id}", response_model=DeckDetailResponse)
async def get_deck(
    deck_id: str,
    db: DbSession,
    api_key: CurrentApiKey,
) -> DeckDetailResponse:
    """Get a single deck with download URL."""
    deck = await _get_owned_deck(db, api_key, deck_id)
    return _deck_detail(deck)


@router.get("/{deck_id}/ir")
async def get_deck_ir(
    deck_id: str,
    db: DbSession,
    api_key: CurrentApiKey,
) -> dict:
    """Get the IR snapshot that produced a deck (DECK-02: reproducibility)."""
    deck = await _get_owned_deck(db, api_key, deck_id)
    return deck.ir_snapshot or {}


@router.delete("/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deck(
    deck_id: str,
    db: DbSession,
    api_key: CurrentApiKey,
) -> None:
    """Soft-delete a deck."""
    deck = await _get_owned_deck(db, api_key, deck_id)
    await deck_repo.soft_delete(db, deck.id)
    await db.commit()


# ---------------------------------------------------------------------------
# Mutation endpoints
# ---------------------------------------------------------------------------


@router.post("/{deck_id}/append", response_model=DeckDetailResponse)
async def append_slides(
    deck_id: str,
    body: AppendSlidesRequest,
    db: DbSession,
    api_key: CurrentApiKey,
) -> DeckDetailResponse:
    """Append slides to an existing deck and re-render."""
    deck = await _get_owned_deck(db, api_key, deck_id)
    try:
        new_ir = deck_ops.append_slides(deck.ir_snapshot, body.slides)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    pptx_bytes = deck_ops.re_render(new_ir)
    # For simplicity, store updated IR and mark status. Real S3 upload would go here.
    await deck_repo.update_ir_snapshot(db, deck.id, new_ir)
    await deck_repo.update_status(db, deck.id, "complete")
    await db.commit()

    # Reload
    deck = await deck_repo.get_by_id(db, deck.id)
    return _deck_detail(deck)


@router.put("/{deck_id}/slides/{index}", response_model=DeckDetailResponse)
async def replace_slide(
    deck_id: str,
    index: int,
    body: ReplaceSlidesRequest,
    db: DbSession,
    api_key: CurrentApiKey,
) -> DeckDetailResponse:
    """Replace a specific slide in a deck and re-render."""
    deck = await _get_owned_deck(db, api_key, deck_id)
    try:
        new_ir = deck_ops.replace_slide(deck.ir_snapshot, index, body.slide)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    pptx_bytes = deck_ops.re_render(new_ir)
    await deck_repo.update_ir_snapshot(db, deck.id, new_ir)
    await deck_repo.update_status(db, deck.id, "complete")
    await db.commit()

    deck = await deck_repo.get_by_id(db, deck.id)
    return _deck_detail(deck)


@router.post("/{deck_id}/reorder", response_model=DeckDetailResponse)
async def reorder_slides(
    deck_id: str,
    body: ReorderSlidesRequest,
    db: DbSession,
    api_key: CurrentApiKey,
) -> DeckDetailResponse:
    """Reorder slides in a deck and re-render."""
    deck = await _get_owned_deck(db, api_key, deck_id)
    try:
        new_ir = deck_ops.reorder_slides(deck.ir_snapshot, body.order)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    pptx_bytes = deck_ops.re_render(new_ir)
    await deck_repo.update_ir_snapshot(db, deck.id, new_ir)
    await deck_repo.update_status(db, deck.id, "complete")
    await db.commit()

    deck = await deck_repo.get_by_id(db, deck.id)
    return _deck_detail(deck)


@router.post("/{deck_id}/retheme", response_model=DeckDetailResponse)
async def retheme_deck(
    deck_id: str,
    body: RethemeRequest,
    db: DbSession,
    api_key: CurrentApiKey,
) -> DeckDetailResponse:
    """Change the theme of a deck and re-render."""
    deck = await _get_owned_deck(db, api_key, deck_id)
    try:
        new_ir = deck_ops.retheme(deck.ir_snapshot, body.theme)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    pptx_bytes = deck_ops.re_render(new_ir)
    await deck_repo.update_ir_snapshot(db, deck.id, new_ir)
    await deck_repo.update_status(db, deck.id, "complete")
    await db.commit()

    deck = await deck_repo.get_by_id(db, deck.id)
    return _deck_detail(deck)


@router.post("/{deck_id}/export")
async def export_deck(
    deck_id: str,
    body: ExportRequest,
    db: DbSession,
    api_key: CurrentApiKey,
):
    """Re-export a deck to a different format (DECK-03)."""
    deck = await _get_owned_deck(db, api_key, deck_id)

    if body.format == "gslides":
        # Google Slides export requires OAuth -- delegate to render_pipeline
        from deckforge.config import settings
        from deckforge.ir import Presentation
        from deckforge.workers.tasks import render_pipeline

        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google Slides export not configured.",
            )
        refresh_token = api_key.google_refresh_token
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google account not connected.",
            )
        from deckforge.rendering.gslides.oauth import GoogleOAuthHandler

        handler = GoogleOAuthHandler(
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
        )
        credentials = handler.build_credentials(
            access_token="",
            refresh_token=refresh_token,
        )
        presentation = Presentation.model_validate(deck.ir_snapshot)
        result = render_pipeline(presentation, output_format="gslides", credentials=credentials)
        return {
            "format": "gslides",
            "presentation_id": result.presentation_id,
            "presentation_url": result.presentation_url,
        }
    else:
        # PPTX export
        pptx_bytes = deck_ops.re_render(deck.ir_snapshot)
        return StreamingResponse(
            io.BytesIO(pptx_bytes),
            media_type=PPTX_CONTENT_TYPE,
            headers={
                "Content-Disposition": f'attachment; filename="deck-{deck.id}.pptx"',
                "X-Deck-Id": str(deck.id),
            },
        )
