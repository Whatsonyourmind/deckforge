"""ARQ task functions for rendering and content generation.

Implements the full rendering pipeline: IR validation -> layout engine ->
PPTX renderer -> QA pipeline -> S3 upload. Also provides a synchronous
render helper for small presentations (<=10 slides) called directly from
the API layer.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from deckforge.db.repositories import batch_repo, deck_repo, job_repo, webhook_repo
from deckforge.ir import Presentation
from deckforge.ir.normalize import normalize_ir
from deckforge.layout.engine import LayoutEngine
from deckforge.layout.text_measurer import TextMeasurer
from deckforge.qa.pipeline import QAPipeline
from deckforge.qa.types import QAReport
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
) -> tuple[bytes, QAReport] | tuple:
    """Run the full render pipeline synchronously with QA pass.

    Supports PPTX (default) and Google Slides output formats.

    This is the core rendering function shared by both the async worker task
    and the synchronous API path (<=10 slides).

    Args:
        presentation: Validated IR Presentation model.
        output_format: "pptx" (default) or "gslides" for Google Slides.
        credentials: Google OAuth credentials (required for gslides).

    Returns:
        For PPTX: tuple of (pptx_bytes, qa_report).
        For Google Slides: tuple of (GoogleSlidesResult, qa_report).
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
        result = renderer.render(presentation, layout_results, theme, credentials)

        # QA pass
        qa_pipeline = QAPipeline(theme_registry)
        qa_report = qa_pipeline.run(presentation, layout_results, theme)

        return result, qa_report
    else:
        # Default: PPTX
        renderer = PptxRenderer()
        pptx_bytes = renderer.render(presentation, layout_results, theme)

        # QA pass
        qa_pipeline = QAPipeline(theme_registry)
        qa_report = qa_pipeline.run(presentation, layout_results, theme)

        return pptx_bytes, qa_report


async def _fire_registered_webhooks(
    db_factory,
    api_key_id: uuid.UUID,
    event_type: str,
    payload: dict,
) -> None:
    """Look up registered webhooks for an event and deliver with HMAC signing."""
    if not db_factory:
        return

    async with db_factory() as session:
        hooks = await webhook_repo.get_by_event(session, api_key_id, event_type)

    for hook in hooks:
        try:
            await deliver_webhook(
                hook.url,
                payload,
                secret=hook.secret,
            )
        except Exception:
            logger.warning(
                "Failed to deliver registered webhook to %s for event %s",
                hook.url,
                event_type,
            )


async def _handle_batch_completion(
    db_factory,
    batch_id: uuid.UUID,
    api_key_id: uuid.UUID,
    job_id: str,
    success: bool,
) -> None:
    """Update batch counters and fire batch.complete webhook if done."""
    if not db_factory:
        return

    async with db_factory() as session:
        if success:
            batch = await batch_repo.increment_completed(session, batch_id)
        else:
            batch = await batch_repo.increment_failed(session, batch_id)
        await session.commit()

    # Check if batch is now complete
    if batch and batch.status in ("complete", "partial_failure", "failed"):
        event = f"batch.{batch.status}"
        batch_payload = {
            "event": event,
            "batch_id": str(batch_id),
            "total": batch.total_items,
            "completed": batch.completed_items,
            "failed": batch.failed_items,
        }

        # Fire batch webhook URL if configured
        if batch.webhook_url:
            await deliver_webhook(batch.webhook_url, batch_payload)

        # Fire registered webhooks for batch event
        await _fire_registered_webhooks(
            db_factory, api_key_id, event, batch_payload
        )


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
    3. Run layout engine + PPTX renderer + QA pipeline to produce .pptx bytes
    4. Upload to S3
    5. Update deck/job status to complete with quality_score
    6. Fire webhooks (direct + registered)
    7. Handle batch completion if part of a batch
    """
    db_factory = ctx.get("db_factory")
    s3_client = ctx.get("s3_client")
    s3_bucket = ctx.get("s3_bucket", "deckforge")

    try:
        # 1. Update job status to running
        await publish_progress(ctx, job_id, "validating", 0.1)

        # 2. Normalize + Validate IR
        presentation = Presentation.model_validate(normalize_ir(ir_data))
        await publish_progress(ctx, job_id, "rendering", 0.3)

        # 3. Run full render pipeline (layout + PPTX + QA)
        pptx_bytes, qa_report = render_pipeline(presentation)
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

        # 5. Update deck/job status to complete with quality_score
        api_key_id = None
        batch_id = None
        if db_factory:
            async with db_factory() as session:
                # Find the job to get deck_id, api_key_id, batch_id
                job = await job_repo.get_by_id(session, uuid.UUID(job_id))
                if job:
                    api_key_id = job.api_key_id
                    batch_id = job.batch_id
                    if job.deck_id:
                        await deck_repo.update_status(
                            session,
                            job.deck_id,
                            "complete",
                            file_url=file_url,
                            quality_score=qa_report.score,
                        )
                await job_repo.update_status(
                    session,
                    uuid.UUID(job_id),
                    "complete",
                    progress=1.0,
                    result={
                        "file_key": file_key,
                        "file_url": file_url,
                        "quality_score": qa_report.score,
                        "quality_grade": qa_report.grade,
                    },
                )
                await session.commit()

        await publish_progress(ctx, job_id, "complete", 1.0)

        # 6. Fire webhooks
        webhook_payload = {
            "event": "render.complete",
            "job_id": job_id,
            "file_url": file_url,
            "quality_score": qa_report.score,
            "quality_grade": qa_report.grade,
        }

        # Direct webhook URL (from request parameter)
        if webhook_url:
            await deliver_webhook(webhook_url, webhook_payload)

        # Registered webhooks (from DB)
        if api_key_id:
            await _fire_registered_webhooks(
                db_factory, api_key_id, "render.complete", webhook_payload
            )

        # 7. Handle batch completion
        if batch_id and api_key_id:
            await _handle_batch_completion(
                db_factory, batch_id, api_key_id, job_id, success=True
            )

        return {
            "status": "complete",
            "file_key": file_key,
            "file_url": file_url,
            "quality_score": qa_report.score,
        }

    except Exception as exc:
        logger.exception("render_presentation failed for job %s", job_id)

        # Update status to failed
        api_key_id = None
        batch_id = None
        if db_factory:
            async with db_factory() as session:
                job = await job_repo.get_by_id(session, uuid.UUID(job_id))
                if job:
                    api_key_id = job.api_key_id
                    batch_id = job.batch_id
                    if job.deck_id:
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

        # Handle batch failure
        if batch_id and api_key_id:
            await _handle_batch_completion(
                db_factory, batch_id, api_key_id, job_id, success=False
            )

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
    3. Render the generated Presentation IR to PPTX with QA
    4. Upload to S3
    5. Update deck/job status to complete with quality_score
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

        # 3. Render the IR to PPTX with QA
        presentation = Presentation.model_validate(ir_data)
        pptx_bytes, qa_report = render_pipeline(presentation)
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

        # 5. Update deck/job status to complete with quality_score
        if db_factory:
            async with db_factory() as session:
                job = await job_repo.get_by_id(session, uuid.UUID(job_id))
                if job and job.deck_id:
                    await deck_repo.update_status(
                        session,
                        job.deck_id,
                        "complete",
                        file_url=file_url,
                        quality_score=qa_report.score,
                    )
                await job_repo.update_status(
                    session,
                    uuid.UUID(job_id),
                    "complete",
                    progress=1.0,
                    result={
                        "file_key": file_key,
                        "file_url": file_url,
                        "ir": ir_data,
                        "quality_score": qa_report.score,
                        "quality_grade": qa_report.grade,
                    },
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
                    "quality_score": qa_report.score,
                    "quality_grade": qa_report.grade,
                },
            )

        return {
            "status": "complete",
            "file_key": file_key,
            "file_url": file_url,
            "quality_score": qa_report.score,
        }

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
