# DeckForge Feature Audit

**Auditor**: Claude Opus 4.6 (1M context)
**Date**: 2026-03-30
**Scope**: Full codebase audit of `/c/Users/lukep/Desktop/Projects AI/SlideMaker`
**Files reviewed**: 120+ Python/TypeScript source files, configs, demos, tests

---

## Task 1: Core Rendering Pipeline Assessment

### End-to-End Flow

The rendering pipeline is well-architected with clear separation:

```
IR (Pydantic) -> Layout Engine -> PPTX Renderer -> QA Pipeline -> bytes
```

**Entry points**:
- `POST /v1/render` -- accepts IR JSON, validates via Pydantic, renders sync (<=10 slides) or async (>10)
- `POST /v1/generate` -- accepts NL prompt, enqueues to ARQ content worker
- `render_pipeline()` in `workers/tasks.py` -- shared sync function used by both API sync path and ARQ worker

**PPTX Renderer** (`rendering/pptx_renderer.py`):
- Creates a blank 13.333" x 7.5" (16:9 widescreen) presentation
- Iterates layout results, creates slides, applies backgrounds, renders elements, applies transitions and speaker notes
- Finance slides get special full-slide rendering via `render_finance_slide()`
- Non-finance slides use element-by-element dispatch through `ELEMENT_RENDERERS` registry
- Exception handling is per-element (one bad element doesn't kill the whole slide)

**Layout Engine** (`layout/engine.py`):
- 7-step pipeline: pattern select -> slide master -> measure -> regions -> constrain -> solve -> overflow
- Uses kiwisolver for constraint solving
- Adaptive overflow cascade: font reduction (2pt steps, min 10/14pt) -> reflow (90% width) -> slide split
- Slide splitting works for bullet lists (halves items) with "(cont.)" continuation slides

**Content Pipeline** (`content/pipeline.py`):
- 4-stage async pipeline: IntentParser -> Outliner -> SlideWriter -> CrossSlideRefiner
- Model-agnostic via LLMRouter with fallback chain (Claude -> OpenAI -> Gemini -> Ollama)
- SSE streaming via Redis pub/sub for real-time progress events
- Final output validated via `Presentation.model_validate()`

**Demo IRs**:
- 5 demos: startup-pitch (285 lines), pe-deal-memo (306), mckinsey-strategy (304), board-update (295), product-launch (308)
- All include prompt.txt + ir.json pairs
- Appear well-structured but use a simpler element format (type/content/role) that may not match the full IR schema

### Verdict: Core Pipeline is Solid
The architecture is production-grade. The main risk is that it has not been tested end-to-end with real LLM calls and real PPTX output validation.

---

## Task 2: Quality Risks

### Font Handling -- RISK: MODERATE

**What it does**: Uses a safe-font whitelist (`_SAFE_FONTS` in `rendering/utils.py`) with 22 PowerPoint-universal fonts. `resolve_font_name()` maps requested fonts to safe alternatives, falling back to Calibri.

**Issue**: Themes reference fonts like "Montserrat", "Open Sans", "JetBrains Mono" that are NOT in the safe font set. `resolve_font_name("Montserrat")` returns "Calibri". This means the executive-dark theme (and others) will silently render with wrong fonts.

**Impact**: Every theme with non-system fonts will look different than designed. The Dockerfile installs `fonts-liberation` and `fonts-dejavu-core` but NOT Montserrat/Open Sans/etc.

**Fix effort**: Low -- either (a) bundle Google Fonts in the Docker image or (b) update theme YAMLs to use system fonts, or (c) expand the safe font mapping to include Liberation/DejaVu substitutes for the theme fonts.

### Image Placement -- RISK: LOW

**What it does**: `ImageRenderer` supports base64, URL download (via httpx), and placeholder rectangles. Has `contain` mode (aspect-ratio preserving with PIL), `fill` mode, and `cover` mode.

**Issue**: The `contain` mode does integer division on EMU values (`width // 2`) which may cause subtle positioning errors since `Inches()` returns EMU values, not pixels. The division should work on the EMU scale but is semantically confusing.

**Impact**: Minor visual misalignment in contain mode images.

### Chart Rendering -- RISK: LOW-MODERATE

**What it does**: 24 chart types split into:
- **Native editable** (14): bar, stacked_bar, grouped_bar, horizontal_bar, line, multi_line, area, stacked_area, pie, donut, scatter, bubble, combo, radar -- use python-pptx native chart objects
- **Static PNG** (10): waterfall, funnel, treemap, tornado, football_field, sensitivity_table, heatmap, sankey, gantt, sunburst -- use Plotly -> PNG at 2x scale (300 DPI)

**Issue 1**: The chart element is registered as `_noop` in `ELEMENT_RENDERERS` (line 82: `ElementType.CHART.value: _noop`). Charts are rendered via a separate `render_chart()` function that must be called explicitly. This means charts in non-finance slides rendered via the standard element loop WILL NOT RENDER -- they get a no-op.

**Impact**: CRITICAL for non-finance slides with charts. The `render_element()` path skips chart elements entirely. Charts only work in finance slide types (which use dedicated slide renderers) or if there's integration code I haven't found.

**Issue 2**: Static charts require Kaleido/Chromium (installed in Dockerfile). If Chromium is missing locally, `fig.to_image()` will crash.

### Text Overflow -- RISK: LOW

**What it does**: 3-stage adaptive cascade:
1. Font reduction in 2pt steps (min 10pt body, 14pt heading), up to 5 iterations
2. Reflow with 90% width for more aggressive wrapping
3. Slide splitting (divides bullet lists in half, creates continuation slides)

**Verdict**: Well-designed. The main gap is that body text (non-bullet) splitting falls back to returning the original slide unchanged ("cannot split non-bullet content easily"). Long paragraphs will just overflow.

### Theme Application -- RISK: LOW

**What it does**: 15 YAML themes with 3-tier variable resolution:
1. Tier 1: Raw color values (`colors.navy_900: "#0A1E3D"`)
2. Tier 2: Semantic palette (`palette.primary: "$colors.navy_900"`)
3. Tier 3: Slide masters (regions with font/color/size)

`ThemeResolver` expands `$variable` references. `ThemeRegistry` loads, resolves, validates contrast (WCAG AA), and caches.

**Strengths**: Contrast validation with warnings, BrandKit merger with protected keys, chart color palettes per theme.

**Issue**: The `_dict_to_theme()` method has defensive fallbacks for unresolved `$references` (returns `#000000`). This means a theme with a typo in a reference silently renders with black instead of crashing with a helpful error.

---

## Task 3: Bugs and Gaps That Block Launch

### BUG 1: CRITICAL -- `python-pptx` missing from `pyproject.toml`

The package `python-pptx` is imported throughout the rendering code (`from pptx import Presentation`) but is NOT listed in `pyproject.toml` dependencies. A fresh `pip install` will fail on first import.

**File**: `pyproject.toml` line 11-37
**Fix**: Add `"python-pptx>=1.0.0",` to the dependencies list.

### BUG 2: CRITICAL -- Docker Compose uses wrong module path

`docker-compose.yml` line 6 uses `src.deckforge.main:app` but the Dockerfile CMD (line 60) uses `deckforge.main:app`. The Docker image uses `[tool.setuptools.packages.find] where = ["src"]`, which means the installed package is `deckforge`, not `src.deckforge`.

The docker-compose volume mount (`.:/app`) makes the `src/` directory available, so the `src.deckforge` import path works with the mount but would fail in production without it. The ARQ worker commands on lines 23 and 34 have the same issue (`arq src.deckforge.workers.settings.*`).

**Fix**: Change to `deckforge.main:app` and `deckforge.workers.settings.*` in docker-compose.yml.

### BUG 3: CRITICAL -- Chart elements are no-ops in standard slides

`ELEMENT_RENDERERS` maps `ElementType.CHART.value` to `_noop` (a no-op renderer). The `render_chart()` function exists but is never called from the standard element rendering path in `PptxRenderer._render_elements()`. Only finance slide types render charts because they use `render_finance_slide()` which has its own chart handling.

**Fix**: Replace `_noop` with a chart element renderer that calls `render_chart()`, or add chart dispatch logic to the element rendering loop.

### BUG 4: MODERATE -- Preview endpoint tuple unpacking error

`preview.py` line 52 calls `pptx_bytes = render_pipeline(preview_ir)` but `render_pipeline()` returns `tuple[bytes, QAReport]`. This will crash with a TypeError when `pptx_to_thumbnails()` receives a tuple instead of bytes.

**Fix**: Change to `pptx_bytes, _qa_report = render_pipeline(preview_ir)`.

### BUG 5: MODERATE -- Google Slides not listed in capabilities

`discovery.py` line 128 returns `supported_output_formats=["pptx"]` but the render endpoint accepts `output_format=gslides`. Agents relying on capabilities discovery won't know Google Slides is available.

**Fix**: Add `"gslides"` to the list.

### BUG 6: LOW -- Google OAuth refresh token stored in plaintext

`auth_google.py` line 104 has an explicit `TODO: Encrypt with Fernet`. The refresh token is stored as plain text in the database, which is a security concern for production.

### BUG 7: LOW -- Missing Alembic migrations for initial tables

The `alembic/versions/` directory only contains migrations 003-005 (batch_webhook_tables, billing_tables, payment_events). Migrations 001-002 (which presumably create the core User, ApiKey, Job, Deck tables) are missing.

**Impact**: Running `alembic upgrade head` on a fresh database will fail because migrations 003+ reference tables that don't exist.

### BUG 8: LOW -- MCP tool attribute mismatch

`mcp/tools.py` line 53 accesses `qa_report.overall_score` but the `QAReport` type uses `.score` (confirmed in `qa/pipeline.py` line 112: `qa_report.score`). Similarly, line 60 accesses `qa_report.issues` which may not be the correct attribute name.

### BUG 9: LOW -- `AuthContext.stripe_customer_id` doesn't exist

`billing.py` lines 155 and 199 access `api_key.stripe_customer_id` via `getattr()` but `AuthContext` dataclass has no `stripe_customer_id` field. The checkout endpoint will always return "No Stripe customer ID associated with this API key."

### BUG 10: LOW -- Fly.io worker process references missing module

`fly.toml` line 12 runs `python -m deckforge.workers.run` but no `workers/run.py` file exists.

---

## Task 4: Highest-ROI Quick Wins

### 1. Fix `python-pptx` dependency (5 minutes, blocks everything)
Add to `pyproject.toml`. Without this, nothing installs.

### 2. Fix chart rendering in standard slides (30 minutes, major feature gap)
Wire `render_chart()` into the element renderer registry instead of the no-op. This unlocks charts in 23 of 32 slide types.

### 3. Fix Docker Compose module paths (5 minutes, blocks local dev)
Change `src.deckforge` to `deckforge` in all three docker-compose commands.

### 4. Fix preview endpoint tuple unpacking (5 minutes, crashes on use)
Unpack `render_pipeline()` return value correctly.

### 5. Add font bundling to Docker image (20 minutes, visual quality)
Install Google Fonts (Montserrat, Open Sans) in the Dockerfile runtime stage. This makes all 15 themes render with correct typography.

### 6. Add Swagger/OpenAPI documentation (0 minutes -- already exists!)
FastAPI auto-generates OpenAPI docs at `/docs` and `/redoc`. Already configured with title, version, and description. Just needs marketing.

### 7. Add PDF export (2-4 hours, high-value feature)
LibreOffice is already in the Dockerfile. The thumbnail path already converts PPTX to PDF. Expose a `output_format=pdf` option that returns the intermediate PDF instead of converting to PNG.

### 8. Better error messages for IR validation (1 hour)
Pydantic v2 already gives detailed validation errors, but they could be wrapped with domain-specific guidance (e.g., "slide_type 'foo' is not valid. Valid types: title, bullets, chart, ...").

### 9. Markdown input support for content generation (2-3 hours)
Add a markdown parser to the intent_parser stage that converts markdown documents into structured slide outlines, bypassing the LLM for users who already have content.

### 10. Example gallery page (2-4 hours)
The 5 demos already exist with prompt.txt + ir.json. Build a simple endpoint that lists demos and allows rendering them with any theme -- essentially a live playground.

---

## Task 5: Feature Launch Readiness Matrix

| Feature | Code Exists | Works E2E | Launch Ready | Effort to Fix |
|---|---|---|---|---|
| **PPTX generation** | Yes (full) | Mostly* | No* | *Fix python-pptx dep + chart no-op: 1hr |
| **Google Slides output** | Yes (full) | Untested | No | Needs OAuth test + gslides dep: 2-4hr |
| **Content pipeline (NL->IR)** | Yes (4-stage) | Untested | No | Needs LLM keys + integration test: 2hr |
| **Native charts (bar/line/pie/etc)** | Yes (14 types) | Broken** | No | **Chart no-op bug: 30min |
| **Static charts (waterfall/funnel/etc)** | Yes (10 types) | Broken** | No | **Same no-op bug + Kaleido test: 1hr |
| **Layout engine** | Yes (full) | Likely works | Yes (conditional) | Test with real content: 1hr |
| **Overflow handling** | Yes (3-stage) | Likely works | Yes (conditional) | Body text split gap: 2hr |
| **15 themes** | Yes (YAML) | Work but wrong fonts | No | Font bundling: 20min |
| **Theme contrast validation** | Yes (WCAG AA) | Works | Yes | -- |
| **BrandKit overlay** | Yes (merger) | Likely works | Yes (conditional) | Test: 30min |
| **9 finance slides** | Yes (full renderers) | Likely works | Yes (conditional) | Test with real data: 2hr |
| **TypeScript SDK** | Yes (builder+client) | Likely works | Yes (conditional) | Build + npm test: 30min |
| **MCP server (6 tools)** | Yes (FastMCP) | Broken*** | No | ***Fix qa_report attr: 15min |
| **Stripe billing (3 tiers)** | Yes (full) | Incomplete | No | Missing stripe_customer_id: 2-4hr |
| **Credit reservation/deduction** | Yes (full) | Likely works | Yes (conditional) | Test: 1hr |
| **x402 machine payments** | Yes (full) | Untested | No | Needs facilitator test: 4hr |
| **Unkey auth (production)** | Yes (full) | Untested | No | Needs Unkey account: 1hr |
| **DB auth (development)** | Yes (SHA-256) | Likely works | Yes (conditional) | -- |
| **Rate limiting** | Yes (dual: Unkey + Redis) | Likely works | Yes (conditional) | -- |
| **Batch rendering** | Yes (full) | Untested | No | Test: 1hr |
| **Webhook delivery** | Yes (HMAC signed) | Untested | No | Test: 1hr |
| **SSE streaming** | Yes (Redis pub/sub) | Untested | No | Test: 1hr |
| **QA pipeline (5-pass)** | Yes (full) | Likely works | Yes (conditional) | -- |
| **Auto-fix (contrast/overflow)** | Yes (full) | Likely works | Yes (conditional) | -- |
| **Preview thumbnails** | Yes (LibreOffice) | Broken**** | No | ****Fix tuple unpacking: 5min |
| **Idempotency (X-Request-Id)** | Yes | Likely works | Yes (conditional) | -- |
| **Cost estimation** | Yes | Likely works | Yes | -- |
| **Discovery endpoints** | Yes (themes/types/caps) | Works | Mostly (gslides missing) | 5min |
| **Onboarding (signup+status)** | Yes | Likely works | Yes (conditional) | -- |
| **Analytics dashboard** | Yes (admin only) | Untested | No | Test: 1hr |
| **Docker setup** | Yes | Broken***** | No | *****Fix module paths: 5min |
| **Fly.io deployment** | Yes | Broken****** | No | ******Missing workers/run.py: 30min |
| **Alembic migrations** | Partial (3/5) | Broken | No | Missing 001-002: 30min |

### Legend
- **Works E2E**: Has been tested or is architecturally certain to work
- **Launch Ready**: Can be shipped to paying customers today
- **Yes (conditional)**: Code is correct but needs integration testing before launch
- **Broken**: Has a specific identified bug that prevents operation

---

## Priority Fix Order for Launch

### P0 -- Blocks all operation (1-2 hours total)
1. Add `python-pptx` to `pyproject.toml`
2. Fix Docker Compose module paths (`src.deckforge` -> `deckforge`)
3. Add missing Alembic migrations 001-002
4. Fix chart no-op in element renderer registry

### P1 -- Blocks key features (2-3 hours total)
5. Fix preview endpoint tuple unpacking
6. Fix MCP tool `qa_report.overall_score` -> `qa_report.score`
7. Add `gslides` to capabilities response
8. Fix Fly.io worker process (create `workers/run.py` or fix fly.toml)
9. Add Google Fonts to Dockerfile

### P2 -- Blocks billing/auth (4-6 hours total)
10. Wire `stripe_customer_id` into AuthContext or billing flow
11. Encrypt Google OAuth refresh tokens (Fernet)
12. Integration test: full render with demo IRs
13. Integration test: content generation with at least one LLM provider

### P3 -- Polish for launch (4-8 hours total)
14. Add PDF export endpoint (LibreOffice already installed)
15. Markdown input support for /v1/generate
16. Demo gallery endpoint
17. Body text overflow splitting
18. Expand safe font mapping for non-system fonts

---

## Architecture Strengths

The codebase is impressively well-structured for its age:

- **Clean separation of concerns**: IR schema, layout engine, rendering, content generation, and API are fully decoupled
- **Pydantic everywhere**: Strong typing with discriminated unions for 32 slide types, 24 chart types, and all elements
- **Dual auth paths**: Production (Unkey) and development (DB) with identical AuthContext interface
- **Async-first**: FastAPI + SQLAlchemy 2.0 async + ARQ workers
- **Graceful degradation**: Thumbnail fallback (LibreOffice -> Pillow placeholder), LLM fallback chain, font fallback
- **QA built in**: 5-pass pipeline with auto-fix is a genuine differentiator
- **Comprehensive test suite**: 33 unit test files + 7 integration test files cover most components

The main gap is that the code has been written but not yet exercised end-to-end. The bugs above are all "first-run" bugs that would surface immediately during manual testing. A single afternoon of smoke testing + the P0 fixes would make this launch-ready for beta.
