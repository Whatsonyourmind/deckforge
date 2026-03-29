"""FastAPI dependency injection helpers.

Provides typed dependencies for database sessions and Redis clients,
used throughout the API routes and middleware.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from deckforge.db.engine import get_db


async def get_redis(request: Request) -> Redis:
    """Retrieve the Redis client stored on app.state during lifespan."""
    return request.app.state.redis


DbSession = Annotated[AsyncSession, Depends(get_db)]
RedisClient = Annotated[Redis, Depends(get_redis)]
