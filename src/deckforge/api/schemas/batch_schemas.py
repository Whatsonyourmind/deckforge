"""Request and response schemas for batch render operations."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BatchRenderItem(BaseModel):
    """A single item in a batch render request."""

    ir: dict = Field(..., description="Presentation IR payload")
    theme: str | None = Field(
        None, description="Theme override for this item"
    )


class BatchRenderRequest(BaseModel):
    """POST /v1/batch/render request body."""

    items: list[BatchRenderItem] = Field(
        ..., min_length=1, max_length=100, description="List of IR payloads"
    )
    webhook_url: str | None = Field(
        None, description="Webhook URL for batch completion notification"
    )


class BatchVariationsRequest(BaseModel):
    """POST /v1/batch/variations request body."""

    ir: dict = Field(..., description="Base IR payload")
    themes: list[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of theme names to apply",
    )
    webhook_url: str | None = Field(
        None, description="Webhook URL for batch completion notification"
    )


class BatchJobItem(BaseModel):
    """An individual job within a batch."""

    job_id: str
    deck_id: str


class BatchResponse(BaseModel):
    """Response for batch creation."""

    batch_id: str
    jobs: list[BatchJobItem]
    total_items: int


class BatchStatusResponse(BaseModel):
    """GET /v1/batch/{batch_id} response."""

    batch_id: str
    status: str
    total: int
    completed: int
    failed: int
