"""Error response schemas for the DeckForge API."""

from __future__ import annotations

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error envelope returned by all error responses."""

    error: str
    detail: str | None = None
    request_id: str | None = None


class ValidationErrorResponse(BaseModel):
    """422 validation error with structured Pydantic details."""

    error: str = "validation_error"
    detail: list[dict]
