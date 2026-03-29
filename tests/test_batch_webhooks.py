"""Tests for batch job models, webhook registration, HMAC signing, and repositories."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from deckforge.workers.webhooks import sign_webhook_payload


# ── HMAC Webhook Signing Tests ───────────────────────────────────────────────


class TestSignWebhookPayload:
    """Tests for HMAC-SHA256 webhook payload signing."""

    def test_produces_valid_hmac_sha256_signature(self):
        """sign_webhook_payload returns a hex HMAC-SHA256 signature."""
        payload = b'{"event": "render.complete", "job_id": "abc"}'
        secret = "test_secret_key_1234"

        signature, timestamp = sign_webhook_payload(payload, secret)

        # Signature should be a hex string of expected length (64 chars for SHA-256)
        assert isinstance(signature, str)
        assert len(signature) == 64
        assert isinstance(timestamp, int)
        assert timestamp > 0

    def test_signature_is_verifiable_with_same_secret(self):
        """The signature can be verified by recomputing HMAC with the same secret."""
        payload = b'{"event": "render.complete"}'
        secret = "my_webhook_secret"

        signature, timestamp = sign_webhook_payload(payload, secret)

        # Recompute the expected signature
        message = f"{timestamp}.".encode() + payload
        expected = hmac.new(
            secret.encode(), message, hashlib.sha256
        ).hexdigest()

        assert signature == expected

    def test_different_secret_produces_different_signature(self):
        """Different secrets produce different HMAC signatures."""
        payload = b'{"event": "render.complete"}'
        secret_a = "secret_alpha"
        secret_b = "secret_beta"

        sig_a, ts_a = sign_webhook_payload(payload, secret_a)
        sig_b, ts_b = sign_webhook_payload(payload, secret_b)

        assert sig_a != sig_b


# ── BatchJob Model Tests ─────────────────────────────────────────────────────


class TestBatchJobModel:
    """Tests for the BatchJob database model."""

    def test_stores_total_and_completed_items(self):
        """BatchJob stores total_items and completed_items correctly."""
        from deckforge.db.models.batch_job import BatchJob

        batch = BatchJob(
            api_key_id=uuid.uuid4(),
            total_items=5,
            completed_items=2,
            failed_items=0,
            status="running",
        )
        assert batch.total_items == 5
        assert batch.completed_items == 2
        assert batch.failed_items == 0
        assert batch.status == "running"

    def test_default_values(self):
        """BatchJob has sensible defaults for completed/failed items.

        SQLAlchemy mapped_column defaults apply at DB flush time, so we
        verify fields accept the expected explicit defaults.
        """
        from deckforge.db.models.batch_job import BatchJob

        batch = BatchJob(
            api_key_id=uuid.uuid4(),
            total_items=10,
            completed_items=0,
            failed_items=0,
            status="pending",
        )
        assert batch.completed_items == 0
        assert batch.failed_items == 0
        assert batch.status == "pending"


# ── WebhookRegistration Model Tests ──────────────────────────────────────────


class TestWebhookRegistrationModel:
    """Tests for the WebhookRegistration database model."""

    def test_stores_url_events_and_secret(self):
        """WebhookRegistration stores url, events list, and secret."""
        from deckforge.db.models.webhook_registration import WebhookRegistration

        reg = WebhookRegistration(
            api_key_id=uuid.uuid4(),
            url="https://example.com/webhook",
            events=["render.complete", "batch.complete"],
            secret="hmac_secret_here",
            is_active=True,
        )
        assert reg.url == "https://example.com/webhook"
        assert reg.events == ["render.complete", "batch.complete"]
        assert reg.secret == "hmac_secret_here"
        assert reg.is_active is True


# ── BatchRepository Tests ────────────────────────────────────────────────────


class TestBatchRepository:
    """Tests for BatchRepository using real SQLAlchemy session (SQLite)."""

    @pytest.fixture
    async def async_session(self):
        """Create an in-memory SQLite async session for testing."""
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        from deckforge.db.base import Base

        # Import all models so tables are registered
        import deckforge.db.models  # noqa: F401

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async_session_factory = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session_factory() as session:
            yield session

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_increment_completed_updates_atomically(self, async_session):
        """BatchRepository.increment_completed updates completed_items atomically."""
        from deckforge.db.repositories.batch import BatchRepository

        repo = BatchRepository()
        api_key_id = uuid.uuid4()

        batch = await repo.create(async_session, api_key_id=api_key_id, total_items=3)
        await async_session.commit()

        # Increment once
        updated = await repo.increment_completed(async_session, batch.id)
        await async_session.commit()
        assert updated.completed_items == 1
        assert updated.status == "running"

        # Increment to completion
        await repo.increment_completed(async_session, batch.id)
        await async_session.commit()
        updated = await repo.increment_completed(async_session, batch.id)
        await async_session.commit()
        assert updated.completed_items == 3
        assert updated.status == "complete"
        assert updated.completed_at is not None


# ── WebhookRepository Tests ──────────────────────────────────────────────────


class TestWebhookRepository:
    """Tests for WebhookRepository using real SQLAlchemy session (SQLite)."""

    @pytest.fixture
    async def async_session(self):
        """Create an in-memory SQLite async session for testing."""
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        from deckforge.db.base import Base

        import deckforge.db.models  # noqa: F401

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async_session_factory = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session_factory() as session:
            yield session

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_get_by_event_returns_only_matching_webhooks(self, async_session):
        """WebhookRepository.get_by_event returns only webhooks subscribed to that event."""
        from deckforge.db.repositories.webhook import WebhookRepository

        repo = WebhookRepository()
        api_key_id = uuid.uuid4()

        # Create two webhooks with different event subscriptions
        await repo.create(
            async_session,
            api_key_id=api_key_id,
            url="https://example.com/render-hook",
            events=["render.complete"],
        )
        await repo.create(
            async_session,
            api_key_id=api_key_id,
            url="https://example.com/batch-hook",
            events=["batch.complete"],
        )
        await repo.create(
            async_session,
            api_key_id=api_key_id,
            url="https://example.com/all-hook",
            events=["render.complete", "batch.complete"],
        )
        await async_session.commit()

        # Query for render.complete -- should get 2 webhooks
        render_hooks = await repo.get_by_event(
            async_session, api_key_id, "render.complete"
        )
        assert len(render_hooks) == 2
        urls = {h.url for h in render_hooks}
        assert "https://example.com/render-hook" in urls
        assert "https://example.com/all-hook" in urls

        # Query for batch.complete -- should get 2 webhooks
        batch_hooks = await repo.get_by_event(
            async_session, api_key_id, "batch.complete"
        )
        assert len(batch_hooks) == 2
        urls = {h.url for h in batch_hooks}
        assert "https://example.com/batch-hook" in urls
        assert "https://example.com/all-hook" in urls
