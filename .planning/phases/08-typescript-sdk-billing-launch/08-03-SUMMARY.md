---
phase: 08-typescript-sdk-billing-launch
plan: 03
subsystem: api, infra
tags: [fastapi, discovery, fly.io, docker, deployment, slide-types, themes]

requires:
  - phase: 02-layout-engine-theme-system
    provides: ThemeRegistry with 15 YAML themes and color resolution
  - phase: 01-foundation-ir-schema
    provides: SlideType enum (32 types), Presentation Pydantic model
provides:
  - GET /v1/themes endpoint with color previews for all 15 themes
  - GET /v1/slide-types endpoint with 32 slide types and valid example IR
  - GET /v1/capabilities endpoint with API metadata and feature flags
  - SlideTypeRegistry service with per-type metadata and example IR
  - Production multi-stage Dockerfile with Chromium, non-root user
  - Fly.io deployment config with API + worker process groups
  - Railway Procfile for alternative deployment
affects: [deployment, sdk-consumers, api-documentation]

tech-stack:
  added: [fly.io, docker-multi-stage]
  patterns: [discovery-endpoint, lru-cache-static-data, static-registry]

key-files:
  created:
    - src/deckforge/api/routes/discovery.py
    - src/deckforge/api/schemas/discovery_schemas.py
    - src/deckforge/services/slide_type_registry.py
    - fly.toml
    - Procfile
    - .dockerignore
    - tests/test_discovery.py
  modified:
    - src/deckforge/api/app.py
    - Dockerfile

key-decisions:
  - "lru_cache for theme list (themes are YAML files, rarely change at runtime)"
  - "SlideTypeRegistry as static dict with helper functions (no database needed for discovery)"
  - "Example IRs use minimal valid Presentation payloads validated at module load"
  - "Multi-stage Dockerfile separates build deps from runtime (smaller image)"
  - "Chromium in runtime image for Kaleido/Plotly static chart rendering"

patterns-established:
  - "Discovery endpoint pattern: public GET endpoints returning cached static data"
  - "Static registry pattern: class wrapping module-level dict with get_all/get_by_id/get_by_category"

requirements-completed: [API-05, API-06, API-07, INFRA-05]

duration: 6min
completed: 2026-03-29
---

# Phase 8 Plan 3: Discovery Endpoints and Deployment Config Summary

**Three discovery endpoints (themes, slide-types, capabilities) with full example IR for all 32 slide types, plus production Dockerfile and Fly.io config**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-29T08:04:27Z
- **Completed:** 2026-03-29T08:10:52Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- GET /v1/themes returns 15 themes with hex color previews (primary, accent, background, etc.)
- GET /v1/slide-types returns all 32 types with validated Pydantic example IR, filterable by category
- GET /v1/capabilities returns API version, sync/async limits, chart types, rate limits, and feature flags
- SlideTypeRegistry covers all 32 SlideType enum values with realistic example data
- Production Dockerfile: multi-stage build, non-root user, Chromium for charts, healthcheck
- Fly.io config: API + worker process groups, auto-scaling, HTTPS, 1GB shared-CPU VMs

## Task Commits

Each task was committed atomically:

1. **Task 1: Discovery endpoints and slide type registry (TDD)**
   - `0dda5a0` (test) - Failing tests for 3 discovery endpoints + registry completeness
   - `53b4c21` (feat) - Implementation passing all 16 tests
2. **Task 2: Production Dockerfile and Fly.io deployment config** - `54597f3` (feat)

## Files Created/Modified
- `src/deckforge/services/slide_type_registry.py` - Static catalog of 32 slide types with metadata and example IR
- `src/deckforge/api/routes/discovery.py` - GET /v1/themes, /v1/slide-types, /v1/capabilities endpoints
- `src/deckforge/api/schemas/discovery_schemas.py` - Pydantic response models for discovery endpoints
- `src/deckforge/api/app.py` - Wired discovery router into FastAPI app factory
- `tests/test_discovery.py` - 16 tests covering all discovery endpoints and registry
- `Dockerfile` - Production multi-stage build replacing development single-stage
- `fly.toml` - Fly.io deployment with API + worker process groups
- `Procfile` - Railway/Heroku compatibility
- `.dockerignore` - Excludes tests, docs, caches, secrets from Docker context

## Decisions Made
- Used `functools.lru_cache` for theme list building (themes are static YAML files)
- SlideTypeRegistry implemented as module-level dict with class wrapper (no DB needed)
- All 32 example IRs validated against `Presentation.model_validate()` ensuring correctness
- Bullet list items are plain strings (not dicts), table rows are plain lists (not dict with cells key)
- Chart elements use `chart_data` field (not `content`) per IR schema
- Multi-stage Dockerfile keeps build tools (gcc) out of runtime image
- Chromium included in runtime for Plotly/Kaleido static chart PNG rendering

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed example IR format for bullet lists, tables, and charts**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** Initial helper functions used `{"text": t}` for bullet items, `{"cells": r}` for table rows, and `content` for chart data -- all mismatched the actual Pydantic IR schema
- **Fix:** Bullet items as plain strings, table rows as plain lists, chart elements use `chart_data` with proper `BarChartData`/`WaterfallChartData` schemas
- **Files modified:** src/deckforge/services/slide_type_registry.py
- **Verification:** All 32 example IRs pass `Presentation.model_validate()`
- **Committed in:** 53b4c21 (Task 1 feat commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential fix -- example IRs must validate against the actual IR schema. No scope creep.

## Issues Encountered
None beyond the IR format correction handled inline during implementation.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
This is the FINAL plan of the entire project. All 22 plans across 8 phases are now complete.

DeckForge API is ready for deployment:
- All API routes wired (health, discovery, render, generate, preview, jobs, auth, decks, estimate, batch, webhooks, billing)
- TypeScript SDK published (08-01)
- Billing system with Stripe integration (08-02)
- Production Docker + Fly.io config ready for `fly deploy`

## Self-Check: PASSED

All 8 files verified present. All 3 commits verified in git log.

---
*Phase: 08-typescript-sdk-billing-launch*
*Completed: 2026-03-29*
