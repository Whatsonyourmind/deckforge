"""API key authentication middleware.

Dual-mode auth: Unkey-managed verification in production, SHA-256 DB fallback
for local development (when UNKEY_ROOT_KEY is not configured).

Maintains backwards compatibility with X-API-Key header and dk_live_/dk_test_ prefixes.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from deckforge.api.deps import DbSession
from deckforge.config import settings
from deckforge.db.models.api_key import ApiKey
from deckforge.db.repositories import api_key_repo

logger = logging.getLogger(__name__)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

VALID_PREFIXES = ("dk_live_", "dk_test_")


@dataclass(frozen=True)
class AuthContext:
    """Unified authentication context consumed by downstream middleware.

    Produced by either Unkey verification or legacy DB auth.
    """

    key_id: str
    tier: str = "starter"
    user_id: str | None = None
    stripe_customer_id: str | None = None
    rate_limited: bool = False
    remaining: int | None = None
    scopes: list[str] = field(default_factory=lambda: ["read", "generate"])
    payment_settled: bool = False  # True when authenticated via x402 payment
    source: str = "unkey"  # "unkey" | "db" | "x402"

    @property
    def id(self) -> str:
        """Backwards-compatible alias for key_id.

        Existing routes reference api_key.id from the old ApiKey model.
        """
        return self.key_id

    @property
    def uuid_id(self) -> uuid.UUID:
        """Return key_id as a UUID for repository queries.

        Falls back to a deterministic UUID if key_id is not a valid UUID
        (e.g., Unkey IDs or x402 payment IDs).
        """
        try:
            return uuid.UUID(self.key_id)
        except (ValueError, AttributeError):
            return uuid.uuid5(uuid.NAMESPACE_URL, self.key_id)


async def _verify_via_unkey(api_key: str) -> AuthContext:
    """Verify an API key via the Unkey API.

    Unkey handles rate limiting automatically during verification.
    The response includes rate_limited flag and remaining count.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.unkey.dev/v1/keys.verifyKey",
            json={"apiId": settings.UNKEY_API_ID, "key": api_key},
            headers={"Content-Type": "application/json"},
            timeout=10.0,
        )

    if resp.status_code != 200:
        logger.error("Unkey API returned %d: %s", resp.status_code, resp.text)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upstream key verification service unavailable.",
        )

    data = resp.json()

    if not data.get("valid", False):
        code = data.get("code", "UNKNOWN")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid API key ({code}).",
        )

    meta = data.get("meta") or {}
    rate_limit = data.get("ratelimit") or {}

    return AuthContext(
        key_id=data.get("keyId", "unknown"),
        tier=meta.get("tier", "starter"),
        user_id=meta.get("user_id"),
        stripe_customer_id=meta.get("stripe_customer_id"),
        rate_limited=rate_limit.get("remaining", 1) <= 0,
        remaining=rate_limit.get("remaining"),
        scopes=meta.get("scopes", ["read", "generate"]),
        source="unkey",
    )


async def _verify_via_db(db: AsyncSession, api_key: str) -> AuthContext:
    """Legacy DB-based verification using SHA-256 hash lookup.

    Used when UNKEY_ROOT_KEY is not configured (local development).
    """
    from sqlalchemy import select

    from deckforge.db.models.user import User

    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    db_key = await api_key_repo.get_by_hash(db, key_hash)

    if db_key is None or not db_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or deactivated API key.",
        )

    # Fire-and-forget last_used_at update
    await api_key_repo.update_last_used(db, db_key.id)

    # Look up the user's stripe_customer_id for billing integration
    stripe_customer_id = None
    if db_key.user_id:
        stmt = select(User.stripe_customer_id).where(User.id == db_key.user_id)
        result = await db.execute(stmt)
        stripe_customer_id = result.scalar_one_or_none()

    return AuthContext(
        key_id=str(db_key.id),
        tier=db_key.tier,
        user_id=str(db_key.user_id),
        stripe_customer_id=stripe_customer_id,
        rate_limited=False,  # DB mode has no built-in rate limit flag
        remaining=None,
        scopes=db_key.scopes or ["read", "generate"],
        source="db",
    )


async def get_api_key(
    db: DbSession,
    api_key: str | None = Security(API_KEY_HEADER),
) -> AuthContext:
    """Validate and resolve an API key from the X-API-Key header.

    Production: Verifies via Unkey API (when UNKEY_ROOT_KEY is set).
    Development: Falls back to SHA-256 DB lookup.

    Steps:
    1. Reject if header is missing.
    2. Reject if key doesn't start with dk_live_ or dk_test_.
    3. Verify via Unkey or DB lookup.
    4. Return AuthContext for downstream middleware.
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide X-API-Key header.",
        )

    if not api_key.startswith(VALID_PREFIXES):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format. Keys must start with dk_live_ or dk_test_.",
        )

    # Unkey path (production)
    if settings.UNKEY_ROOT_KEY is not None:
        return await _verify_via_unkey(api_key)

    # DB fallback (development)
    return await _verify_via_db(db, api_key)


CurrentApiKey = Annotated[AuthContext, Depends(get_api_key)]
