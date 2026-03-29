---
phase: 01-foundation-ir-schema
plan: 02
subsystem: infra
tags: [docker, postgresql, sqlalchemy, alembic, pydantic-settings, redis, minio, repository-pattern]

# Dependency graph
requires: []
provides:
  - Docker Compose local dev stack (6 services with healthchecks)
  - Dockerfile with Python 3.12 and bundled TrueType fonts
  - SQLAlchemy async models for users, api_keys, decks, jobs
  - Async database engine and session factory
  - Alembic async migration configuration
  - Repository pattern for data access (ApiKey, Deck, Job)
  - Pydantic Settings centralized configuration
affects: [02-layout-engine, 03-pptx-rendering, 04-content-pipeline, 05-google-slides, 06-api-billing]

# Tech tracking
tech-stack:
  added: [pydantic-settings, sqlalchemy, alembic, psycopg3, aiosqlite]
  patterns: [repository-pattern, async-sessionmaker, declarative-base-naming-conventions, pydantic-settings-env-prefix]

key-files:
  created:
    - src/deckforge/config.py
    - src/deckforge/db/base.py
    - src/deckforge/db/engine.py
    - src/deckforge/db/models/user.py
    - src/deckforge/db/models/api_key.py
    - src/deckforge/db/models/deck.py
    - src/deckforge/db/models/job.py
    - src/deckforge/db/repositories/api_key.py
    - src/deckforge/db/repositories/deck.py
    - src/deckforge/db/repositories/job.py
    - Dockerfile
    - docker-compose.yml
    - alembic.ini
    - alembic/env.py
    - tests/integration/test_db.py
  modified:
    - pyproject.toml

key-decisions:
  - "Used sqlalchemy.JSON instead of postgresql.JSONB for cross-dialect compatibility (PostgreSQL auto-maps JSON to its native JSON type; JSONB indexing can be added via explicit migration)"
  - "Repository pattern with singleton instances for stateless data access"
  - "MetaData with naming conventions passed directly to Base class for Alembic deterministic constraint names"

patterns-established:
  - "Repository pattern: stateless classes with async methods taking session as first arg"
  - "Settings singleton: from deckforge.config import settings"
  - "Async session generator: get_db() for FastAPI dependency injection"
  - "Alembic async env.py pattern with NullPool for migrations"

requirements-completed: [INFRA-01, INFRA-02, INFRA-03, INFRA-04]

# Metrics
duration: 6min
completed: 2026-03-29
---

# Phase 1 Plan 2: Infrastructure & Database Summary

**Docker Compose dev stack with PostgreSQL/Redis/MinIO, 4 SQLAlchemy async models, Alembic migrations, and repository pattern with 11 passing integration tests**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-29T00:12:20Z
- **Completed:** 2026-03-29T00:19:07Z
- **Tasks:** 2
- **Files modified:** 26

## Accomplishments
- Full Docker Compose stack with 6 services (api, content-worker, render-worker, postgres, redis, minio) with healthchecks and dependency ordering
- Dockerfile with Python 3.12-slim base, Liberation and DejaVu font bundles for headless text measurement
- 4 SQLAlchemy ORM models (User, ApiKey, Deck, Job) with JSON columns, foreign keys, and naming conventions
- Async Alembic configuration importing all models for autogenerate
- 3 repository classes (ApiKeyRepository, DeckRepository, JobRepository) implementing create, get, update patterns
- 11 integration tests passing against in-memory SQLite: table creation, model CRUD, repository operations
- Pydantic Settings with DECKFORGE_ env prefix and .env file loading

## Task Commits

Each task was committed atomically:

1. **Task 1: Configuration, Dockerfile, Docker Compose, and database models** - `c6e99ab` (feat)
2. **Task 2: Alembic migrations, repository pattern, and integration tests** - `9764443` (feat)

## Files Created/Modified
- `src/deckforge/config.py` - Pydantic Settings with all environment variables
- `src/deckforge/db/base.py` - SQLAlchemy DeclarativeBase with Alembic naming conventions
- `src/deckforge/db/engine.py` - Async engine and session factory
- `src/deckforge/db/models/user.py` - User model (email, name, is_active)
- `src/deckforge/db/models/api_key.py` - ApiKey model (hash, prefix, scopes, tier)
- `src/deckforge/db/models/deck.py` - Deck model (IR snapshot, status, file_url, quality_score)
- `src/deckforge/db/models/job.py` - Job model (type, queue, status, progress, result)
- `src/deckforge/db/repositories/api_key.py` - ApiKey CRUD with get_by_hash
- `src/deckforge/db/repositories/deck.py` - Deck CRUD with get_by_request_id for idempotency
- `src/deckforge/db/repositories/job.py` - Job CRUD with get_active_jobs filter
- `Dockerfile` - Python 3.12-slim with fonts-liberation, fonts-dejavu-core, libpq-dev
- `docker-compose.yml` - 6 services: api, content-worker, render-worker, postgres, redis, minio
- `.env.example` - Documented environment variables
- `.gitignore` - Python, IDE, OS ignores plus .env
- `alembic.ini` - Async PostgreSQL URL, file template with date prefix
- `alembic/env.py` - Async Alembic config importing all models
- `alembic/script.py.mako` - Standard migration template
- `tests/integration/test_db.py` - 11 tests for models and repositories
- `pyproject.toml` - Added aiosqlite dev dependency

## Decisions Made
- Used `sqlalchemy.JSON` instead of `sqlalchemy.dialects.postgresql.JSONB` for cross-dialect test compatibility. PostgreSQL maps JSON columns to its native JSON type. JSONB-specific features (GIN indexing) can be added via explicit Alembic migrations when needed.
- Repository pattern uses stateless singleton instances -- no internal state, session passed as argument for testability and thread safety.
- Used `MetaData(naming_convention=...)` on the Base class rather than setting it on the class attribute post-hoc, fixing a SQLAlchemy initialization error.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed DeclarativeBase metadata initialization**
- **Found during:** Task 1 (Database models)
- **Issue:** `DeclarativeBase.metadata` is not accessible as a class attribute before the subclass is defined. `metadata = DeclarativeBase.metadata` raised AttributeError.
- **Fix:** Used `metadata = MetaData(naming_convention=NAMING_CONVENTION)` instead
- **Files modified:** `src/deckforge/db/base.py`
- **Verification:** All 4 models import without error
- **Committed in:** c6e99ab (Task 1 commit)

**2. [Rule 1 - Bug] Changed JSONB to JSON for cross-dialect compatibility**
- **Found during:** Task 2 (Integration tests)
- **Issue:** `sqlalchemy.dialects.postgresql.JSONB` cannot be compiled by the SQLite dialect, causing all tests to fail with `CompileError: can't render element of type JSONB`
- **Fix:** Replaced `JSONB` imports with `sqlalchemy.JSON` across api_key.py, deck.py, and job.py. JSON works on all dialects and PostgreSQL maps it appropriately.
- **Files modified:** `src/deckforge/db/models/api_key.py`, `src/deckforge/db/models/deck.py`, `src/deckforge/db/models/job.py`
- **Verification:** All 11 integration tests pass
- **Committed in:** 9764443 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes necessary for correctness. No scope creep. JSON type is functionally equivalent to JSONB for the application layer.

## Issues Encountered
None beyond the auto-fixed deviations.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Database models and repositories ready for API route handlers (Phase 3+)
- Docker Compose stack ready for local development (run `docker compose up`)
- Alembic configured for generating migrations from model changes
- Settings system ready for any module to import configuration
- Repository pattern established as the data access convention

## Self-Check: PASSED

All 18 created files verified present. Both task commits (c6e99ab, 9764443) verified in git history.

---
*Phase: 01-foundation-ir-schema*
*Completed: 2026-03-29*
