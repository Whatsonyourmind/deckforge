"""ARQ worker pool settings for content and render workers.

Dual pool architecture:
- Content workers (arq:content): I/O-bound LLM calls, max_jobs=20
- Render workers (arq:render): CPU-bound PPTX generation, max_jobs=4
"""

from __future__ import annotations

from urllib.parse import urlparse

import boto3
from arq.connections import RedisSettings
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from deckforge.config import settings


def _parse_redis_url(url: str) -> RedisSettings:
    """Convert a redis:// URL into arq RedisSettings."""
    parsed = urlparse(url)
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        database=int(parsed.path.lstrip("/") or "0"),
        password=parsed.password,
    )


REDIS_SETTINGS = _parse_redis_url(settings.REDIS_URL)


async def worker_startup(ctx: dict) -> None:
    """Initialize shared resources for worker context.

    Called once when a worker pool starts. Stores database session factory,
    Redis client reference, and S3 client in the worker context dict.
    """
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    ctx["db_factory"] = async_sessionmaker(engine, expire_on_commit=False)
    ctx["engine"] = engine

    ctx["s3_client"] = boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        config=boto3.session.Config(signature_version="s3v4"),
    )
    ctx["s3_bucket"] = settings.S3_BUCKET


async def worker_shutdown(ctx: dict) -> None:
    """Clean up worker resources on shutdown."""
    engine = ctx.get("engine")
    if engine:
        await engine.dispose()


class ContentWorkerSettings:
    """ARQ settings for content generation workers (I/O-bound)."""

    from deckforge.workers.tasks import generate_content

    functions = [generate_content]
    queue_name = "arq:content"
    max_jobs = 20
    job_timeout = 120
    redis_settings = REDIS_SETTINGS
    on_startup = worker_startup
    on_shutdown = worker_shutdown


class RenderWorkerSettings:
    """ARQ settings for render workers (CPU-bound)."""

    from deckforge.workers.tasks import render_presentation

    functions = [render_presentation]
    queue_name = "arq:render"
    max_jobs = 4
    job_timeout = 60
    redis_settings = REDIS_SETTINGS
    on_startup = worker_startup
    on_shutdown = worker_shutdown
