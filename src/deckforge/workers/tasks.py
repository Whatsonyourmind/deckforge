"""ARQ task functions for rendering and content generation.

These are stub implementations that validate IR, publish progress events,
upload placeholder results to S3, and fire webhooks. Real rendering logic
will be added in Phase 3.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from deckforge.db.repositories import deck_repo, job_repo
from deckforge.ir import Presentation
from deckforge.workers.storage import ensure_bucket, get_download_url, upload_file
from deckforge.workers.webhooks import deliver_webhook

logger = logging.getLogger(__name__)


async def publish_progress(
    ctx: dict,
    job_id: str,
    stage: str,
    progress: float,
) -> None:
    """Publish a job progress event to Redis pub/sub and update the database.

    Publishes to channel ``job:{job_id}:progress`` with JSON payload
    containing stage, progress, and timestamp.
    """
    redis = ctx.get("redis")
    if redis:
        payload = json.dumps(
            {
                "stage": stage,
                "progress": progress,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        await redis.publish(f"job:{job_id}:progress", payload)

    # Update job progress in database (skip for terminal stages --
    # the task function handles the final status update itself)
    if stage not in ("complete", "failed"):
        db_factory = ctx.get("db_factory")
        if db_factory:
            async with db_factory() as session:
                await job_repo.update_status(
                    session,
                    uuid.UUID(job_id),
                    "running",
                    progress=progress,
                )
                await session.commit()


async def render_presentation(
    ctx: dict,
    job_id: str,
    ir_data: dict,
    webhook_url: str | None = None,
) -> dict:
    """Render a presentation from IR data (stub).

    Pipeline:
    1. Update job status to running
    2. Validate IR with Pydantic
    3. Create placeholder output (JSON of validated IR)
    4. Upload to S3
    5. Update deck status to complete
    6. Fire webhook if configured
    """
    db_factory = ctx.get("db_factory")
    s3_client = ctx.get("s3_client")
    s3_bucket = ctx.get("s3_bucket", "deckforge")

    try:
        # 1. Update job status to running
        await publish_progress(ctx, job_id, "validating", 0.1)

        # 2. Validate IR
        presentation = Presentation.model_validate(ir_data)
        await publish_progress(ctx, job_id, "rendering", 0.5)

        # 3. Create placeholder file (JSON of validated IR)
        output_data = json.dumps(
            presentation.model_dump(mode="json"),
            indent=2,
        ).encode("utf-8")

        file_key = f"renders/{job_id}/{uuid.uuid4().hex}.json"
        file_url = None

        # 4. Upload to S3
        if s3_client:
            ensure_bucket(s3_client, s3_bucket)
            upload_file(
                s3_client,
                s3_bucket,
                file_key,
                output_data,
                "application/json",
            )
            file_url = get_download_url(s3_client, s3_bucket, file_key)

        # 5. Update deck/job status to complete
        if db_factory:
            async with db_factory() as session:
                # Find the deck associated with this job
                job = await job_repo.get_by_id(session, uuid.UUID(job_id))
                if job and job.deck_id:
                    await deck_repo.update_status(
                        session,
                        job.deck_id,
                        "complete",
                        file_url=file_url,
                    )
                await job_repo.update_status(
                    session,
                    uuid.UUID(job_id),
                    "complete",
                    progress=1.0,
                    result={"file_key": file_key, "file_url": file_url},
                )
                await session.commit()

        await publish_progress(ctx, job_id, "complete", 1.0)

        # 6. Fire webhook if configured
        if webhook_url:
            await deliver_webhook(
                webhook_url,
                {
                    "event": "render.complete",
                    "job_id": job_id,
                    "file_url": file_url,
                },
            )

        return {"status": "complete", "file_key": file_key, "file_url": file_url}

    except Exception as exc:
        logger.exception("render_presentation failed for job %s", job_id)

        # Update status to failed
        if db_factory:
            async with db_factory() as session:
                job = await job_repo.get_by_id(session, uuid.UUID(job_id))
                if job and job.deck_id:
                    await deck_repo.update_status(
                        session,
                        job.deck_id,
                        "failed",
                        error=str(exc),
                    )
                await job_repo.update_status(
                    session,
                    uuid.UUID(job_id),
                    "failed",
                    error=str(exc),
                )
                await session.commit()

        raise


async def generate_content(
    ctx: dict,
    job_id: str,
    prompt: str,
    webhook_url: str | None = None,
) -> dict:
    """Generate presentation content from a prompt (stub).

    Pipeline:
    1. Update job status to running
    2. Parse prompt, outline, write, refine (all stubbed)
    3. Create minimal IR with a title slide from the prompt
    4. Enqueue render_presentation with the generated IR
    """
    db_factory = ctx.get("db_factory")

    try:
        await publish_progress(ctx, job_id, "parsing", 0.1)
        await publish_progress(ctx, job_id, "outlining", 0.3)
        await publish_progress(ctx, job_id, "writing", 0.6)
        await publish_progress(ctx, job_id, "refining", 0.8)

        # Create minimal IR from the prompt
        ir_data = {
            "schema_version": "1.0",
            "metadata": {"title": prompt[:100]},
            "slides": [
                {
                    "slide_type": "title_slide",
                    "title": prompt[:100],
                    "subtitle": "Auto-generated presentation",
                }
            ],
        }

        # Update job with generated IR
        if db_factory:
            async with db_factory() as session:
                await job_repo.update_status(
                    session,
                    uuid.UUID(job_id),
                    "complete",
                    progress=1.0,
                    result={"ir": ir_data},
                )
                await session.commit()

        await publish_progress(ctx, job_id, "complete", 1.0)

        # In a real implementation, we would enqueue render_presentation here:
        # await ctx["redis"].enqueue_job("render_presentation", job_id=..., ir_data=ir_data)

        return {"status": "complete", "ir": ir_data}

    except Exception as exc:
        logger.exception("generate_content failed for job %s", job_id)

        if db_factory:
            async with db_factory() as session:
                await job_repo.update_status(
                    session,
                    uuid.UUID(job_id),
                    "failed",
                    error=str(exc),
                )
                await session.commit()

        raise
