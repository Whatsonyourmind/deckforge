"""Generate endpoint -- accepts NL prompts, enqueues content generation, streams progress.

POST /v1/generate: Accepts a prompt + optional config, creates a deck/job record,
and enqueues to the ARQ content worker queue.

GET /v1/generate/{job_id}/stream: SSE endpoint that subscribes to Redis pub/sub
for real-time progress events from the content pipeline.
"""

from __future__ import annotations

import asyncio
import json
import logging

from arq.connections import ArqRedis
from fastapi import APIRouter
from fastapi.responses import Response
from sse_starlette.sse import EventSourceResponse

from deckforge.api.deps import DbSession, RedisClient
from deckforge.api.middleware.auth import CurrentApiKey
from deckforge.api.middleware.credits import CreditCheck
from deckforge.api.middleware.rate_limit import RateLimited
from deckforge.api.schemas.requests import GenerateRequest
from deckforge.api.schemas.responses import GenerateResponse
from deckforge.db.repositories import deck_repo, job_repo

logger = logging.getLogger(__name__)

router = APIRouter(tags=["generate"])


@router.post(
    "/generate",
    response_model=GenerateResponse,
    status_code=202,
    responses={
        202: {"description": "Content generation job enqueued"},
        401: {"description": "Invalid or missing API key"},
        402: {"description": "Insufficient credits"},
        422: {"description": "Request validation error"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def generate(
    body: GenerateRequest,
    db: DbSession,
    redis: RedisClient,
    api_key: CurrentApiKey,
    _rate_limit: RateLimited,
    _credit_check: CreditCheck,
) -> GenerateResponse:
    """Start content generation from a natural language prompt.

    Creates a deck record and a job record, then enqueues the
    ``generate_content`` task to the ARQ content worker queue.
    """
    # Create a placeholder IR snapshot (will be populated by the pipeline)
    placeholder_ir = {
        "schema_version": "1.0",
        "metadata": {"title": body.prompt[:100]},
        "slides": [],
    }

    deck = await deck_repo.create(
        db,
        api_key_id=api_key.id,
        ir_snapshot=placeholder_ir,
    )

    job = await job_repo.create(
        db,
        api_key_id=api_key.id,
        job_type="generate",
        queue_name="arq:content",
        deck_id=deck.id,
    )
    await db.commit()

    # Serialize optional configs for task args
    gen_opts_dict = body.generation_options.model_dump() if body.generation_options else None
    llm_config_dict = body.llm_config.model_dump() if body.llm_config else None

    # Enqueue to ARQ content worker queue
    try:
        arq = ArqRedis(pool_or_conn=redis.connection_pool)
        await arq.enqueue_job(
            "generate_content",
            job_id=str(job.id),
            prompt=body.prompt,
            generation_options=gen_opts_dict,
            theme=body.theme,
            llm_config=llm_config_dict,
            webhook_url=body.webhook_url,
            _queue_name="arq:content",
        )
    except Exception:
        logger.warning("Failed to enqueue generate_content job %s", job.id)

    return GenerateResponse(
        job_id=str(job.id),
        status="queued",
        message="Content generation job enqueued",
    )


@router.get(
    "/generate/{job_id}/stream",
    responses={
        200: {"description": "SSE stream of pipeline progress events"},
        401: {"description": "Invalid or missing API key"},
    },
)
async def generate_stream(
    job_id: str,
    redis: RedisClient,
    api_key: CurrentApiKey,
) -> Response:
    """Stream pipeline progress events via Server-Sent Events.

    Subscribes to the Redis pub/sub channel ``job:{job_id}:progress``
    and yields SSE events for each pipeline stage update.

    Terminates when a ``complete`` or ``failed`` event is received,
    or after a 120-second server-side timeout.
    """

    async def event_generator():
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"job:{job_id}:progress")
        event_id = 0

        try:
            timeout = 120  # seconds
            deadline = asyncio.get_event_loop().time() + timeout

            while asyncio.get_event_loop().time() < deadline:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )
                if message and message["type"] == "message":
                    event_id += 1
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")

                    try:
                        payload = json.loads(data)
                        stage = payload.get("stage", "unknown")
                    except (json.JSONDecodeError, TypeError):
                        stage = "unknown"
                        payload = {"raw": data}

                    yield {
                        "id": str(event_id),
                        "event": stage,
                        "data": json.dumps(payload),
                    }

                    # Terminate on terminal events
                    if stage in ("complete", "failed"):
                        return
                else:
                    await asyncio.sleep(0.1)

        finally:
            await pubsub.unsubscribe(f"job:{job_id}:progress")
            await pubsub.aclose()

    return EventSourceResponse(event_generator())
