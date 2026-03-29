"""Integration tests for database models and repositories.

Uses an in-memory SQLite async engine for test isolation -- no Docker or
PostgreSQL required. Tests verify that all models create tables correctly
and that repository CRUD operations work as expected.

Note: SQLite does not support JSONB natively, so JSONB columns fall back
to JSON (SQLAlchemy handles the dialect mapping automatically).
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from deckforge.db.base import Base
from deckforge.db.models.api_key import ApiKey
from deckforge.db.models.deck import Deck
from deckforge.db.models.job import Job
from deckforge.db.models.user import User
from deckforge.db.repositories.api_key import ApiKeyRepository
from deckforge.db.repositories.deck import DeckRepository
from deckforge.db.repositories.job import JobRepository


@pytest.fixture
async def engine():
    """Create an in-memory SQLite async engine for testing."""
    eng = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session(engine):
    """Provide an async session bound to the test engine."""
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as sess:
        yield sess
        await sess.rollback()


# ---------------------------------------------------------------------------
# Table creation tests
# ---------------------------------------------------------------------------


async def test_all_tables_created(engine):
    """Verify that create_all produces all expected tables."""
    async with engine.connect() as conn:
        table_names = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )
    assert "users" in table_names
    assert "api_keys" in table_names
    assert "decks" in table_names
    assert "jobs" in table_names


# ---------------------------------------------------------------------------
# Model creation tests
# ---------------------------------------------------------------------------


async def test_user_model_create(session: AsyncSession):
    """User model creates with all fields."""
    user = User(email="test@example.com", name="Test User")
    session.add(user)
    await session.flush()

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.is_active is True


async def test_api_key_model_create(session: AsyncSession):
    """ApiKey model creates with JSONB scopes."""
    user = User(email="key-owner@example.com")
    session.add(user)
    await session.flush()

    api_key = ApiKey(
        user_id=user.id,
        key_hash="a" * 64,
        key_prefix="dk_live_abc",
        name="My Test Key",
        scopes=["read", "generate", "admin"],
        tier="pro",
    )
    session.add(api_key)
    await session.flush()

    assert api_key.id is not None
    assert api_key.scopes == ["read", "generate", "admin"]
    assert api_key.tier == "pro"
    assert api_key.is_active is True
    assert api_key.is_test is False


async def test_deck_model_create(session: AsyncSession):
    """Deck model creates with JSONB ir_snapshot."""
    user = User(email="deck-owner@example.com")
    session.add(user)
    await session.flush()

    api_key = ApiKey(
        user_id=user.id,
        key_hash="b" * 64,
        key_prefix="dk_live_def",
        name="Deck Key",
    )
    session.add(api_key)
    await session.flush()

    ir_data = {
        "metadata": {"title": "Q4 Earnings"},
        "slides": [{"slide_type": "title", "elements": []}],
    }
    deck = Deck(
        api_key_id=api_key.id,
        ir_snapshot=ir_data,
        request_id="req_123",
    )
    session.add(deck)
    await session.flush()

    assert deck.id is not None
    assert deck.ir_snapshot == ir_data
    assert deck.status == "pending"
    assert deck.request_id == "req_123"


async def test_job_model_create(session: AsyncSession):
    """Job model creates with all status fields."""
    user = User(email="job-owner@example.com")
    session.add(user)
    await session.flush()

    api_key = ApiKey(
        user_id=user.id,
        key_hash="c" * 64,
        key_prefix="dk_live_ghi",
        name="Job Key",
    )
    session.add(api_key)
    await session.flush()

    job = Job(
        api_key_id=api_key.id,
        job_type="render",
        queue_name="arq:render",
    )
    session.add(job)
    await session.flush()

    assert job.id is not None
    assert job.job_type == "render"
    assert job.queue_name == "arq:render"
    assert job.status == "queued"
    assert job.progress == 0.0
    assert job.result is None


# ---------------------------------------------------------------------------
# Repository tests
# ---------------------------------------------------------------------------


@pytest.fixture
async def seed_user_and_key(session: AsyncSession):
    """Seed a user and API key for repository tests."""
    user = User(email="repo-test@example.com")
    session.add(user)
    await session.flush()

    api_key = ApiKey(
        user_id=user.id,
        key_hash="d" * 64,
        key_prefix="dk_test_xyz",
        name="Repo Test Key",
    )
    session.add(api_key)
    await session.flush()

    return user, api_key


async def test_api_key_repo_create_and_get_by_id(
    session: AsyncSession,
    seed_user_and_key,
):
    """ApiKeyRepository creates and retrieves by ID."""
    user, _ = seed_user_and_key
    repo = ApiKeyRepository()

    key = await repo.create(
        session,
        user_id=user.id,
        key_hash="e" * 64,
        key_prefix="dk_live_new",
        name="New Key",
        scopes=["read"],
        tier="starter",
    )
    assert key.id is not None

    found = await repo.get_by_id(session, key.id)
    assert found is not None
    assert found.name == "New Key"


async def test_api_key_repo_get_by_hash(
    session: AsyncSession,
    seed_user_and_key,
):
    """ApiKeyRepository retrieves by hash."""
    user, _ = seed_user_and_key
    repo = ApiKeyRepository()

    target_hash = "f" * 64
    await repo.create(
        session,
        user_id=user.id,
        key_hash=target_hash,
        key_prefix="dk_live_hsh",
        name="Hash Key",
    )

    found = await repo.get_by_hash(session, target_hash)
    assert found is not None
    assert found.key_prefix == "dk_live_hsh"

    not_found = await repo.get_by_hash(session, "0" * 64)
    assert not_found is None


async def test_deck_repo_create_and_get_by_id(
    session: AsyncSession,
    seed_user_and_key,
):
    """DeckRepository creates and retrieves by ID."""
    _, api_key = seed_user_and_key
    repo = DeckRepository()

    deck = await repo.create(
        session,
        api_key_id=api_key.id,
        ir_snapshot={"slides": []},
    )
    assert deck.id is not None

    found = await repo.get_by_id(session, deck.id)
    assert found is not None
    assert found.ir_snapshot == {"slides": []}


async def test_deck_repo_get_by_request_id(
    session: AsyncSession,
    seed_user_and_key,
):
    """DeckRepository retrieves by request_id for idempotency."""
    _, api_key = seed_user_and_key
    repo = DeckRepository()

    await repo.create(
        session,
        api_key_id=api_key.id,
        ir_snapshot={"slides": [{"type": "title"}]},
        request_id="idempotent_req_001",
    )

    found = await repo.get_by_request_id(session, "idempotent_req_001")
    assert found is not None
    assert found.request_id == "idempotent_req_001"

    not_found = await repo.get_by_request_id(session, "nonexistent")
    assert not_found is None


async def test_job_repo_create_and_get_by_id(
    session: AsyncSession,
    seed_user_and_key,
):
    """JobRepository creates and retrieves by ID."""
    _, api_key = seed_user_and_key
    repo = JobRepository()

    job = await repo.create(
        session,
        api_key_id=api_key.id,
        job_type="generate",
        queue_name="arq:content",
    )
    assert job.id is not None

    found = await repo.get_by_id(session, job.id)
    assert found is not None
    assert found.job_type == "generate"
    assert found.queue_name == "arq:content"


async def test_job_repo_get_active_jobs(
    session: AsyncSession,
    seed_user_and_key,
):
    """JobRepository returns only active (queued/running) jobs."""
    _, api_key = seed_user_and_key
    repo = JobRepository()

    # Create one queued, one running, one complete
    await repo.create(
        session, api_key_id=api_key.id, job_type="render", queue_name="arq:render"
    )
    job2 = await repo.create(
        session, api_key_id=api_key.id, job_type="generate", queue_name="arq:content"
    )
    await repo.update_status(session, job2.id, "running")

    job3 = await repo.create(
        session, api_key_id=api_key.id, job_type="render", queue_name="arq:render"
    )
    await repo.update_status(session, job3.id, "complete")

    active = await repo.get_active_jobs(session, api_key.id)
    assert len(active) == 2
    statuses = {j.status for j in active}
    assert statuses == {"queued", "running"}
