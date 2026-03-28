# Technology Stack

**Project:** DeckForge
**Researched:** 2026-03-26
**Overall Confidence:** HIGH

---

## Executive Summary

DeckForge's stack is Python-native for the backend (FastAPI + python-pptx + Google APIs) with a TypeScript SDK generated from the OpenAPI spec. The core rendering is built on python-pptx 1.0.2, the only production-grade open-source PPTX library in Python, and Google's official Slides/Sheets API clients. LLM orchestration uses LiteLLM for multi-model abstraction (with a critical supply chain caveat -- pin to a verified safe version). Async task processing uses ARQ with Redis, matching FastAPI's async-first design. Layout solving uses kiwisolver (Cassowary constraint solver). The stack is deliberately boring where boring is good (PostgreSQL, Redis, S3-compatible storage) and opinionated only where the domain demands it (constraint-based layout, multi-pass QA).

---

## Recommended Stack

### Python Runtime

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| Python | 3.12 | Runtime | Best balance of performance + ecosystem support. 3.13 has free-threaded mode but ecosystem support is still maturing. 3.12 is the safe production choice. | HIGH |

**Rationale:** Python 3.12 delivers significant performance improvements (up to 5% faster than 3.11), better error messages, and full compatibility with every library in this stack. Python 3.13's free-threaded mode (no-GIL) is experimental and several C-extension libraries (including lxml, used by python-pptx) have not fully tested against it. Stick with 3.12 for production stability.

---

### API Framework

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| FastAPI | >=0.135.2 | HTTP API framework | De facto standard for high-performance Python APIs. Native OpenAPI 3.1, Pydantic v2 integration, SSE support, async-first. 40% adoption increase in 2025. | HIGH |
| Uvicorn | >=0.42.0 | ASGI server | The standard ASGI server for FastAPI. Production-ready with HTTP/1.1 and WebSocket support. | HIGH |
| Pydantic | >=2.12 | Validation + serialization | Core of the IR schema system. Pydantic v2 is 5-50x faster than v1 with Rust-based validation core. 2.12 adds `exclude_if` and ValidateAs. | HIGH |
| sse-starlette | >=3.3.3 | Server-Sent Events | Production-ready SSE for streaming generation progress. W3C spec compliant, automatic disconnect detection, graceful shutdown. FastAPI 0.135+ has native SSE support, but sse-starlette is more battle-tested for production use. | HIGH |

**Why FastAPI over alternatives:**
- **Not Django REST Framework:** DRF is sync-first, heavier ORM coupling, slower for I/O-bound workloads. DeckForge is async-native.
- **Not Flask:** No native async, no built-in validation, no automatic OpenAPI. Would require assembling 5+ libraries to match what FastAPI provides out of the box.
- **Not Litestar:** Promising but smaller ecosystem, fewer production references, less tooling. FastAPI's ecosystem advantage matters for hiring and community support.

---

### PPTX Generation

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| python-pptx | 1.0.2 | PPTX rendering | The only production-grade open-source Python library for creating/editing .pptx files. Supports native editable charts, tables, images, shapes, masters/layouts. Battle-tested at scale (Aither has 865-line production renderer). | HIGH |
| lxml | >=5.0 | XML manipulation | Dependency of python-pptx. Needed for direct Open XML manipulation when python-pptx API gaps require XML-level fixes (waterfall charts, advanced formatting). | HIGH |
| Pillow | >=12.1.1 | Image processing | Logo placement, image resizing/cropping, format conversion, thumbnail generation for previews. Essential for brand kit overlay. | HIGH |

**Critical note on python-pptx:** Version 1.0.2 was released August 2024 and the library is in low-activity maintenance mode. This is acceptable because:
1. The Open XML (.pptx) format is stable and not changing
2. The library handles all core slide elements (text, charts, tables, shapes, images)
3. When the API has gaps, you can manipulate the underlying lxml XML directly
4. No credible alternative exists in the open-source Python ecosystem

**What python-pptx handles natively:**
- 16+ chart types (bar, line, pie, scatter, bubble, area, radar, combo, etc.)
- Tables with merged cells and formatting
- Slide masters and layouts
- Images, shapes, text boxes with formatting
- Speaker notes
- Placeholder-based content insertion

**What requires lxml workarounds:**
- Waterfall charts (build from stacked bar with invisible series)
- Advanced chart formatting (data label positioning, custom colors per point)
- Some animation/transition properties
- Embedded fonts beyond system defaults

**Why NOT alternatives:**
- **Aspose.Slides:** Proprietary license ($1,199+/year), not open-source. Feature-rich but adds vendor lock-in and per-deployment costs that conflict with SaaS economics.
- **pptxlib:** Too new (Dec 2025), unproven at scale, limited documentation.
- **LibreOffice headless:** Different approach (template + fill), poor chart fidelity, process-based (slow), not Python-native API.

---

### Google Slides Output

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| google-api-python-client | >=2.150.0 | Google Slides API + Sheets API | Official Google client. Slides API for presentation creation via batchUpdate, Sheets API for chart-backing spreadsheets. | HIGH |
| google-auth | >=2.37.0 | OAuth 2.0 authentication | Official auth library for Google APIs. Supports OAuth 2.0 PKCE (SPAs) and service accounts. | HIGH |
| google-auth-oauthlib | >=1.2.0 | OAuth flow helpers | Bridges google-auth with OAuthLib for web OAuth flows. Required for user-authorized Slides access. | HIGH |

**Architecture for Google Slides charts:** Google Slides does not support native chart creation through the API alone. The pattern is:
1. Create a temporary Google Sheets spreadsheet with chart data
2. Create the chart in Sheets
3. Use `presentations.batchUpdate` with `createSheetsChart` to embed the Sheets chart into the Slides presentation
4. The chart remains linked and editable through Sheets

This is the only way to get editable charts in Google Slides programmatically. Document this pattern clearly in architecture docs.

---

### Chart Generation (Static Fallback)

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| plotly | >=6.1 | Static chart images | For chart types python-pptx cannot render natively (heatmap, sankey, gantt, sunburst). Plotly produces high-quality SVG/PNG via Kaleido. | MEDIUM |
| kaleido | >=1.0.0 | Plotly static export | Converts Plotly figures to PNG/SVG. v1.0 requires Chrome installed (changed from bundled Chromium). Server deployments need Chrome in the Docker image. | MEDIUM |

**Why Plotly over Matplotlib:**
- Plotly's chart types better match the financial visualization needs (waterfall, funnel, treemap, sankey)
- Cleaner default styling that looks presentation-ready without heavy customization
- Kaleido export produces crisp high-DPI images suitable for slide embedding

**Important Kaleido v1 caveat:** Kaleido 1.0+ requires Chrome to be installed on the system. This means the Docker image must include Chrome/Chromium. This adds ~400MB to image size but is a one-time cost. The alternative (bundled Chromium in older Kaleido) was unreliable on many platforms.

**When to use static vs native charts:**
- **Native (python-pptx built-in):** bar, line, pie, scatter, area, combo, radar -- always prefer native for PPTX output (editable in PowerPoint)
- **Static image fallback:** heatmap, sankey, gantt, sunburst, football field -- embed as high-DPI PNG when no native equivalent exists

---

### LLM Orchestration

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| LiteLLM | ==1.82.6 (pinned) | Multi-model LLM abstraction | Unified OpenAI-compatible API for 100+ models (Claude, GPT, Gemini, Ollama). Cost tracking, fallback chains, rate limiting built in. | MEDIUM |

**CRITICAL SECURITY NOTE:** LiteLLM suffered a supply chain attack in March 2026. Versions 1.82.7 and 1.82.8 contained credential-stealing malware. These have been removed from PyPI. **Pin to 1.82.6 exactly.** Monitor the official security advisory at https://docs.litellm.ai/blog/security-update-march-2026 before upgrading. The LiteLLM team has paused releases pending a supply chain review.

**Mitigation strategy:**
1. Pin `litellm==1.82.6` in pyproject.toml with a hash check
2. Use `pip install --require-hashes` in CI/CD
3. If LiteLLM trust does not recover, the fallback plan is a thin custom adapter layer using each provider's official SDK directly (openai, anthropic, google-generativeai). LiteLLM's value is convenience, not irreplaceability.

**Why LiteLLM over alternatives:**
- **Not Pydantic AI:** Pydantic AI is an agent framework, not a pure LLM abstraction layer. It adds agent orchestration patterns DeckForge does not need. The content pipeline has its own orchestration (intent -> outline -> expand -> refine). Using Pydantic AI's agent graph for this would fight DeckForge's pipeline design.
- **Not raw SDKs:** Managing 4+ provider SDKs (openai, anthropic, google-generativeai, ollama) with separate interfaces, error handling, and streaming implementations is significant boilerplate. LiteLLM eliminates this.
- **Not Portkey/OpenRouter:** These are managed services with per-request costs. DeckForge needs a library, not a SaaS proxy between it and LLM providers. Users bring their own API keys.

**Custom adapter as escape hatch:**
```python
# If LiteLLM trust is not restored, build a thin adapter:
class LLMAdapter(Protocol):
    async def complete(self, messages: list, model: str, **kwargs) -> CompletionResponse: ...
    async def stream(self, messages: list, model: str, **kwargs) -> AsyncIterator[StreamChunk]: ...

# Implementations: ClaudeAdapter, OpenAIAdapter, GeminiAdapter, OllamaAdapter
# Each wraps the official SDK. ~200 lines per adapter.
```

---

### Async Task Processing

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| ARQ | 0.27.0 | Async task queue | Native asyncio, Redis-backed, lightweight. Perfect match for FastAPI's async architecture. Content generation + rendering happen in workers. | MEDIUM |
| Redis | >=7.0 | Queue broker + cache + SSE pub/sub | Single Redis instance serves ARQ queue, rate limiting, SSE event pub/sub, and caching. Reduces infrastructure complexity. | HIGH |
| redis (python) | >=7.1.1 | Redis client | Official Redis Python client with native asyncio support (merged aioredis). | HIGH |

**Why ARQ over Celery:**
- ARQ is async-native; Celery is fundamentally synchronous with async bolted on
- ARQ workers run many concurrent async tasks in one process (ideal for I/O-bound LLM calls and API requests)
- Celery would need process-based concurrency, consuming far more memory for the same throughput
- ARQ's simplicity matches DeckForge's modular monolith -- no need for Celery's RabbitMQ/multi-broker complexity

**Why ARQ over Taskiq:**
- ARQ is more mature (v0.27, established) vs Taskiq (v0.12, still pre-1.0)
- ARQ's "at least once" delivery with idempotency requirement matches DeckForge's needs (rendering is naturally idempotent with request_id)
- Taskiq has broader broker support (NATS, Kafka) that DeckForge does not need

**ARQ maintenance mode caveat:** ARQ announced "maintenance only" mode. This is acceptable because:
1. It works well for its focused use case
2. The API surface is small and stable
3. Redis as broker is not going away
4. If ARQ is abandoned, migrating to Taskiq is straightforward (similar patterns)
5. The alternative (Celery) has its own troubled history (the 5.x release cycle was rocky)

---

### Database

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| PostgreSQL | >=16 | Primary data store | Users, API keys, decks, usage tracking, billing records. JSONB for IR storage. Enterprise-standard, excellent for financial data. | HIGH |
| SQLAlchemy | >=2.0.48 | ORM + query builder | Async support via psycopg3, type-safe queries, mature migration story. 2.0 style is clean and explicit. | HIGH |
| Alembic | >=1.18.4 | Database migrations | The only serious migration tool for SQLAlchemy. Auto-generates migrations from model diffs. | HIGH |
| psycopg | >=3.2 | PostgreSQL driver | Modern async-native PostgreSQL driver. Same URL works for sync and async engines. Replaces asyncpg + psycopg2 with a single driver. | HIGH |

**Why PostgreSQL over alternatives:**
- **Not MongoDB:** DeckForge has relational data (users -> API keys -> decks -> usage). The IR is structured JSON stored in JSONB columns, giving you document flexibility within a relational model.
- **Not SQLite:** No concurrent write support. DeckForge has multiple workers writing simultaneously.
- **Managed options:** Neon (serverless, free tier, branching) for MVP/development. Supabase or AWS RDS for production.

**Why psycopg3 over asyncpg:**
- psycopg3 supports both sync and async from the same driver
- Better maintained, actively developed by the original psycopg author
- SQLAlchemy 2.0's first-class psycopg3 support means same connection URL for both engine types

---

### File Storage

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| boto3 | >=1.36 | S3-compatible storage | Generated PPTX files, uploaded images, brand kit assets. S3 API is universal -- works with AWS S3, Cloudflare R2, MinIO. | HIGH |
| Cloudflare R2 | (service) | Object storage | Zero egress fees (critical for file downloads), S3-compatible API, global CDN. ~75% cheaper than AWS S3 for download-heavy workloads. | HIGH |

**Why R2 over S3:**
- PPTX files are downloaded frequently (every generation = a download). S3 egress at $0.09/GB adds up fast. R2 egress is free.
- S3-compatible API means zero code changes if migrating to/from S3 later
- R2 Workers integration for signed URLs and access control

**Storage strategy:**
- Generated PPTX/PDF files: R2 with 7-day auto-expiry (or user-configured retention)
- User-uploaded images/logos: R2 with indefinite retention
- IR snapshots: PostgreSQL JSONB (relational, queryable)

---

### Billing

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| stripe | >=15.0.0 | Billing + payments | Industry standard. Native support for subscriptions + metered usage + billing credits -- exactly DeckForge's pricing model. AI-focused metering features launched in 2026. | HIGH |

**Why Stripe:**
- Stripe Meters API is purpose-built for usage-based billing (send events like "tokens processed", "slides rendered")
- Billing Credits feature supports DeckForge's credit-based pricing model natively
- Python SDK is well-maintained (v15.0.0 released March 2026)
- Handles subscription tiers + overage + credit top-ups without custom billing logic
- Webhook system for async payment events integrates cleanly with FastAPI

**Credit implementation pattern:**
1. Create a Stripe Meter for "slide_credits"
2. Meter events fire on each render/generate completion
3. Billing credits pre-load credits on subscription activation
4. Overage pricing kicks in automatically when credits are exhausted

---

### Layout Engine

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| kiwisolver | >=1.4.8 | Cassowary constraint solver | 10-500x faster than original Cassowary. Used to solve layout constraints (margins, gutters, element positioning) on the 12-column grid. | MEDIUM |

**Architecture for layout solving:**

The layout engine is custom-built on top of kiwisolver, not an off-the-shelf layout library. kiwisolver provides the constraint-solving primitives; DeckForge builds:

1. **Grid system** -- 12-column grid with configurable margins/gutters as constraints
2. **Content measurement** -- Pillow for text bounding boxes, element counting
3. **Constraint generation** -- Convert slide_type + content profile into kiwisolver constraints
4. **Adaptive refinement** -- Iterative solving with fallback (reduce font, reflow, split slide)

This is the most technically novel part of DeckForge and cannot be bought off-the-shelf. Budget significant development time for it.

**Why kiwisolver over rolling a custom solver:**
- Cassowary is the proven algorithm for UI layout (used in iOS Auto Layout, macOS)
- kiwisolver is actively maintained (March 2026 release), C++ performance
- The constraint model maps naturally to slide layout rules (minimum margins, maximum content width, alignment groups)

---

### TypeScript SDK

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| @hey-api/openapi-ts | latest | SDK code generation | Generates typed TypeScript client from FastAPI's OpenAPI schema. Used by Vercel, PayPal. Production-ready SDK output with Zod validation. | HIGH |
| TypeScript | >=5.5 | SDK language | Type-safe builder API for constructing IR. Published to npm as @deckforge/sdk. | HIGH |
| tsup | latest | Build tool | Fast TypeScript bundler. ESM + CJS dual output for maximum compatibility. | HIGH |
| vitest | latest | SDK testing | Fast, Vite-native test runner for the SDK package. | HIGH |

**SDK generation strategy:**
1. FastAPI auto-generates OpenAPI 3.1 spec
2. @hey-api/openapi-ts generates typed HTTP client from the spec
3. Hand-written fluent builder API (Presentation.create(), Slide.bulletPoints(), etc.) wraps the generated client
4. Types for the IR schema are auto-generated from Pydantic models via OpenAPI

**Why @hey-api/openapi-ts over openapi-generator:**
- Produces modern TypeScript (ESM, tree-shakeable)
- Generates Zod schemas alongside types (runtime validation in the SDK)
- Smaller, cleaner output than openapi-generator's verbose templates
- Active development, used in production by major companies

---

### Testing

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| pytest | >=8.3 | Python test framework | Standard, extensive plugin ecosystem. async support via pytest-asyncio. | HIGH |
| pytest-asyncio | >=0.24 | Async test support | Required for testing async FastAPI routes and ARQ workers. | HIGH |
| httpx | >=0.28 | HTTP test client | AsyncClient for testing FastAPI endpoints. Also used by FastAPI's TestClient internally. | HIGH |
| fakeredis | >=2.25 | Redis mock | In-memory Redis for unit tests without a running Redis instance. Supports async. | HIGH |

---

### DevOps + Infrastructure

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| Docker | latest | Containerization | Consistent dev/prod environments. Must include Chrome/Chromium for Kaleido static chart export. | HIGH |
| docker-compose | latest | Local dev orchestration | API + worker + Redis + PostgreSQL in one command. | HIGH |
| Ruff | >=0.9 | Linting + formatting | Replaces flake8 + black + isort. 10-100x faster, single tool. The 2025-2026 standard for Python. | HIGH |
| mypy | >=1.14 | Type checking | Static type analysis. Critical for a complex IR schema system. | HIGH |
| pre-commit | >=4.0 | Git hooks | Runs ruff + mypy before commits. | MEDIUM |

---

## Full Dependency List

### pyproject.toml (core dependencies)

```toml
[project]
requires-python = ">=3.12,<3.14"

dependencies = [
    # API Framework
    "fastapi>=0.135.2",
    "uvicorn[standard]>=0.42.0",
    "pydantic>=2.12",
    "sse-starlette>=3.3.3",

    # PPTX Generation
    "python-pptx==1.0.2",
    "Pillow>=12.1.1",

    # Google Slides/Sheets
    "google-api-python-client>=2.150.0",
    "google-auth>=2.37.0",
    "google-auth-oauthlib>=1.2.0",

    # Charts (static fallback)
    "plotly>=6.1",
    "kaleido>=1.0.0",

    # LLM Orchestration
    "litellm==1.82.6",  # PINNED - supply chain attack on 1.82.7/1.82.8

    # Async Workers
    "arq>=0.27.0",
    "redis>=7.1.1",

    # Database
    "sqlalchemy[asyncio]>=2.0.48",
    "alembic>=1.18.4",
    "psycopg[binary]>=3.2",

    # Storage
    "boto3>=1.36",

    # Billing
    "stripe>=15.0.0",

    # Layout
    "kiwisolver>=1.4.8",

    # Utilities
    "pyyaml>=6.0",       # Theme definitions
    "httpx>=0.28",       # External HTTP calls
    "python-multipart",  # File uploads
    "passlib[bcrypt]",   # Password hashing
    "python-jose[cryptography]",  # JWT tokens
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.24",
    "pytest-cov>=6.0",
    "httpx>=0.28",
    "fakeredis>=2.25",
    "ruff>=0.9",
    "mypy>=1.14",
    "pre-commit>=4.0",
]
```

### SDK package.json (core dependencies)

```json
{
  "name": "@deckforge/sdk",
  "version": "0.1.0",
  "type": "module",
  "devDependencies": {
    "@hey-api/openapi-ts": "latest",
    "tsup": "latest",
    "typescript": "^5.5",
    "vitest": "latest",
    "zod": "^3.23"
  }
}
```

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|---|---|---|---|
| API Framework | FastAPI | Django REST Framework | Sync-first, heavier, slower for I/O-bound async workloads |
| API Framework | FastAPI | Litestar | Smaller ecosystem, fewer production references, less tooling |
| PPTX Library | python-pptx | Aspose.Slides | Proprietary ($1,199+/yr), vendor lock-in, conflicts with SaaS economics |
| PPTX Library | python-pptx | pptxlib | Too new (Dec 2025), unproven, limited docs |
| Task Queue | ARQ | Celery | Sync-first, process-based concurrency wastes memory for I/O-bound tasks |
| Task Queue | ARQ | Taskiq | Pre-1.0, less mature. Good fallback if ARQ is abandoned. |
| LLM Abstraction | LiteLLM | Pydantic AI | Agent framework, not pure abstraction. DeckForge has its own pipeline. |
| LLM Abstraction | LiteLLM | Raw SDKs | 4+ SDKs with different interfaces = too much boilerplate |
| LLM Abstraction | LiteLLM | Portkey/OpenRouter | Managed SaaS proxies, not libraries. Users bring their own keys. |
| Database | PostgreSQL + SQLAlchemy | MongoDB | Relational data model with JSONB for document flexibility is better fit |
| Database Driver | psycopg3 | asyncpg | psycopg3 handles both sync + async from one driver |
| Chart Fallback | Plotly + Kaleido | Matplotlib | Plotly's financial chart types and default styling are more presentation-ready |
| Storage | Cloudflare R2 | AWS S3 | Zero egress fees critical for download-heavy file delivery |
| SDK Generation | @hey-api/openapi-ts | openapi-generator | Cleaner TypeScript output, Zod schemas, tree-shakeable ESM |
| Python Linter | Ruff | flake8 + black + isort | Ruff replaces all three, 10-100x faster |

---

## Infrastructure Architecture (MVP)

```
                    +-------------------+
                    |   Cloudflare R2   |
                    |  (file storage)   |
                    +--------^----------+
                             |
+--------+     +-------------+-------------+     +-------------+
| Client | --> | FastAPI (uvicorn)          | --> | PostgreSQL  |
|        | <-- | auth, routing, SSE, billing| <-- | (Neon)      |
+--------+     +------+--------+-----------+     +-------------+
                      |        |
               +------v-+  +--v-----------+
               | Redis  |  | ARQ Workers  |
               | (queue,|  | - content    |
               |  cache,|  | - rendering  |
               |  SSE)  |  | - QA         |
               +--------+  +--------------+
```

**MVP hosting targets:**
- API + Workers: Railway or Fly.io ($25-50/mo)
- PostgreSQL: Neon (free tier, then $19/mo)
- Redis: Upstash (free tier, then $10/mo)
- Storage: Cloudflare R2 (10GB free, then $0.015/GB/mo)
- Total: ~$50-100/mo until meaningful traffic

---

## Docker Base Image

```dockerfile
FROM python:3.12-slim

# Required for Kaleido v1 static chart export
RUN apt-get update && apt-get install -y \
    chromium \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_PATH=/usr/bin/chromium
```

**Why this matters:** Kaleido v1.0 requires Chrome/Chromium installed. Forgetting this breaks static chart generation in production. The `python:3.12-slim` + Chromium base image is ~500MB, which is acceptable for a rendering-heavy service.

---

## Sources

### Verified (HIGH confidence)
- [python-pptx PyPI](https://pypi.org/project/python-pptx/) - v1.0.2, Aug 2024
- [FastAPI PyPI](https://pypi.org/project/fastapi/) - v0.135.2, Mar 2026
- [Pydantic v2.12 release](https://pydantic.dev/articles/pydantic-v2-12-release) - v2.12.5, Nov 2025
- [SQLAlchemy 2.0 Changelog](https://docs.sqlalchemy.org/en/20/changelog/changelog_20.html) - v2.0.48, Mar 2026
- [Alembic PyPI](https://pypi.org/project/alembic/) - v1.18.4, Feb 2026
- [ARQ PyPI](https://pypi.org/project/arq/) - v0.27.0, Feb 2026
- [redis-py PyPI](https://pypi.org/project/redis/) - v7.1.1, Feb 2026
- [Uvicorn PyPI](https://pypi.org/project/uvicorn/) - v0.42.0, Mar 2026
- [sse-starlette PyPI](https://pypi.org/project/sse-starlette/) - v3.3.3, Mar 2026
- [Stripe PyPI](https://pypi.org/project/stripe/) - v15.0.0, Mar 2026
- [Pillow PyPI](https://pypi.org/project/pillow/) - v12.1.1, Feb 2026
- [Stripe Billing Credits](https://docs.stripe.com/billing/subscriptions/usage-based/billing-credits/implementation-guide)
- [Stripe Meters API](https://docs.stripe.com/api/billing/meter)
- [Cloudflare R2 boto3 docs](https://developers.cloudflare.com/r2/examples/aws/boto3/)
- [Google Slides API quickstart](https://developers.google.com/workspace/slides/api/quickstart/python)
- [python-pptx chart docs](https://python-pptx.readthedocs.io/en/latest/user/charts.html)
- [Kaleido v1 changes](https://plotly.com/python/static-image-generation-changes/)

### Verified with caveats (MEDIUM confidence)
- [LiteLLM GitHub](https://github.com/BerriAI/litellm) - v1.82.6 safe; supply chain attack on 1.82.7-1.82.8
- [LiteLLM Security Advisory](https://docs.litellm.ai/blog/security-update-march-2026) - Monitor before upgrading past 1.82.6
- [kiwisolver PyPI](https://pypi.org/project/kiwisolver/) - v1.4.8, Mar 2026
- [Plotly static image changes](https://plotly.com/python/static-image-generation-changes/) - Kaleido v1 requires Chrome
- [Taskiq GitHub](https://github.com/taskiq-python/taskiq) - v0.12.1, backup if ARQ abandoned

### Community/WebSearch (noted for context)
- [FastAPI 2026 architecture patterns](https://nerdleveltech.com/building-lightning-fast-ai-backends-with-fastapi-2026-edition)
- [ARQ vs Celery comparison](https://leapcell.io/blog/celery-versus-arq-choosing-the-right-task-queue-for-python-applications)
- [LiteLLM alternatives 2026](https://www.edenai.co/post/best-alternatives-to-litellm)
- [@hey-api/openapi-ts](https://github.com/hey-api/openapi-ts) - SDK generation from OpenAPI
- [FastAPI SDK generation docs](https://fastapi.tiangolo.com/advanced/generate-clients/)
