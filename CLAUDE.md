# DeckForge

API-first presentation generation platform. 32 slide types, 24 chart types, 15 themes, native PPTX + Google Slides output, AI content generation, finance vertical with 9 specialized slide types.

## Tech Stack

- **API**: Python 3.12, FastAPI, Pydantic v2, uvicorn
- **Database**: PostgreSQL (prod) / SQLite (dev), SQLAlchemy 2.0 (async), Alembic migrations
- **Queue**: Redis + ARQ (async workers for content generation and rendering)
- **Storage**: MinIO (dev) / Cloudflare R2 (prod), S3-compatible via boto3
- **Rendering**: python-pptx (PPTX), google-api-python-client (Google Slides), Plotly + Kaleido (static chart PNGs)
- **SDK**: TypeScript, tsup build, vitest tests (in `sdk/` directory)
- **Billing**: Stripe (subscriptions, 3 tiers), x402 (USDC per-call for AI agents on Base L2)
- **Auth**: Unkey (prod) / DB-based SHA-256 key hashing (dev), API key prefixes `dk_test_` / `dk_live_`
- **Layout**: kiwisolver constraint solver, 12-column grid, Pillow text measurement
- **Themes**: 15 YAML definitions in `src/deckforge/themes/data/`
- **Content**: Model-agnostic LLM orchestration (Claude, OpenAI, Gemini, Ollama) with 4-stage pipeline
- **MCP**: FastMCP server with 6 tools for AI agent integration

## Project Structure

```
src/deckforge/
  config.py       # Pydantic Settings, DECKFORGE_ env prefix, all config fields
  main.py         # App entrypoint, lifespan, uvicorn runner
  ir/             # Pydantic IR models
    slides/       # 32 slide types (23 universal + 9 finance), discriminated on slide_type
    elements/     # Element types (title, text, metric, chart, image, table, etc.)
    charts/       # 24 chart types, discriminated on chart_type
  api/            # FastAPI routes + middleware
    routes/       # 15 route modules: render, generate, health, billing, onboarding, etc.
    middleware/    # Auth (Unkey/DB), rate limiting (Redis token bucket), credit check, x402
  db/             # Database layer
    base.py       # SQLAlchemy Base with naming conventions
    engine.py     # Async engine, session factory, get_db() dependency
    models/       # 8 models: User, ApiKey, Job, Deck, BatchJob, UsageRecord, PaymentEvent, WebhookRegistration
    repositories/ # Repository pattern, singleton instances, session-as-argument
  rendering/      # Output renderers
    pptx/         # PPTX renderer with ELEMENT_RENDERERS registry, transitions, Open XML
    gslides/      # Google Slides renderer with ELEMENT_BUILDERS dispatch, batchUpdate
    charts/       # Static chart renderers (Plotly -> PNG at 300 DPI), 24 chart types
    thumbnails/   # 3-tier fallback: LibreOffice -> pdf2image -> Pillow placeholder
  layout/         # Constraint-based layout
    solver.py     # kiwisolver constraint system
    grid.py       # 12-column grid
    patterns/     # PATTERN_REGISTRY: 9 layout patterns + GenericPattern fallback
    overflow.py   # Adaptive: font reduce (2pt steps) -> reflow -> slide split
  themes/         # Theme system
    data/         # 15 YAML themes (arctic-clean, corporate-blue, finance-pro, etc.)
    resolver.py   # 3-tier resolution: colors -> palette -> slide_masters
    brand_kit.py  # BrandKitMerger (protected keys: spacing, typography.scale)
  content/        # NL-to-IR pipeline
    pipeline.py   # 4-stage: intent -> outline -> expand -> refine
    intent.py     # Prompt classification
    outline.py    # Slide structure planning
    expand.py     # Content generation per slide
    refine.py     # QA and polish
  llm/            # LLM provider adapters
    router.py     # Provider selection + fallback chain
    adapters/     # Claude (tool_use), OpenAI (json_schema), Gemini (response_schema), Ollama (retry)
  charts/         # Chart recommender (data analysis -> chart type suggestion)
  finance/        # Financial formatting, conditional formatting, data ingestion
  qa/             # 5-pass QA pipeline, auto-fix engine (contrast, overflow, alignment), scorer
  billing/        # Stripe client, credit reservation/deduction, tier definitions, x402 config
  services/       # Business logic: DeckOperations, SlideTypeRegistry, CostEstimator
  workers/        # ARQ workers: ContentWorkerSettings, RenderWorkerSettings, task definitions
  mcp/            # MCP server: 6 tools (render, generate, themes, slide_types, estimate, preview)

sdk/              # TypeScript SDK (@deckforge/sdk)
  src/            # Immutable builder pattern, SSE streaming, full type coverage (32 slide + 24 chart types)
demos/            # 5 demo deck IRs (mckinsey-strategy, pe-deal-memo, startup-pitch, board-update, product-launch)
alembic/          # Database migrations (5 migrations)
scripts/          # bootstrap-db.sh (migrations + seed data)
```

## Key Commands

```bash
# Local development
docker compose up -d                    # Start all services (API, workers, PG, Redis, MinIO)
bash scripts/bootstrap-db.sh            # Initialize database (migrations + seed admin + test key)
pytest                                  # Run Python tests
cd sdk && npm test                      # Run SDK tests (vitest)

# Building
cd sdk && npm run build                 # Build TypeScript SDK (tsup)

# Code quality
ruff check src/                         # Lint Python code
ruff format src/                        # Format Python code
mypy src/                               # Type check

# Deployment
fly deploy                              # Deploy to Fly.io
fly secrets set KEY=value               # Set production secrets
fly ssh console -C "alembic upgrade head"  # Run migrations on production
```

## Architecture Patterns

- **IR Schema**: Pydantic discriminated unions on `slide_type`, `type`, and `chart_type` fields. 32 slide types in `ir/slides/`, elements in `ir/elements/`, 24 chart types in `ir/charts/`. Use `model_rebuild()` for forward references.

- **Renderer Registry**: `ELEMENT_RENDERERS` dict maps `element.type` string to renderer instance. Finance slides use `render_finance_slide()` with early return before element loop. Google Slides uses parallel `ELEMENT_BUILDERS` dispatch table.

- **Layout Patterns**: `PATTERN_REGISTRY` maps `SlideType` to pattern class. `GenericPattern` as fallback. Adaptive overflow cascade: font reduce (2pt steps, min 10/14pt) -> reflow -> slide split.

- **Repository Pattern**: Singleton instances, session-as-argument. Located in `db/repositories/`.

- **Config**: Pydantic Settings with `DECKFORGE_` prefix, loaded from `.env`. All fields in `config.py`.

- **Workers**: ARQ with Redis. `ContentWorkerSettings` and `RenderWorkerSettings`. Worker context dict pattern (`db_factory`, `redis`, `s3_client`, `s3_bucket`). Local imports in worker tasks to avoid circular dependencies.

- **Auth**: `AuthContext` dataclass with `.id` property. Dual auth: Unkey for production, DB-based SHA-256 for development. x402 payments skip rate limiting.

- **Billing**: Credit reservation before render, deduction on success, release on failure. Enterprise tier allows overage. `CostEstimator` uses `ceil(slides/10)` base + per-type surcharges.

- **Render Pipeline**: `render_pipeline()` shared sync function callable from API sync path and ARQ worker. Sync threshold: 10 slides. Returns `(bytes, QAReport)` tuple.

- **Content Pipeline**: 4-stage async: intent -> outline -> expand -> refine. Model-agnostic via LLM router with fallback chain. SSE streaming via Redis pub/sub.

## Coding Conventions

- **Python**: Type hints everywhere, Pydantic models for all schemas, async endpoints
- **Imports**: Local imports in worker tasks to avoid circular dependencies
- **Tests**: pytest with fixtures, `asyncio_mode = "auto"`, testpaths `tests/`
- **FastAPI**: Annotated dependency injection (`DbSession`, `RedisClient`, `CurrentApiKey`, `RateLimited`)
- **Error handling**: `HTTPException` with descriptive messages, 422 for validation errors
- **Config**: All settings via `DECKFORGE_` environment variables, never hardcoded
- **Models**: SQLAlchemy 2.0 `mapped_column` style, UUID primary keys via `uuid.uuid4`
- **Line length**: 100 characters (ruff configured)
- **Target**: Python 3.12+

## Important Files

- `src/deckforge/config.py` -- All environment variables and defaults
- `src/deckforge/api/app.py` -- Route registration (15 routers under `/v1`)
- `src/deckforge/ir/slides/universal.py` -- 23 universal slide type definitions
- `src/deckforge/ir/slides/finance.py` -- 9 finance slide type definitions
- `src/deckforge/ir/charts/types.py` -- 24 chart type definitions with `ChartUnion`
- `src/deckforge/rendering/pptx/` -- PPTX renderer with element registry
- `src/deckforge/layout/patterns/` -- Layout pattern registry
- `src/deckforge/themes/data/` -- 15 YAML theme definitions
- `src/deckforge/billing/tiers.py` -- Tier definitions (Starter/Pro/Enterprise)
- `docker-compose.yml` -- 6 services for local development
- `fly.toml` -- Fly.io deployment configuration
- `Dockerfile` -- Multi-stage build (builder + runtime with Chromium)
