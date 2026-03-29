"""API key authentication middleware.

Validates dk_live_ / dk_test_ prefixed API keys by hashing with SHA-256
and looking up the hash in the database.
"""

from __future__ import annotations

import hashlib
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from deckforge.api.deps import DbSession
from deckforge.db.models.api_key import ApiKey
from deckforge.db.repositories import api_key_repo

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

VALID_PREFIXES = ("dk_live_", "dk_test_")


async def get_api_key(
    db: DbSession,
    api_key: str | None = Security(API_KEY_HEADER),
) -> ApiKey:
    """Validate and resolve an API key from the X-API-Key header.

    Steps:
    1. Reject if header is missing.
    2. Reject if key doesn't start with dk_live_ or dk_test_.
    3. SHA-256 hash the key and look up in the database.
    4. Reject if not found or inactive.
    5. Update last_used_at and return the ApiKey model.
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

    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    db_key = await api_key_repo.get_by_hash(db, key_hash)

    if db_key is None or not db_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or deactivated API key.",
        )

    # Fire-and-forget last_used_at update (non-blocking for the request)
    await api_key_repo.update_last_used(db, db_key.id)

    return db_key


CurrentApiKey = Annotated[ApiKey, Depends(get_api_key)]
