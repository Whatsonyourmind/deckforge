"""Developer onboarding routes.

POST /v1/onboard/signup  - Create user + provision API key
GET  /v1/onboard/status/{user_id} - Track onboarding progress
"""

from __future__ import annotations

import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from deckforge.api.deps import DbSession
from deckforge.api.schemas.onboarding_schemas import (
    OnboardingStatusResponse,
    SignupRequest,
    SignupResponse,
)
from deckforge.billing.tiers import get_tier
from deckforge.config import settings
from deckforge.db.models.api_key import ApiKey
from deckforge.db.models.deck import Deck
from deckforge.db.models.job import Job
from deckforge.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["onboarding"])


def _generate_raw_key() -> str:
    """Generate a random API key with dk_live_ prefix."""
    token = secrets.token_hex(24)
    return f"dk_live_{token}"


async def _create_unkey_key(
    tier: str,
    user_id: str,
) -> str:
    """Create an API key via the Unkey API.

    Returns the raw key string (shown once to the user).
    """
    tier_config = get_tier(tier)

    payload = {
        "apiId": settings.UNKEY_API_ID,
        "prefix": "dk_live",
        "meta": {
            "tier": tier,
            "user_id": user_id,
            "scopes": ["read", "generate"],
        },
        "ratelimit": {
            "type": "fast",
            "limit": tier_config.rate_limit,
            "refillRate": tier_config.rate_limit,
            "refillInterval": 60000,  # 1 minute in ms
        },
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.unkey.dev/v1/keys.createKey",
            json=payload,
            headers={
                "Authorization": f"Bearer {settings.UNKEY_ROOT_KEY}",
                "Content-Type": "application/json",
            },
            timeout=10.0,
        )

    if resp.status_code != 200:
        logger.error("Unkey createKey failed: %d %s", resp.status_code, resp.text)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to provision API key via Unkey.",
        )

    data = resp.json()
    return data["key"]


async def _create_db_key(
    db: DbSession,
    user_id: uuid.UUID,
    tier: str,
) -> str:
    """Create an API key in the local database (dev mode fallback).

    Returns the raw key string.
    """
    raw_key = _generate_raw_key()
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    api_key = ApiKey(
        user_id=user_id,
        key_hash=key_hash,
        key_prefix=raw_key[:15],
        name="Onboarding Key",
        scopes=["read", "generate"],
        tier=tier,
        is_test=False,
    )
    db.add(api_key)
    await db.flush()
    return raw_key


@router.post(
    "/onboard/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Sign up and get an API key",
)
async def signup(body: SignupRequest, db: DbSession) -> SignupResponse:
    """Create a new user and provision an API key.

    The API key is returned in the response and shown only once.
    Store it securely -- it cannot be retrieved again.
    """
    # Check for duplicate email
    existing = await db.execute(
        select(User).where(User.email == body.email)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # Create user
    user = User(email=body.email, name=body.name)
    db.add(user)
    await db.flush()

    # Provision API key
    tier_config = get_tier(body.tier)

    if settings.UNKEY_ROOT_KEY is not None:
        raw_key = await _create_unkey_key(
            tier=body.tier,
            user_id=str(user.id),
        )
    else:
        raw_key = await _create_db_key(db, user.id, body.tier)

    await db.commit()

    return SignupResponse(
        user_id=str(user.id),
        api_key=raw_key,
        tier=body.tier,
        credits=tier_config.credit_limit,
        next_steps=[
            "Install SDK: npm install @deckforge/sdk",
            f"Set API key: export DECKFORGE_API_KEY={raw_key[:20]}...",
            (
                "Generate first deck: "
                'curl -X POST https://api.deckforge.dev/v1/generate '
                '-H "X-API-Key: <your-key>" '
                '-H "Content-Type: application/json" '
                "-d '{\"prompt\": \"My first deck\", \"slide_count\": 5}'"
            ),
        ],
    )


@router.get(
    "/onboard/status/{user_id}",
    response_model=OnboardingStatusResponse,
    summary="Check onboarding progress",
)
async def onboarding_status(
    user_id: uuid.UUID,
    db: DbSession,
) -> OnboardingStatusResponse:
    """Check a user's onboarding progress.

    Returns completed steps and the suggested next step.
    """
    # Verify user exists
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    steps_completed: list[str] = ["account_created"]

    # Check if user has an API key
    key_result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == user_id).limit(1)
    )
    has_key = key_result.scalar_one_or_none() is not None
    if has_key:
        steps_completed.append("api_key_created")

    # Check if user has any render jobs
    render_result = await db.execute(
        select(Job).where(Job.api_key_id == user_id).limit(1)
    )
    has_render = render_result.scalar_one_or_none() is not None
    if has_render:
        steps_completed.append("first_render")

    # Check if user has any generated decks
    deck_result = await db.execute(
        select(Deck).where(Deck.api_key_id == user_id).limit(1)
    )
    has_deck = deck_result.scalar_one_or_none() is not None
    if has_deck:
        steps_completed.append("first_generate")

    # Determine next step
    if not has_key:
        next_step = "Create an API key at /v1/onboard/signup"
    elif not has_render:
        next_step = "Render your first deck with POST /v1/render"
    elif not has_deck:
        next_step = "Generate a deck from a prompt with POST /v1/generate"
    else:
        next_step = "Onboarding complete! Explore themes at /v1/discovery/themes"

    # Calculate time elapsed
    now = datetime.now(timezone.utc)
    created = user.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    elapsed = int((now - created).total_seconds())

    return OnboardingStatusResponse(
        steps_completed=steps_completed,
        next_step=next_step,
        time_elapsed_seconds=max(elapsed, 0),
    )
