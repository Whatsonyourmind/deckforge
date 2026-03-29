"""DeckForge application entry point.

Creates the FastAPI app with lifespan managing Redis and database connections.
Run with: uvicorn deckforge.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from redis.asyncio import Redis

from deckforge.api.app import create_app
from deckforge.config import settings


@asynccontextmanager
async def lifespan(app):
    """Manage application startup and shutdown resources."""
    # Startup: create and verify Redis connection
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    await redis.ping()
    app.state.redis = redis

    yield

    # Shutdown: close Redis connection
    await redis.aclose()


app = create_app(lifespan=lifespan)
