"""Alembic environment configuration for async migrations.

Imports all SQLAlchemy models so autogenerate can detect schema changes.
Supports both offline (SQL script) and online (direct connection) modes.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from deckforge.db.base import Base

# Import all models so Alembic sees them for autogenerate
from deckforge.db.models import ApiKey, Deck, Job, User  # noqa: F401

# Alembic Config object
config = context.config

# Set up logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData for autogenerate support
target_metadata = Base.metadata


def _get_url() -> str:
    """Return the database URL, preferring the env var over alembic.ini."""
    import os

    env_url = os.environ.get("DECKFORGE_DATABASE_URL")
    if env_url:
        # Normalise Render-style URLs for SQLAlchemy
        if env_url.startswith("postgres://"):
            env_url = env_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif env_url.startswith("postgresql://"):
            env_url = env_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return env_url
    return config.get_main_option("sqlalchemy.url")  # type: ignore[return-value]


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates SQL scripts without connecting to the database.
    """
    url = _get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations within a connection context."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine.

    Creates an async engine and associates a connection with the context.
    """
    section = dict(config.get_section(config.config_ini_section, {}))
    section["sqlalchemy.url"] = _get_url()
    connectable = async_engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (delegates to async)."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
