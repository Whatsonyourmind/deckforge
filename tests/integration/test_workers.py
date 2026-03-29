"""Integration tests for ARQ worker infrastructure: storage, webhooks, tasks.

Uses mocked S3 (unittest.mock), fakeredis for Redis, and in-memory SQLite
for database -- no Docker required.
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import MagicMock, patch

import pytest
import respx
from fakeredis.aioredis import FakeRedis
from httpx import Response
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from deckforge.db.base import Base
from deckforge.db.models.api_key import ApiKey
from deckforge.db.models.deck import Deck
from deckforge.db.models.job import Job
from deckforge.db.models.user import User
from deckforge.db.repositories import deck_repo, job_repo
from deckforge.workers.storage import (
    delete_file,
    get_download_url,
    upload_file,
)
from deckforge.workers.tasks import generate_content, publish_progress, render_presentation
from deckforge.workers.webhooks import deliver_webhook


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def worker_engine():
    """In-memory SQLite engine for worker tests."""
    eng = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def worker_db_factory(worker_engine):
    """Session factory bound to the worker test engine."""
    return async_sessionmaker(worker_engine, expire_on_commit=False)


@pytest.fixture
async def worker_session(worker_db_factory):
    """Individual session for setup/assertions."""
    async with worker_db_factory() as sess:
        yield sess


@pytest.fixture
async def worker_redis():
    """FakeRedis for worker tests."""
    redis = FakeRedis(decode_responses=True)
    yield redis
    await redis.aclose()


@pytest.fixture
async def seed_worker_data(worker_session: AsyncSession):
    """Seed a user, API key, deck, and job for worker tests."""
    user = User(email="worker-test@example.com")
    worker_session.add(user)
    await worker_session.flush()

    api_key = ApiKey(
        user_id=user.id,
        key_hash="w" * 64,
        key_prefix="dk_test_wrk",
        name="Worker Key",
    )
    worker_session.add(api_key)
    await worker_session.flush()

    deck = Deck(
        api_key_id=api_key.id,
        ir_snapshot={},
        request_id="worker_req_001",
    )
    worker_session.add(deck)
    await worker_session.flush()

    job = Job(
        api_key_id=api_key.id,
        job_type="render",
        queue_name="arq:render",
        deck_id=deck.id,
    )
    worker_session.add(job)
    await worker_session.flush()
    await worker_session.commit()

    return user, api_key, deck, job


@pytest.fixture
def worker_ctx(worker_db_factory, worker_redis):
    """ARQ worker context dict with test dependencies."""
    mock_s3 = MagicMock()
    mock_s3.generate_presigned_url.return_value = "https://s3.example.com/file.json"

    return {
        "db_factory": worker_db_factory,
        "redis": worker_redis,
        "s3_client": mock_s3,
        "s3_bucket": "test-bucket",
    }


# ---------------------------------------------------------------------------
# Storage tests
# ---------------------------------------------------------------------------


def test_upload_file_calls_put_object():
    """storage.upload_file uploads data via put_object."""
    mock_client = MagicMock()
    key = upload_file(mock_client, "mybucket", "test.json", b'{"a":1}', "application/json")

    mock_client.put_object.assert_called_once_with(
        Bucket="mybucket",
        Key="test.json",
        Body=b'{"a":1}',
        ContentType="application/json",
    )
    assert key == "test.json"


def test_get_download_url_generates_presigned():
    """storage.get_download_url generates a presigned URL."""
    mock_client = MagicMock()
    mock_client.generate_presigned_url.return_value = "https://example.com/test.json?sig=abc"

    url = get_download_url(mock_client, "mybucket", "test.json", expires_in=7200)

    mock_client.generate_presigned_url.assert_called_once_with(
        "get_object",
        Params={"Bucket": "mybucket", "Key": "test.json"},
        ExpiresIn=7200,
    )
    assert "example.com" in url


def test_delete_file_calls_delete_object():
    """storage.delete_file calls delete_object."""
    mock_client = MagicMock()
    delete_file(mock_client, "mybucket", "test.json")
    mock_client.delete_object.assert_called_once_with(Bucket="mybucket", Key="test.json")


# ---------------------------------------------------------------------------
# Webhook tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_deliver_webhook_sends_post():
    """deliver_webhook sends a POST with correct JSON payload."""
    route = respx.post("https://hooks.example.com/callback").mock(
        return_value=Response(200)
    )

    result = await deliver_webhook(
        "https://hooks.example.com/callback",
        {"event": "render.complete", "job_id": "123"},
    )

    assert result is True
    assert route.called
    request = route.calls[0].request
    body = json.loads(request.content)
    assert body["event"] == "render.complete"
    assert body["job_id"] == "123"


@pytest.mark.asyncio
@respx.mock
async def test_deliver_webhook_retries_on_failure():
    """deliver_webhook retries on server error and eventually fails."""
    route = respx.post("https://hooks.example.com/fail").mock(
        return_value=Response(500)
    )

    result = await deliver_webhook(
        "https://hooks.example.com/fail",
        {"event": "test"},
        max_retries=2,
    )

    assert result is False
    assert route.call_count == 2


# ---------------------------------------------------------------------------
# Publish progress tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_publish_progress_publishes_to_redis(worker_ctx, seed_worker_data):
    """publish_progress publishes to the correct Redis channel."""
    _, _, _, job = seed_worker_data
    redis = worker_ctx["redis"]

    # Track published messages by wrapping the publish method
    published: list[tuple[str, str]] = []
    original_publish = redis.publish

    async def tracking_publish(channel, message):
        published.append((channel, message))
        return await original_publish(channel, message)

    redis.publish = tracking_publish

    await publish_progress(worker_ctx, str(job.id), "rendering", 0.5)

    assert len(published) == 1
    channel, raw_message = published[0]
    assert channel == f"job:{job.id}:progress"
    data = json.loads(raw_message)
    assert data["stage"] == "rendering"
    assert data["progress"] == 0.5
    assert "timestamp" in data

    # Restore original
    redis.publish = original_publish


# ---------------------------------------------------------------------------
# Task tests
# ---------------------------------------------------------------------------


MINIMAL_IR = {
    "schema_version": "1.0",
    "metadata": {"title": "Worker Test"},
    "slides": [{"slide_type": "title_slide", "title": "Test"}],
}


@pytest.mark.asyncio
async def test_render_presentation_validates_and_completes(worker_ctx, seed_worker_data):
    """render_presentation validates IR, uploads result, and updates job status."""
    _, _, deck, job = seed_worker_data

    result = await render_presentation(worker_ctx, str(job.id), MINIMAL_IR)

    assert result["status"] == "complete"
    assert "file_key" in result

    # Verify S3 upload was called
    worker_ctx["s3_client"].put_object.assert_called_once()

    # Verify job was updated in database
    async with worker_ctx["db_factory"]() as session:
        updated_job = await job_repo.get_by_id(session, job.id)
        assert updated_job.status == "complete"
        assert updated_job.progress == 1.0


@pytest.mark.asyncio
async def test_generate_content_produces_ir_and_publishes_progress(
    worker_ctx, seed_worker_data
):
    """generate_content creates minimal IR and publishes progress events."""
    _, _, _, job = seed_worker_data

    # Change the job type to content for this test
    async with worker_ctx["db_factory"]() as session:
        await job_repo.update_status(session, job.id, "queued")
        await session.commit()

    # Track published messages
    redis = worker_ctx["redis"]
    published_stages: list[str] = []
    original_publish = redis.publish

    async def tracking_publish(channel, message):
        data = json.loads(message)
        published_stages.append(data["stage"])
        return await original_publish(channel, message)

    redis.publish = tracking_publish

    result = await generate_content(worker_ctx, str(job.id), "Quarterly earnings review")

    assert result["status"] == "complete"
    assert "ir" in result
    ir = result["ir"]
    assert ir["metadata"]["title"] == "Quarterly earnings review"
    assert len(ir["slides"]) >= 1

    # Verify progress stages were published
    assert "parsing" in published_stages
    assert "complete" in published_stages

    # Restore original
    redis.publish = original_publish
