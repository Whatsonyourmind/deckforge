"""Request and response schemas for webhook registration."""

from __future__ import annotations

from pydantic import BaseModel, Field


class WebhookCreateRequest(BaseModel):
    """POST /v1/webhooks request body."""

    url: str = Field(..., description="Webhook endpoint URL")
    events: list[str] = Field(
        ...,
        min_length=1,
        description="Event types to subscribe to (e.g. render.complete, batch.complete)",
    )


class WebhookResponse(BaseModel):
    """A single webhook registration."""

    id: str
    url: str
    events: list[str]
    secret: str
    is_active: bool
    created_at: str


class WebhookListResponse(BaseModel):
    """GET /v1/webhooks response."""

    webhooks: list[WebhookResponse]
