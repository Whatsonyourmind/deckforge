# Phase 1: Foundation + IR Schema - Research

**Researched:** 2026-03-26
**Domain:** FastAPI project scaffolding, Pydantic v2 IR schema design, async infrastructure (ARQ + Redis + PostgreSQL), Docker Compose orchestration
**Confidence:** HIGH

## Summary

Phase 1 establishes every foundational piece that all eight phases depend on. The core challenge is designing a Pydantic v2 discriminated union schema for 32 slide types and multiple element types that validates efficiently, generates clean OpenAPI 3.1 docs, and remains extensible. The infrastructure challenge is wiring together FastAPI + ARQ workers + Redis + PostgreSQL + MinIO in Docker Compose with async throughout.

The stack choices are locked by prior research (STACK.md): FastAPI, Pydantic v2, SQLAlchemy 2.0 async with psycopg3, ARQ + Redis, MinIO for local S3-compatible storage. This research focuses on _how_ to implement these correctly -- the patterns, pitfalls, and code structures that make Phase 1 robust.

**Primary recommendation:** Build the IR schema first as the centerpiece, then wrap infrastructure around it. Use discriminated unions with a `slide_type` Literal field for slides and a `type` Literal field for elements. Organize models in per-category modules (universal slides, finance slides, text elements, data elements, etc.) and compose them into a single `Annotated[Union[...], Field(discriminator='...')]` type alias. This approach scales to 32+ types without performance degradation and generates correct OpenAPI discriminator metadata.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| IR-01 | IR schema defines all 32 slide types as Pydantic discriminated unions | Pydantic v2 discriminated union patterns, Literal-based discriminator, per-module file organization |
| IR-02 | IR schema defines all element types (text, data, visual, layout) with typed payloads | Nested discriminated union pattern (slide_type -> element type), Annotated type aliases |
| IR-03 | IR schema defines all chart subtypes with data models | Chart subtype discriminated union with `chart_type` Literal field |
| IR-04 | IR schema validates input and returns descriptive errors for malformed payloads | Pydantic v2 validation error reduction via discriminated unions, custom validators |
| IR-05 | IR supports generation_options (target_slide_count, density, chart_style, quality_target) | Pydantic BaseModel with enum fields and Optional ranges |
| IR-06 | IR supports metadata (title, purpose, audience, confidentiality, language) | Pydantic BaseModel with enum fields for purpose/audience/confidentiality |
| INFRA-01 | Docker Compose for local development (API + workers + Redis + PostgreSQL + MinIO) | Docker Compose multi-service pattern with healthchecks and depends_on |
| INFRA-02 | Dockerfile with bundled TrueType fonts for headless text measurement | python:3.12-slim base + fonts-liberation + Google Fonts bundling |
| INFRA-03 | PostgreSQL database with SQLAlchemy models (users, api_keys, decks, usage_events) | SQLAlchemy 2.0 async with Mapped annotations, psycopg3 driver, async session factory |
| INFRA-04 | Alembic migrations | Alembic async template with psycopg3, naming conventions for autogenerate |
| INFRA-05 | Railway/Fly.io deployment configuration for MVP launch | Deferred to end of phase -- Dockerfile is the deployment artifact |
| API-08 | GET /v1/health returns API health status | FastAPI route with Redis/PostgreSQL connectivity checks |
| API-09 | API key authentication (dk_live_/dk_test_ format) with scoped permissions | FastAPI Depends + APIKeyHeader, database lookup, scope validation |
| API-10 | Rate limiting per API key per tier (10/60/custom req/min) | Redis Lua script atomic token bucket, per-key hash, middleware pattern |
| API-11 | OpenAPI 3.1 spec auto-generated from Pydantic models | FastAPI native OpenAPI 3.1 generation with discriminated union support |
| API-14 | Idempotent operations via client-provided request_id | Database unique constraint on request_id, check-before-create pattern |
| WORKER-01 | ARQ + Redis task queue for content generation and rendering jobs | ARQ WorkerSettings, async task functions, Redis pool creation |
| WORKER-02 | Separate content worker pool (I/O-bound) and render worker pool (CPU-bound) | ARQ multiple queue_name pattern, separate WorkerSettings classes |
| WORKER-03 | S3/R2 file storage for generated presentations | boto3 with MinIO endpoint_url for local dev, s3v4 signature |
| WORKER-04 | Webhook delivery on job completion | httpx async POST in worker after_job_end hook |
| WORKER-05 | Job status tracking with progress events | Redis pub/sub for progress, ARQ job.status() and job.info() |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | >=0.135.2 | HTTP API framework | Native OpenAPI 3.1, Pydantic v2 integration, async-first |
| Pydantic | >=2.12 | IR schema validation + serialization | Rust-based validation core, discriminated union support, 5-50x faster than v1 |
| Uvicorn | >=0.42.0 | ASGI server | Standard FastAPI production server |
| SQLAlchemy | >=2.0.48 | Async ORM | Mapped annotations, async engine, psycopg3 native support |
| Alembic | >=1.18.4 | Database migrations | Auto-generates from model diffs, async template available |
| psycopg | >=3.2 | PostgreSQL driver | Async-native, single driver for sync+async, first-class SQLAlchemy 2.0 support |
| ARQ | 0.27.0 | Async task queue | Native asyncio, Redis-backed, lightweight, matches FastAPI async model |
| redis (python) | >=7.1.1 | Redis client | Async support (merged aioredis), used for ARQ + rate limiting + pub/sub |
| boto3 | >=1.36 | S3-compatible storage | MinIO for local dev, R2/S3 for production, universal API |
| httpx | >=0.28 | HTTP client | Async HTTP client for webhook delivery and testing |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic-settings | >=2.6 | Environment config | Loading .env files, settings validation |
| python-multipart | latest | File uploads | Multipart form data support in FastAPI |
| Pillow | >=12.1.1 | Font/image processing | Text measurement with ImageFont.truetype() in Docker |

### Dev Dependencies

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | >=8.3 | Test framework | All tests |
| pytest-asyncio | >=0.24 | Async test support | Testing async routes and workers |
| httpx | >=0.28 | Test client | AsyncClient for FastAPI integration tests |
| fakeredis | >=2.25 | Redis mock | Unit tests without running Redis |
| ruff | >=0.9 | Linting + formatting | Pre-commit, CI |
| mypy | >=1.14 | Type checking | Critical for IR schema correctness |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| psycopg3 | asyncpg | asyncpg is async-only; psycopg3 does both sync+async from one driver |
| ARQ | Celery | Celery is sync-first, process-based; ARQ is async-native, lighter |
| ARQ | Taskiq | Taskiq is pre-1.0 (v0.12); ARQ is stable. Good fallback if ARQ abandoned. |
| pydantic-settings | python-dotenv | pydantic-settings validates env vars with Pydantic models |
| Custom rate limiter | slowapi | slowapi uses fixed window; custom Lua token bucket is more precise per-key |

**Installation:**
```bash
pip install "fastapi>=0.135.2" "uvicorn[standard]>=0.42.0" "pydantic>=2.12" \
  "sqlalchemy[asyncio]>=2.0.48" "alembic>=1.18.4" "psycopg[binary]>=3.2" \
  "arq>=0.27.0" "redis>=7.1.1" "boto3>=1.36" "httpx>=0.28" \
  "pydantic-settings>=2.6" "python-multipart" "Pillow>=12.1.1"
```

## Architecture Patterns

### Recommended Project Structure

```
SlideMaker/
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── alembic.ini
├── alembic/
│   ├── env.py                    # Async env.py template
│   └── versions/                 # Migration files
├── src/
│   └── deckforge/
│       ├── __init__.py
│       ├── config.py             # Pydantic Settings
│       ├── main.py               # FastAPI app factory, lifespan
│       ├── api/
│       │   ├── __init__.py
│       │   ├── app.py            # create_app() factory
│       │   ├── deps.py           # Dependency injection (db session, auth, redis)
│       │   ├── middleware/
│       │   │   ├── __init__.py
│       │   │   ├── auth.py       # API key authentication
│       │   │   └── rate_limit.py # Redis token bucket rate limiter
│       │   ├── routes/
│       │   │   ├── __init__.py
│       │   │   ├── health.py     # GET /v1/health
│       │   │   ├── render.py     # POST /v1/render (stub - echoes IR)
│       │   │   └── jobs.py       # Job status + SSE events
│       │   └── schemas/
│       │       ├── __init__.py
│       │       ├── responses.py  # API response models
│       │       └── errors.py     # Error response models
│       ├── ir/
│       │   ├── __init__.py       # Re-exports: Presentation, Slide, Element
│       │   ├── presentation.py   # Presentation top-level model
│       │   ├── metadata.py       # PresentationMetadata, GenerationOptions
│       │   ├── slides/
│       │   │   ├── __init__.py   # SlideUnion type alias (all 32)
│       │   │   ├── base.py       # BaseSlide with common fields
│       │   │   ├── universal.py  # 23 universal slide models
│       │   │   └── finance.py    # 9 finance slide models
│       │   ├── elements/
│       │   │   ├── __init__.py   # ElementUnion type alias (all types)
│       │   │   ├── base.py       # BaseElement with common fields
│       │   │   ├── text.py       # heading, body_text, bullet_list, etc.
│       │   │   ├── data.py       # table, chart, kpi_card, etc.
│       │   │   ├── visual.py     # image, icon, shape, etc.
│       │   │   └── layout.py     # container, column, row, grid_cell
│       │   ├── charts/
│       │   │   ├── __init__.py   # ChartUnion type alias
│       │   │   └── types.py      # All chart subtype models
│       │   ├── enums.py          # SlideType, ElementType, ChartType enums
│       │   ├── brand_kit.py      # BrandKit model
│       │   └── validators.py     # Cross-field validators
│       ├── db/
│       │   ├── __init__.py
│       │   ├── base.py           # Base class with naming conventions
│       │   ├── engine.py         # Async engine + session factory
│       │   ├── models/
│       │   │   ├── __init__.py
│       │   │   ├── user.py       # User model
│       │   │   ├── api_key.py    # ApiKey model with scopes
│       │   │   ├── deck.py       # Deck model (IR stored as JSONB)
│       │   │   └── job.py        # Job model for tracking
│       │   └── repositories/
│       │       ├── __init__.py
│       │       ├── api_key.py    # ApiKey CRUD
│       │       ├── deck.py       # Deck CRUD
│       │       └── job.py        # Job CRUD
│       └── workers/
│           ├── __init__.py
│           ├── settings.py       # WorkerSettings classes (content + render queues)
│           ├── tasks.py          # Task function definitions
│           ├── storage.py        # S3/MinIO upload/download helpers
│           └── webhooks.py       # Webhook delivery
├── tests/
│   ├── conftest.py               # Shared fixtures (async client, db session, redis)
│   ├── unit/
│   │   ├── test_ir_schema.py     # IR validation tests
│   │   ├── test_ir_slides.py     # Per-slide-type validation
│   │   ├── test_ir_elements.py   # Element validation
│   │   └── test_rate_limiter.py  # Token bucket logic
│   └── integration/
│       ├── test_health.py        # Health endpoint
│       ├── test_auth.py          # API key auth flow
│       ├── test_render.py        # IR submission + validation
│       └── test_workers.py       # Job enqueueing + status
└── scripts/
    ├── seed_api_keys.py          # Create test API keys
    └── seed_db.py                # Development seed data
```

### Pattern 1: Pydantic v2 Discriminated Union for IR Slides

**What:** Each slide type is a separate Pydantic model with a `slide_type` Literal field. All models are composed into a single discriminated union type alias.

**When to use:** Always for the slide type system. This is the core IR pattern.

**Why:** Pydantic v2's discriminated unions are implemented in Rust and route validation directly to the correct model based on the discriminator value. For 32 types, this avoids trying all 32 models sequentially (which regular unions do). It also generates correct OpenAPI `discriminator` metadata.

**Example:**
```python
# src/deckforge/ir/slides/base.py
from pydantic import BaseModel, Field
from typing import Literal

class BaseSlide(BaseModel):
    """Common fields for all slide types."""
    layout_hint: LayoutHint | None = None
    transition: Transition = Transition.NONE
    speaker_notes: str | None = None
    elements: list[ElementUnion] = Field(default_factory=list)

# src/deckforge/ir/slides/universal.py
class TitleSlide(BaseSlide):
    slide_type: Literal["title_slide"] = "title_slide"
    # title_slide-specific fields can go here

class AgendaSlide(BaseSlide):
    slide_type: Literal["agenda"] = "agenda"

class BulletPointsSlide(BaseSlide):
    slide_type: Literal["bullet_points"] = "bullet_points"

# ... all 23 universal types

# src/deckforge/ir/slides/finance.py
class DcfSummarySlide(BaseSlide):
    slide_type: Literal["dcf_summary"] = "dcf_summary"

class CompTableSlide(BaseSlide):
    slide_type: Literal["comp_table"] = "comp_table"

# ... all 9 finance types

# src/deckforge/ir/slides/__init__.py
from typing import Annotated, Union
from pydantic import Field

SlideUnion = Annotated[
    Union[
        TitleSlide, AgendaSlide, SectionDividerSlide, KeyMessageSlide,
        BulletPointsSlide, TwoColumnTextSlide, ComparisonSlide,
        TimelineSlide, ProcessFlowSlide, OrgChartSlide, TeamSlide,
        QuoteSlide, ImageWithCaptionSlide, IconGridSlide,
        StatsCalloutSlide, TableSlide, ChartSlide, MatrixSlide,
        FunnelSlide, MapSlide, ThankYouSlide, AppendixSlide, QAndASlide,
        # Finance
        DcfSummarySlide, CompTableSlide, WaterfallChartSlide,
        DealOverviewSlide, ReturnsAnalysisSlide, CapitalStructureSlide,
        MarketLandscapeSlide, RiskMatrixSlide, InvestmentThesisSlide,
    ],
    Field(discriminator="slide_type"),
]
```

**Source:** [Pydantic Unions docs](https://docs.pydantic.dev/latest/concepts/unions/)

### Pattern 2: Nested Discriminated Union for Elements

**What:** Elements have a `type` discriminator with four categories (text, data, visual, layout), each containing subtypes.

**When to use:** For the element type hierarchy within slides.

**Example:**
```python
# src/deckforge/ir/elements/text.py
class HeadingElement(BaseElement):
    type: Literal["heading"] = "heading"
    content: HeadingContent  # text, level (h1/h2/h3)

class BulletListElement(BaseElement):
    type: Literal["bullet_list"] = "bullet_list"
    content: BulletListContent  # items, style

# src/deckforge/ir/elements/__init__.py
ElementUnion = Annotated[
    Union[
        HeadingElement, SubheadingElement, BodyTextElement,
        BulletListElement, NumberedListElement, CalloutBoxElement,
        PullQuoteElement, FootnoteElement, LabelElement,
        # Data
        TableElement, ChartElement, KpiCardElement,
        MetricGroupElement, ProgressBarElement, GaugeElement, SparklineElement,
        # Visual
        ImageElement, IconElement, ShapeElement,
        DividerElement, SpacerElement, LogoElement, BackgroundElement,
        # Layout
        ContainerElement, ColumnElement, RowElement, GridCellElement,
    ],
    Field(discriminator="type"),
]
```

### Pattern 3: Async Database Session with Dependency Injection

**What:** SQLAlchemy async engine + session factory injected into FastAPI routes via Depends.

**When to use:** All database operations.

**Example:**
```python
# src/deckforge/db/engine.py
from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine
)

engine = create_async_engine(
    settings.DATABASE_URL,  # postgresql+psycopg://user:pass@host/db
    echo=settings.DEBUG,
)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session

# src/deckforge/api/deps.py
from fastapi import Depends
from typing import Annotated

DbSession = Annotated[AsyncSession, Depends(get_db)]
```

**Source:** [FastAPI + Async SQLAlchemy 2 Guide](https://berkkaraal.com/blog/2024/09/19/setup-fastapi-project-with-async-sqlalchemy-2-alembic-postgresql-and-docker/)

### Pattern 4: ARQ Dual Worker Pools

**What:** Separate ARQ worker configurations for content (I/O-bound) and render (CPU-bound) tasks, using different queue names.

**When to use:** Worker infrastructure setup.

**Example:**
```python
# src/deckforge/workers/settings.py
from arq import cron
from arq.connections import RedisSettings

REDIS_SETTINGS = RedisSettings(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
)

class ContentWorkerSettings:
    """I/O-bound worker pool for LLM calls."""
    functions = [generate_content]
    queue_name = "arq:content"
    max_jobs = 20  # High concurrency for I/O-bound
    job_timeout = 120
    redis_settings = REDIS_SETTINGS
    on_startup = worker_startup
    on_shutdown = worker_shutdown

class RenderWorkerSettings:
    """CPU-bound worker pool for PPTX rendering."""
    functions = [render_presentation, upload_to_storage]
    queue_name = "arq:render"
    max_jobs = 4   # Lower concurrency for CPU-bound
    job_timeout = 60
    redis_settings = REDIS_SETTINGS
    on_startup = worker_startup
    on_shutdown = worker_shutdown

# Enqueue to specific queue:
await redis.enqueue_job("render_presentation", ir_data, _queue_name="arq:render")
await redis.enqueue_job("generate_content", prompt, _queue_name="arq:content")
```

**Source:** [ARQ docs](https://arq-docs.helpmanual.io/), [ARQ issue #186](https://github.com/samuelcolvin/arq/issues/186)

### Pattern 5: API Key Authentication via Dependency

**What:** Custom API key validation using FastAPI's APIKeyHeader security scheme with database lookup.

**When to use:** All protected endpoints.

**Example:**
```python
# src/deckforge/api/middleware/auth.py
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
import hashlib
import secrets

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(
    db: DbSession,
    api_key: str | None = Security(API_KEY_HEADER),
) -> ApiKeyModel:
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    # Validate prefix format
    if not (api_key.startswith("dk_live_") or api_key.startswith("dk_test_")):
        raise HTTPException(status_code=401, detail="Invalid API key format")

    # Hash the key for database lookup (store hashed, never plaintext)
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    db_key = await api_key_repo.get_by_hash(db, key_hash)

    if not db_key or not db_key.is_active:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return db_key

# Usage as dependency
CurrentApiKey = Annotated[ApiKeyModel, Depends(get_api_key)]
```

### Pattern 6: Redis Token Bucket Rate Limiter

**What:** Atomic token bucket rate limiting using Redis Lua script, keyed per API key.

**When to use:** Rate limiting middleware.

**Example:**
```python
# src/deckforge/api/middleware/rate_limit.py
import time

TOKEN_BUCKET_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local max_tokens = tonumber(ARGV[2])
local refill_rate = tonumber(ARGV[3])

local state = redis.call('HGETALL', key)
local tokens = max_tokens
local last_refill = now

if #state > 0 then
    tokens = tonumber(state[2])
    last_refill = tonumber(state[4])
end

local elapsed = math.max(0, now - last_refill)
local refilled = math.min(max_tokens, tokens + (elapsed * refill_rate))

local allowed = 0
local remaining = refilled
if refilled >= 1 then
    allowed = 1
    remaining = refilled - 1
end

redis.call('HSET', key, 'tokens', remaining, 'last_refill', now)
redis.call('EXPIRE', key, math.ceil(max_tokens / refill_rate) + 1)

return {allowed, math.ceil(remaining), math.ceil((1 / refill_rate) * 1000)}
"""

TIER_LIMITS = {
    "starter": {"max_tokens": 10, "refill_rate": 10 / 60},   # 10/min
    "pro":     {"max_tokens": 60, "refill_rate": 60 / 60},    # 60/min
}

async def check_rate_limit(redis_client, api_key_id: str, tier: str) -> tuple[bool, int, int]:
    """Returns (allowed, remaining, retry_after_ms)."""
    limits = TIER_LIMITS[tier]
    result = await redis_client.eval(
        TOKEN_BUCKET_SCRIPT,
        keys=[f"rate_limit:{api_key_id}"],
        args=[time.time(), limits["max_tokens"], limits["refill_rate"]],
    )
    return bool(result[0]), result[1], result[2]
```

**Source:** [Redis Rate Limiting Tutorial](https://redis.io/tutorials/howtos/ratelimiting/)

### Anti-Patterns to Avoid

- **Flat file with 32 slide classes:** Putting all 32 slide type models in a single file creates an unreadable 1000+ line file. Split into `slides/universal.py` and `slides/finance.py`.
- **Regular Union instead of discriminated:** Without `Field(discriminator=...)`, Pydantic tries each model left-to-right, producing cascading validation errors for 32 types. Always use discriminated unions.
- **Storing raw API keys in the database:** Hash with SHA-256 before storage. Only show the full key once at creation time.
- **Sync database calls in async routes:** All database operations must use `await` with async session. A single sync call blocks the event loop.
- **ARQ workers sharing the FastAPI process:** Workers MUST run in separate processes. Never run ARQ worker inside the FastAPI app process -- they compete for the event loop.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Token bucket rate limiting | In-memory dict with timestamps | Redis Lua script | Must work across multiple API instances; Redis is atomic |
| Task queue | asyncio.Queue + background tasks | ARQ + Redis | Need persistence, retries, separate worker processes, job status |
| Database migrations | Manual SQL scripts | Alembic autogenerate | Model drift is inevitable; autogenerate catches schema mismatches |
| OpenAPI spec | Hand-written openapi.yaml | FastAPI auto-generation from Pydantic models | 32 slide types = hundreds of schema objects; manual is unmaintainable |
| S3 presigned URLs | Custom URL signing | boto3 generate_presigned_url() | S3v4 signing is complex; boto3 handles it correctly |
| API key generation | Random strings | `secrets.token_urlsafe(32)` with prefix | Cryptographically secure, correct entropy |
| Environment config | os.getenv() calls | pydantic-settings BaseSettings | Type validation, .env file loading, required field checking |

**Key insight:** Phase 1 has many "boring infrastructure" tasks that should use standard solutions. The only truly custom code is the IR schema design and the rate limiter Lua script. Everything else is wiring.

## Common Pitfalls

### Pitfall 1: OpenAPI Schema Bloat with 32 Slide Types

**What goes wrong:** The auto-generated OpenAPI JSON becomes very large (500KB+) with 32 discriminated slide types, each containing nested element unions. The `/docs` page loads slowly or times out.

**Why it happens:** Each slide type generates a separate JSON Schema definition. Each element type within each slide adds more. Discriminated unions generate `oneOf` with `discriminator` mappings for all variants.

**How to avoid:**
- Use `model_config = ConfigDict(json_schema_extra=...)` sparingly -- do not add examples to every model
- Lazy-load the OpenAPI schema (FastAPI caches it after first request)
- Consider a separate `/v1/ir-reference` endpoint with detailed IR docs, keeping the main OpenAPI schema focused on API endpoints
- Test OpenAPI generation early -- add a test that calls `app.openapi()` and verifies it generates without error

**Warning signs:** `/docs` takes >3 seconds to load, SDK generation tools time out.

### Pitfall 2: Circular Imports in IR Schema

**What goes wrong:** Slide models reference ElementUnion, element models might reference sub-elements, creating circular import chains.

**Why it happens:** The IR is deeply nested: Presentation -> Slides -> Elements -> (nested elements in containers).

**How to avoid:**
- Use `from __future__ import annotations` in all IR modules (defers type evaluation)
- Define forward references as strings: `elements: list["ElementUnion"]`
- Call `model_rebuild()` on the top-level Presentation model after all imports
- Keep the import chain one-directional: `presentation.py` imports from `slides/`, which imports from `elements/`, which imports from `enums.py`

**Warning signs:** ImportError at startup, mypy complaints about undefined types.

### Pitfall 3: Alembic Async Configuration Mistakes

**What goes wrong:** Running `alembic revision --autogenerate` fails with "no changes detected" or creates empty migrations.

**Why it happens:** The `env.py` does not import all model modules, so Alembic cannot see the SQLAlchemy models. Or the `target_metadata` is not set to `Base.metadata`.

**How to avoid:**
- In `alembic/env.py`, explicitly import ALL model modules:
  ```python
  from src.deckforge.db.models import user, api_key, deck, job  # noqa: F401
  from src.deckforge.db.base import Base
  target_metadata = Base.metadata
  ```
- Set naming conventions on the Base MetaData for consistent constraint names
- Use `alembic init -t async alembic` to generate the async template
- Set `sqlalchemy.url` in alembic.ini to the sync variant of the URL (psycopg3 supports both)

**Warning signs:** Empty migration files, `autogenerate` missing columns or tables.

### Pitfall 4: MinIO Presigned URL Signature Mismatch

**What goes wrong:** Presigned URLs generated by boto3 return 403 Forbidden when accessed from a client.

**Why it happens:** MinIO uses S3v4 signatures where the host is included. If the presigned URL is generated with `localhost:9000` but accessed via `minio:9000` (Docker internal hostname), the signatures do not match.

**How to avoid:**
- Always use `config=Config(signature_version="s3v4")` when creating the boto3 client
- Set `endpoint_url` to the externally-accessible URL (not Docker internal hostname)
- For Docker Compose, expose MinIO on a fixed port and generate presigned URLs with `localhost:{port}`

**Warning signs:** 403 errors only on presigned URL access, direct boto3 operations work fine.

### Pitfall 5: ARQ Job ID Collisions and Deduplication

**What goes wrong:** Submitting the same request_id twice creates unexpected behavior -- the second job silently returns None (ARQ's deduplication) instead of returning the existing job result.

**Why it happens:** ARQ uses `_job_id` for deduplication. If you pass request_id as _job_id, ARQ rejects the second enqueue. But the API caller does not know whether the original job completed or is still running.

**How to avoid:**
- Check job status in the database BEFORE enqueueing. If a job with that request_id already exists, return its status.
- Use ARQ's `_job_id` as an internal identifier, not the user-facing request_id.
- Store the mapping between request_id and ARQ job_id in PostgreSQL.

**Warning signs:** `enqueue_job()` returning None, idempotent requests not returning cached results.

### Pitfall 6: Font Measurement Discrepancy Between Dev and Docker

**What goes wrong:** Text that fits perfectly in development overflows in production Docker because different fonts are available.

**Why it happens:** macOS/Windows have system fonts (Arial, Helvetica, Calibri) that are not in the Docker image. Pillow falls back to a default bitmap font with different metrics.

**How to avoid:**
- Bundle all theme fonts in the Docker image (Google Fonts are free: Liberation Sans, Open Sans, Montserrat, etc.)
- Use `Pillow.ImageFont.truetype("/path/to/font.ttf", size)` with absolute paths to bundled fonts
- Add a startup check that verifies all required fonts are loadable
- Include `fonts-liberation` package in Dockerfile for basic coverage

**Warning signs:** Text overflow in Docker but not local dev, Pillow fallback font warnings in logs.

## Code Examples

### SQLAlchemy Model with JSONB for IR Storage

```python
# src/deckforge/db/models/deck.py
from sqlalchemy import String, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
import datetime

from src.deckforge.db.base import Base

class Deck(Base):
    __tablename__ = "decks"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    request_id: Mapped[str | None] = mapped_column(
        String(64), unique=True, index=True
    )
    api_key_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("api_keys.id")
    )
    ir_snapshot: Mapped[dict] = mapped_column(JSONB)  # Full IR stored
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, processing, complete, failed
    file_url: Mapped[str | None] = mapped_column(String(512))
    quality_score: Mapped[int | None]
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
```

### API Key Model with Hash and Scopes

```python
# src/deckforge/db/models/api_key.py
class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    key_prefix: Mapped[str] = mapped_column(String(16))  # "dk_live_abc..." for display
    name: Mapped[str] = mapped_column(String(100))
    scopes: Mapped[list[str]] = mapped_column(JSONB, default=["read", "generate"])
    tier: Mapped[str] = mapped_column(String(20), default="starter")
    is_active: Mapped[bool] = mapped_column(default=True)
    is_test: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_used_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
```

### Alembic Async env.py Setup

```python
# alembic/env.py
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from src.deckforge.db.base import Base
# Import ALL models so Alembic sees them
from src.deckforge.db.models import user, api_key, deck, job  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata,
        literal_binds=True, dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Source:** [Alembic async template](https://github.com/sqlalchemy/alembic/blob/main/alembic/templates/async/env.py)

### Docker Compose for Full Local Stack

```yaml
# docker-compose.yml
services:
  api:
    build: .
    command: >
      bash -c "alembic upgrade head &&
               uvicorn src.deckforge.main:app --host 0.0.0.0 --port 8000 --reload"
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    env_file: .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_started

  content-worker:
    build: .
    command: arq src.deckforge.workers.settings.ContentWorkerSettings
    env_file: .env
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy

  render-worker:
    build: .
    command: arq src.deckforge.workers.settings.RenderWorkerSettings
    env_file: .env
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: deckforge
      POSTGRES_PASSWORD: deckforge
      POSTGRES_DB: deckforge
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U deckforge"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - miniodata:/data

volumes:
  pgdata:
  miniodata:
```

### Dockerfile with Font Bundling

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# System dependencies: fonts for text measurement, pg client for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-liberation \
    fonts-dejavu-core \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (Docker layer caching)
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

# Copy application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.deckforge.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### FastAPI App Factory with Lifespan

```python
# src/deckforge/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from redis.asyncio import Redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.redis = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True,
    )
    # Verify connections
    await app.state.redis.ping()
    yield
    # Shutdown
    await app.state.redis.aclose()

def create_app() -> FastAPI:
    app = FastAPI(
        title="DeckForge API",
        version="0.1.0",
        lifespan=lifespan,
    )
    # Include routers
    app.include_router(health_router, prefix="/v1", tags=["health"])
    app.include_router(render_router, prefix="/v1", tags=["render"])
    app.include_router(jobs_router, prefix="/v1", tags=["jobs"])
    return app

app = create_app()
```

### Health Endpoint with Dependency Checks

```python
# src/deckforge/api/routes/health.py
from fastapi import APIRouter, Request
from sqlalchemy import text

router = APIRouter()

@router.get("/health")
async def health(request: Request, db: DbSession):
    checks = {}
    # PostgreSQL
    try:
        await db.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception:
        checks["postgres"] = "error"

    # Redis
    try:
        await request.app.state.redis.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"

    all_ok = all(v == "ok" for v in checks.values())
    return {
        "status": "healthy" if all_ok else "degraded",
        "checks": checks,
        "version": "0.1.0",
    }
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pydantic v1 unions (try all) | Pydantic v2 discriminated unions (direct routing) | 2023 (v2.0) | 5-50x faster validation for large unions |
| asyncpg + psycopg2 (two drivers) | psycopg3 (one driver, sync+async) | 2024 | Single driver simplifies config and testing |
| Celery + RabbitMQ | ARQ + Redis | 2023-2024 (async ecosystem maturity) | Async-native, 10x less memory for I/O-bound tasks |
| SQLAlchemy 1.x declarative | SQLAlchemy 2.0 Mapped annotations | 2023 (v2.0) | Type-safe, IDE completion, cleaner syntax |
| Alembic sync-only | Alembic async template | 2023 | Native async engine support in migrations |
| Manual OpenAPI | FastAPI auto-gen OpenAPI 3.1 | 2024 (FastAPI 0.100+) | OpenAPI 3.1 with discriminator support from Pydantic v2 |

**Deprecated/outdated:**
- `aioredis`: Merged into `redis-py` 7.x. Do not install separately.
- `databases` package: Superseded by SQLAlchemy 2.0 async. Do not use.
- Pydantic v1 `schema_extra`: Replaced by `model_config = ConfigDict(json_schema_extra=...)` in v2.

## Open Questions

1. **psycopg3 connection URL format in Alembic**
   - What we know: psycopg3 uses `postgresql+psycopg://` for async and sync
   - What's unclear: Whether alembic.ini needs the sync URL or async URL when using the async template
   - Recommendation: Use `postgresql+psycopg://` (works for both). The async template wraps it with `async_engine_from_config`.

2. **ARQ job result storage duration**
   - What we know: ARQ stores results in Redis with configurable TTL (`keep_result` default 3600s)
   - What's unclear: Whether we should also persist results to PostgreSQL for long-term retrieval
   - Recommendation: Store job metadata + status in PostgreSQL; use ARQ results only for immediate job polling. This decouples job history from Redis memory.

3. **IR schema version field placement**
   - What we know: The IR will evolve and stored IR snapshots need version tracking
   - What's unclear: Whether `schema_version` goes in the Presentation model or as a wrapper
   - Recommendation: Add `schema_version: Literal["1.0"] = "1.0"` to the Presentation model. Future versions can use a discriminated union on schema_version.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest >=8.3 + pytest-asyncio >=0.24 |
| Config file | None -- Wave 0 creates pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `pytest tests/unit/ -x -q` |
| Full suite command | `pytest tests/ -x --tb=short` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| IR-01 | 32 slide types validate with discriminated union | unit | `pytest tests/unit/test_ir_slides.py -x` | Wave 0 |
| IR-02 | All element types validate with typed payloads | unit | `pytest tests/unit/test_ir_elements.py -x` | Wave 0 |
| IR-03 | All chart subtypes validate | unit | `pytest tests/unit/test_ir_charts.py -x` | Wave 0 |
| IR-04 | Invalid IR returns descriptive 422 errors | unit + integration | `pytest tests/unit/test_ir_validation.py tests/integration/test_render.py -x` | Wave 0 |
| IR-05 | generation_options validates correctly | unit | `pytest tests/unit/test_ir_schema.py::test_generation_options -x` | Wave 0 |
| IR-06 | metadata validates correctly | unit | `pytest tests/unit/test_ir_schema.py::test_metadata -x` | Wave 0 |
| INFRA-01 | Docker Compose brings up full stack | integration | `docker compose up -d && pytest tests/integration/test_health.py -x` | Wave 0 |
| INFRA-02 | Fonts available in Docker image | integration | `pytest tests/integration/test_fonts.py -x` | Wave 0 |
| INFRA-03 | SQLAlchemy models create tables | integration | `pytest tests/integration/test_db.py -x` | Wave 0 |
| INFRA-04 | Alembic migrations run cleanly | integration | `alembic upgrade head && alembic downgrade base && alembic upgrade head` | Wave 0 |
| INFRA-05 | Deployment config present | manual-only | Verify Dockerfile builds | N/A |
| API-08 | Health endpoint returns status | integration | `pytest tests/integration/test_health.py -x` | Wave 0 |
| API-09 | API key auth accepts/rejects correctly | integration | `pytest tests/integration/test_auth.py -x` | Wave 0 |
| API-10 | Rate limiting enforces per-key limits | unit + integration | `pytest tests/unit/test_rate_limiter.py tests/integration/test_rate_limit.py -x` | Wave 0 |
| API-11 | OpenAPI spec generates without error | unit | `pytest tests/unit/test_openapi.py -x` | Wave 0 |
| API-14 | Duplicate request_id returns same result | integration | `pytest tests/integration/test_idempotency.py -x` | Wave 0 |
| WORKER-01 | ARQ task enqueues and executes | integration | `pytest tests/integration/test_workers.py::test_enqueue -x` | Wave 0 |
| WORKER-02 | Separate worker pools process different queues | integration | `pytest tests/integration/test_workers.py::test_dual_pools -x` | Wave 0 |
| WORKER-03 | File uploads to MinIO and returns URL | integration | `pytest tests/integration/test_storage.py -x` | Wave 0 |
| WORKER-04 | Webhook fires on job completion | integration | `pytest tests/integration/test_webhooks.py -x` | Wave 0 |
| WORKER-05 | Job status trackable via API | integration | `pytest tests/integration/test_workers.py::test_job_status -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/unit/ -x -q` (unit tests only, fast)
- **Per wave merge:** `pytest tests/ -x --tb=short` (full suite)
- **Phase gate:** Full suite green + Docker Compose up + health check passing before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `pyproject.toml` -- project config with [tool.pytest.ini_options] asyncio_mode = "auto"
- [ ] `tests/conftest.py` -- shared fixtures: async client, db session override, fakeredis, test API key
- [ ] `tests/unit/test_ir_schema.py` -- Presentation, metadata, generation_options validation
- [ ] `tests/unit/test_ir_slides.py` -- all 32 slide types pass/fail validation
- [ ] `tests/unit/test_ir_elements.py` -- all element types pass/fail validation
- [ ] `tests/unit/test_ir_charts.py` -- chart subtype validation
- [ ] `tests/unit/test_ir_validation.py` -- malformed IR produces descriptive errors
- [ ] `tests/unit/test_rate_limiter.py` -- token bucket logic with fakeredis
- [ ] `tests/unit/test_openapi.py` -- OpenAPI schema generates without error
- [ ] `tests/integration/test_health.py` -- health endpoint with mocked services
- [ ] `tests/integration/test_auth.py` -- API key authentication flow
- [ ] `tests/integration/test_render.py` -- POST valid/invalid IR, check 200/422
- [ ] `tests/integration/test_workers.py` -- ARQ job lifecycle
- [ ] `tests/integration/test_storage.py` -- MinIO upload/download
- [ ] `tests/integration/test_idempotency.py` -- duplicate request_id handling
- [ ] Framework install: `pip install pytest pytest-asyncio httpx fakeredis` via pyproject.toml [dev] deps

## Sources

### Primary (HIGH confidence)

- [Pydantic Unions documentation](https://docs.pydantic.dev/latest/concepts/unions/) -- discriminated union patterns, Literal discriminators, callable discriminators, OpenAPI generation
- [ARQ v0.27.0 documentation](https://arq-docs.helpmanual.io/) -- worker setup, job enqueueing, health checks, retry, Redis settings
- [Alembic async template](https://github.com/sqlalchemy/alembic/blob/main/alembic/templates/async/env.py) -- official async env.py for SQLAlchemy 2.0
- [Redis Rate Limiting tutorial](https://redis.io/tutorials/howtos/ratelimiting/) -- token bucket Lua script, atomic operations
- [FastAPI deployment Docker](https://fastapi.tiangolo.com/deployment/docker/) -- Dockerfile patterns
- [boto3 presigned URLs](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-presigned-urls.html) -- S3v4 signing

### Secondary (MEDIUM confidence)

- [FastAPI + Async SQLAlchemy 2 guide](https://berkkaraal.com/blog/2024/09/19/setup-fastapi-project-with-async-sqlalchemy-2-alembic-postgresql-and-docker/) -- async engine setup, session factory, dependency injection
- [ARQ + SQLAlchemy async done right](https://wazaari.dev/blog/arq-sqlalchemy-done-right) -- worker database sessions with contextvars
- [FastAPI BackgroundTasks vs ARQ comparison](https://davidmuraya.com/blog/fastapi-background-tasks-arq-vs-built-in/) -- when to use ARQ over built-in
- [Token bucket rate limiting in FastAPI](https://www.freecodecamp.org/news/token-bucket-rate-limiting-fastapi) -- middleware pattern, 429 headers
- [FastAPI API key authentication](https://timberry.dev/fastapi-with-apikeys) -- APIKeyHeader pattern
- [Pydantic discriminated unions for experts](https://blog.dataengineerthings.org/pydantic-for-experts-discriminated-unions-in-pydantic-v2-2d9ca965b22f) -- advanced patterns
- [Pydantic nested discriminated unions OpenAPI issue #7491](https://github.com/pydantic/pydantic/issues/7491) -- known schema generation considerations

### Tertiary (LOW confidence)

- [ARQ multiple queues issue #186](https://github.com/samuelcolvin/arq/issues/186) -- separate worker pools pattern (community discussion, not official docs)
- [MinIO presigned URL signature issue](https://github.com/minio/minio/discussions/20662) -- S3v4 signature with host mismatch workaround

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries verified via PyPI with current versions, prior STACK.md research confirmed
- Architecture: HIGH -- patterns verified against official docs (Pydantic, FastAPI, ARQ, SQLAlchemy, Alembic)
- Pitfalls: HIGH -- multiple sources confirm OpenAPI bloat, circular import, and font bundling issues
- IR schema design: HIGH -- Pydantic discriminated union is the documented, recommended approach for tagged unions
- Rate limiting: MEDIUM -- Lua script pattern well-documented by Redis.io, but custom implementation needs testing
- ARQ dual pools: MEDIUM -- supported by ARQ architecture (queue_name parameter) but not explicitly documented as a pattern

**Research date:** 2026-03-26
**Valid until:** 2026-04-26 (stable libraries, 30-day window)
