"""Webhook registration endpoints -- CRUD for async event subscriptions.

POST   /v1/webhooks             -- Register a new webhook
GET    /v1/webhooks             -- List registered webhooks
DELETE /v1/webhooks/{webhook_id} -- Delete a webhook registration
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, HTTPException, status

from deckforge.api.deps import DbSession
from deckforge.api.middleware.auth import CurrentApiKey
from deckforge.api.middleware.rate_limit import RateLimited
from deckforge.api.schemas.webhook_schemas import (
    WebhookCreateRequest,
    WebhookListResponse,
    WebhookResponse,
)
from deckforge.db.repositories import webhook_repo

logger = logging.getLogger(__name__)

router = APIRouter(tags=["webhooks"])

# Supported event types
VALID_EVENTS = {
    "render.complete",
    "render.failed",
    "generate.complete",
    "generate.failed",
    "batch.complete",
    "batch.partial_failure",
    "batch.failed",
}


@router.post("/webhooks", response_model=WebhookResponse, status_code=201)
async def create_webhook(
    body: WebhookCreateRequest,
    db: DbSession,
    api_key: CurrentApiKey,
    _rate_limit: RateLimited,
) -> WebhookResponse:
    """Register a new webhook endpoint.

    The response includes the auto-generated HMAC secret. This is the only
    time the secret is returned -- store it securely for signature verification.
    """
    # Validate event types
    invalid = set(body.events) - VALID_EVENTS
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event types: {sorted(invalid)}. "
            f"Valid: {sorted(VALID_EVENTS)}",
        )

    reg = await webhook_repo.create(
        db,
        api_key_id=api_key.uuid_id,
        url=body.url,
        events=body.events,
    )
    await db.commit()

    return WebhookResponse(
        id=str(reg.id),
        url=reg.url,
        events=reg.events,
        secret=reg.secret,
        is_active=reg.is_active,
        created_at=reg.created_at.isoformat() if reg.created_at else "",
    )


@router.get("/webhooks", response_model=WebhookListResponse)
async def list_webhooks(
    db: DbSession,
    api_key: CurrentApiKey,
    _rate_limit: RateLimited,
) -> WebhookListResponse:
    """List all active webhook registrations for the current API key."""
    hooks = await webhook_repo.get_by_api_key(db, api_key.uuid_id)

    return WebhookListResponse(
        webhooks=[
            WebhookResponse(
                id=str(h.id),
                url=h.url,
                events=h.events,
                secret="****" + h.secret[-8:],  # Mask secret in list response
                is_active=h.is_active,
                created_at=h.created_at.isoformat() if h.created_at else "",
            )
            for h in hooks
        ]
    )


@router.delete("/webhooks/{webhook_id}", status_code=204)
async def delete_webhook(
    webhook_id: str,
    db: DbSession,
    api_key: CurrentApiKey,
    _rate_limit: RateLimited,
) -> None:
    """Delete a webhook registration."""
    try:
        wid = uuid.UUID(webhook_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook_id format",
        )

    hook = await webhook_repo.get_by_id(db, wid)
    if hook is None or hook.api_key_id != api_key.uuid_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )

    await webhook_repo.delete(db, wid)
    await db.commit()
