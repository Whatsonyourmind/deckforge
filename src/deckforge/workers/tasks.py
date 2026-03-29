"""ARQ task functions for rendering and content generation.

Implements the full rendering pipeline: IR validation -> layout engine ->
PPTX renderer -> S3 upload. Also provides a synchronous render helper for
small presentations (<=10 slides) called directly from the API layer.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from deckforge.db.repositories import deck_repo, job_repo
from deckforge.ir import Presentation
from deckforge.layout.engine import LayoutEngine
from deckforge.layout.text_measurer import TextMeasurer
from deckforge.rendering import PptxRenderer
from deckforge.themes.registry import ThemeRegistry
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


def render_pipeline(
    presentation: Presentation,
    output_format: str = "pptx",
    credentials=None,
) -> bytes:
    """Run the full render pipeline synchronously.

    Supports PPTX (default) and Google Slides output formats.

    This is the core rendering function shared by both the async worker task
    and the synchronous API path (<=10 slides).

    Args:
        presentation: Validated IR Presentation model.
        output_format: "pptx" (default) or "gslides" for Google Slides.
        credentials: Google OAuth credentials (required for gslides).

    Returns:
        Raw bytes of the generated .pptx file (for pptx format),
        or GoogleSlidesResult (for gslides format).
    """
    theme_registry = ThemeRegistry()
    text_measurer = TextMeasurer()
    layout_engine = LayoutEngine(text_measurer, theme_registry)

    # Run layout engine
    layout_results = layout_engine.layout_presentation(presentation)

    # Resolve theme
    theme = theme_registry.get_theme(
        presentation.theme,
        presentation.brand_kit,
    )

    if output_format == "gslides":
        from deckforge.rendering.gslides import GoogleSlidesRenderer

        renderer = GoogleSlidesRenderer()
        return renderer.render(presentation, layout_results, theme, credentials)
    else:
        # Default: PPTX
        renderer = PptxRenderer()
        return renderer.render(presentation, layout_results, theme)


async def render_presentation(
    ctx: dict,
    job_id: str,
    ir_data: dict,
    webhook_url: str | None = None,
) -> dict:
    """Render a presentation from IR data.

    Pipeline:
    1. Update job status to running
    2. Validate IR with Pydantic
    3. Run layout engine + PPTX renderer to produce .pptx bytes
    4. Upload to S3
    5. Update deck/job status to complete
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
        await publish_progress(ctx, job_id, "rendering", 0.3)

        # 3. Run full render pipeline (layout + PPTX)
        pptx_bytes = render_pipeline(presentation)
        await publish_progress(ctx, job_id, "uploading", 0.8)

        file_key = f"renders/{job_id}/{uuid.uuid4().hex}.pptx"
        content_type = (
            "application/vnd.openxmlformats-officedocument"
            ".presentationml.presentation"
        )
        file_url = None

        # 4. Upload to S3
        if s3_client:
            ensure_bucket(s3_client, s3_bucket)
            upload_file(
                s3_client,
                s3_bucket,
                file_key,
                pptx_bytes,
                content_type,
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
    generation_options: dict | None = None,
    theme: str = "executive-dark",
    llm_config: dict | None = None,
    webhook_url: str | None = None,
) -> dict:
    """Generate presentation content from a natural language prompt.

    Pipeline:
    1. Create LLMRouter (from user config or settings defaults)
    2. Run ContentPipeline (intent -> outline -> write -> refine)
    3. Render the generated Presentation IR to PPTX
    4. Upload to S3
    5. Update deck/job status to complete
    6. Fire webhook if configured
    """
    from deckforge.content.pipeline import ContentPipeline
    from deckforge.ir.metadata import GenerationOptions
    from deckforge.llm.models import LLMConfig
    from deckforge.llm.router import create_router

    db_factory = ctx.get("db_factory")
    s3_client = ctx.get("s3_client")
    s3_bucket = ctx.get("s3_bucket", "deckforge")

    try:
        # 1. Create LLMRouter
        user_llm_config = LLMConfig.model_validate(llm_config) if llm_config else None
        router = create_router(llm_config=user_llm_config)

        # 2. Run content pipeline with progress publishing
        pipeline = ContentPipeline(router)

        gen_opts = (
            GenerationOptions.model_validate(generation_options)
            if generation_options
            else None
        )

        async def progress_callback(stage: str, progress: float) -> None:
            await publish_progress(ctx, job_id, stage, progress)

        ir_data = await pipeline.run(
            prompt,
            generation_options=gen_opts,
            progress_callback=progress_callback,
        )

        # 3. Render the IR to PPTX
        presentation = Presentation.model_validate(ir_data)
        pptx_bytes = render_pipeline(presentation)
        await publish_progress(ctx, job_id, "uploading", 0.95)

        file_key = f"renders/{job_id}/{uuid.uuid4().hex}.pptx"
        content_type = (
            "application/vnd.openxmlformats-officedocument"
            ".presentationml.presentation"
        )
        file_url = None

        # 4. Upload to S3
        if s3_client:
            ensure_bucket(s3_client, s3_bucket)
            upload_file(s3_client, s3_bucket, file_key, pptx_bytes, content_type)
            file_url = get_download_url(s3_client, s3_bucket, file_key)

        # 5. Update deck/job status to complete
        if db_factory:
            async with db_factory() as session:
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
                    result={"file_key": file_key, "file_url": file_url, "ir": ir_data},
                )
                await session.commit()

        await publish_progress(ctx, job_id, "complete", 1.0)

        # 6. Fire webhook if configured
        if webhook_url:
            await deliver_webhook(
                webhook_url,
                {
                    "event": "generate.complete",
                    "job_id": job_id,
                    "file_url": file_url,
                },
            )

        return {"status": "complete", "file_key": file_key, "file_url": file_url}

    except Exception as exc:
        logger.exception("generate_content failed for job %s", job_id)

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
