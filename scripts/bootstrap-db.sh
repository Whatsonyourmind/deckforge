#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# DeckForge Database Bootstrap
# Runs Alembic migrations and seeds required data.
# Idempotent: safe to run multiple times.
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== DeckForge Database Bootstrap ==="
echo ""

# Step 1: Run Alembic migrations
echo "[1/3] Running Alembic migrations..."
cd "$PROJECT_DIR"
alembic upgrade head
echo "  Migrations complete."
echo ""

# Step 2: Seed admin user and test API key
echo "[2/3] Seeding database..."
python -c "
import sys, os, uuid, hashlib, secrets
sys.path.insert(0, '.')
os.environ.setdefault('DECKFORGE_DATABASE_URL', 'postgresql+psycopg://deckforge:deckforge@localhost:5432/deckforge')

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from src.deckforge.db.base import Base
from src.deckforge.db.models.user import User
from src.deckforge.db.models.api_key import ApiKey
from src.deckforge.config import settings

# Create a sync engine for the bootstrap script
# Replace async driver with sync driver for direct access
sync_url = settings.DATABASE_URL
if '+psycopg' in sync_url and 'async' not in sync_url:
    # psycopg3 works in sync mode with postgresql+psycopg
    pass
elif 'aiosqlite' in sync_url:
    sync_url = sync_url.replace('sqlite+aiosqlite', 'sqlite')
elif 'asyncpg' in sync_url:
    sync_url = sync_url.replace('postgresql+asyncpg', 'postgresql+psycopg')

engine = create_engine(sync_url, echo=False)

with Session(engine) as session:
    # Check if admin user already exists (idempotent)
    existing = session.execute(
        select(User).where(User.email == 'admin@deckforge.dev')
    ).scalar_one_or_none()

    if existing:
        print('  Seed data already exists (idempotent skip)')
        # Find existing test key to display prefix
        key = session.execute(
            select(ApiKey).where(ApiKey.user_id == existing.id)
        ).scalar_one_or_none()
        if key:
            print(f'  Existing test API key prefix: {key.key_prefix}...')
        print('  No changes made.')
    else:
        # Create admin user
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email='admin@deckforge.dev',
            name='Admin',
            is_active=True,
        )
        session.add(user)
        session.flush()

        # Generate a test API key
        raw_key = 'dk_test_' + secrets.token_hex(24)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:16]

        api_key = ApiKey(
            id=uuid.uuid4(),
            user_id=user_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name='Bootstrap test key',
            scopes=['read', 'generate'],
            tier='starter',
            is_active=True,
            is_test=True,
        )
        session.add(api_key)
        session.commit()

        print(f'  Admin user created: admin@deckforge.dev')
        print(f'  Test API key: {raw_key}')
        print(f'  (Save this key -- it cannot be retrieved later)')

print('  Seeding complete.')
"
echo ""

# Step 3: Verify database
echo "[3/3] Verifying database..."
python -c "
import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DECKFORGE_DATABASE_URL', 'postgresql+psycopg://deckforge:deckforge@localhost:5432/deckforge')

from sqlalchemy import create_engine, text
from src.deckforge.config import settings

sync_url = settings.DATABASE_URL
if 'aiosqlite' in sync_url:
    sync_url = sync_url.replace('sqlite+aiosqlite', 'sqlite')
elif 'asyncpg' in sync_url:
    sync_url = sync_url.replace('postgresql+asyncpg', 'postgresql+psycopg')

engine = create_engine(sync_url, echo=False)

with engine.connect() as conn:
    # Try PostgreSQL information_schema first, fall back to SQLite
    try:
        result = conn.execute(text(\"SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'\"))
        count = result.scalar()
    except Exception:
        # SQLite fallback
        result = conn.execute(text(\"SELECT count(*) FROM sqlite_master WHERE type = 'table'\"))
        count = result.scalar()

    print(f'  Tables: {count}')
    assert count and count > 0, 'No tables found -- migrations may have failed'

    # Verify key tables exist
    try:
        conn.execute(text('SELECT count(*) FROM users'))
        conn.execute(text('SELECT count(*) FROM api_keys'))
        print('  Core tables (users, api_keys) verified.')
    except Exception as e:
        print(f'  WARNING: Core table check failed: {e}')

print('  Database verification passed.')
"

echo ""
echo "=== Bootstrap Complete ==="
echo ""
echo "Next steps:"
echo "  curl http://localhost:8000/v1/health"
echo "  curl -H 'Authorization: Bearer dk_test_...' http://localhost:8000/v1/themes"
