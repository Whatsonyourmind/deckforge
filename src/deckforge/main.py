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
    import asyncio
    import logging

    logger = logging.getLogger("deckforge")

    # Startup: create Redis connection with retry for cold-start environments
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    for attempt in range(5):
        try:
            await redis.ping()
            logger.info("Redis connected")
            break
        except Exception as exc:
            if attempt < 4:
                logger.warning("Redis not ready (attempt %d/5): %s", attempt + 1, exc)
                await asyncio.sleep(2)
            else:
                logger.warning("Redis unavailable after 5 attempts, starting in degraded mode")
    app.state.redis = redis

    yield

    # Shutdown: close Redis connection
    await redis.aclose()


app = create_app(lifespan=lifespan)
