"""Shared test fixtures for DeckForge API integration tests.

Uses in-memory SQLite for database and fakeredis for Redis,
so tests run without Docker or external services.
"""

from __future__ import annotations

import hashlib
import uuid

import pytest
from fakeredis.aioredis import FakeRedis
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from deckforge.api.app import create_app
from deckforge.api.deps import get_redis
from deckforge.db.base import Base
from deckforge.db.engine import get_db
from deckforge.db.models.api_key import ApiKey
from deckforge.db.models.user import User


@pytest.fixture
async def engine():
    """Create an in-memory SQLite async engine for testing."""
    eng = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session_factory(engine):
    """Create a session factory bound to the test engine."""
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
async def session(session_factory):
    """Provide an async session bound to the test engine."""
    async with session_factory() as sess:
        yield sess
        await sess.rollback()


@pytest.fixture
async def fake_redis():
    """Provide a fakeredis instance for testing."""
    redis = FakeRedis(decode_responses=True)
    yield redis
    await redis.aclose()


# The raw API key string used in tests
TEST_RAW_KEY = "dk_test_abcdef1234567890"
TEST_KEY_HASH = hashlib.sha256(TEST_RAW_KEY.encode()).hexdigest()


@pytest.fixture
async def seed_api_key(session: AsyncSession):
    """Create a test user and API key in the database. Returns (user, api_key, raw_key)."""
    user = User(email="test-api@example.com", name="API Test User")
    session.add(user)
    await session.flush()

    api_key = ApiKey(
        user_id=user.id,
        key_hash=TEST_KEY_HASH,
        key_prefix="dk_test_abc",
        name="Test Key",
        scopes=["read", "generate"],
        tier="starter",
        is_test=True,
    )
    session.add(api_key)
    await session.flush()
    await session.commit()

    return user, api_key, TEST_RAW_KEY


@pytest.fixture
async def app(session_factory, fake_redis):
    """Create a FastAPI test app with overridden dependencies."""
    test_app = create_app()

    # Override get_db to use test session factory
    async def override_get_db():
        async with session_factory() as sess:
            yield sess

    # Override get_redis to use fakeredis
    async def override_get_redis():
        return fake_redis

    test_app.dependency_overrides[get_db] = override_get_db
    test_app.dependency_overrides[get_redis] = override_get_redis

    # Store fakeredis on app.state for health check (which accesses it directly)
    test_app.state.redis = fake_redis

    yield test_app


@pytest.fixture
async def async_client(app):
    """Provide an httpx AsyncClient wired to the test app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
