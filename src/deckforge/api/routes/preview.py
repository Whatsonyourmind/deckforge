"""Preview endpoint -- renders first N slides as PNG thumbnails.

Runs the full render pipeline (layout + PPTX) on a subset of slides,
then converts to PNG thumbnails via LibreOffice or placeholder fallback.
"""

from __future__ import annotations

import base64
import logging

from fastapi import APIRouter, Query

from deckforge.api.middleware.auth import CurrentApiKey
from deckforge.api.middleware.rate_limit import RateLimited
from deckforge.api.schemas.responses import PreviewResponse, ThumbnailItem
from deckforge.ir import Presentation
from deckforge.rendering.thumbnail import pptx_to_thumbnails
from deckforge.workers.tasks import render_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(tags=["render"])


@router.post(
    "/render/preview",
    response_model=PreviewResponse,
    responses={
        401: {"description": "Invalid or missing API key"},
        422: {"description": "IR validation error"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def render_preview(
    body: Presentation,
    api_key: CurrentApiKey,
    _rate_limit: RateLimited,
    max_slides: int = Query(default=5, ge=1, le=20, description="Max slides to preview"),
) -> PreviewResponse:
    """Render the first N slides as PNG thumbnails.

    Runs the full render pipeline on a trimmed copy of the presentation
    (only the first ``max_slides`` slides), then converts the resulting
    PPTX to PNG images. Returns base64-encoded PNG data for each slide.
    """
    # Trim to first max_slides slides for preview
    preview_slides = body.slides[:max_slides]
    preview_ir = body.model_copy(update={"slides": preview_slides})

    # Run full render pipeline to get PPTX bytes
    pptx_bytes, _qa_report = render_pipeline(preview_ir)

    # Convert to PNG thumbnails
    thumbnails_bytes = pptx_to_thumbnails(pptx_bytes, max_slides=max_slides)

    # Encode as base64
    thumbnails = [
        ThumbnailItem(
            slide_index=i,
            image_base64=base64.b64encode(png_bytes).decode("ascii"),
        )
        for i, png_bytes in enumerate(thumbnails_bytes)
    ]

    return PreviewResponse(
        slide_count=len(thumbnails),
        thumbnails=thumbnails,
    )
