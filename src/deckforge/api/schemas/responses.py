"""Success response schemas for the DeckForge API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """GET /v1/health response."""

    status: Literal["healthy", "degraded"]
    checks: dict[str, str]
    version: str


class RenderResponse(BaseModel):
    """POST /v1/render response."""

    id: str
    status: str
    ir: dict | None = None
    download_url: str | None = None
    quality_score: int | None = None


class JobResponse(BaseModel):
    """GET /v1/jobs/{job_id} response."""

    id: str
    status: str
    progress: float
    job_type: str
    created_at: str
    result: dict | None = None
