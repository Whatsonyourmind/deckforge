"""Request and response schemas for deck CRUD, mutation, and cost estimation endpoints."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Deck list / detail responses
# ---------------------------------------------------------------------------


class DeckSummary(BaseModel):
    """Compact deck representation for list endpoints."""

    id: str
    status: str
    theme: str
    slide_count: int
    quality_score: int | None = None
    created_at: str
    download_url: str | None = None


class DeckListResponse(BaseModel):
    """GET /v1/decks paginated list response."""

    items: list[DeckSummary]
    total: int
    offset: int
    limit: int


class DeckDetailResponse(BaseModel):
    """GET /v1/decks/{deck_id} detail response."""

    id: str
    status: str
    ir: dict
    download_url: str | None = None
    quality_score: int | None = None
    created_at: str


# ---------------------------------------------------------------------------
# Mutation requests
# ---------------------------------------------------------------------------


class AppendSlidesRequest(BaseModel):
    """POST /v1/decks/{deck_id}/append request body."""

    slides: list[dict] = Field(min_length=1)


class ReplaceSlidesRequest(BaseModel):
    """PUT /v1/decks/{deck_id}/slides/{index} request body."""

    slide: dict


class ReorderSlidesRequest(BaseModel):
    """POST /v1/decks/{deck_id}/reorder request body."""

    order: list[int] = Field(min_length=1)


class RethemeRequest(BaseModel):
    """POST /v1/decks/{deck_id}/retheme request body."""

    theme: str = Field(min_length=1)


class ExportRequest(BaseModel):
    """POST /v1/decks/{deck_id}/export request body."""

    format: Literal["pptx", "gslides"] = "pptx"


# ---------------------------------------------------------------------------
# Cost estimation
# ---------------------------------------------------------------------------


class CostEstimateRequest(BaseModel):
    """POST /v1/estimate request body.

    Provide either ``ir`` (for exact estimation) or ``prompt`` (for rough
    estimation based on default slide count with NL surcharge).
    """

    ir: dict | None = None
    prompt: str | None = None


class CostEstimateResponse(BaseModel):
    """POST /v1/estimate response."""

    base_credits: int
    surcharges: dict[str, float]
    total_credits: int
    breakdown: str
