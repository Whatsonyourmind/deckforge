---
phase: 07-qa-pipeline-deck-operations
plan: 03
subsystem: api
tags: [batch, webhooks, hmac, qa-pipeline, arq, fastapi]

# Dependency graph
requires:
  - phase: 07-qa-pipeline-deck-operations (07-01)
    provides: QAPipeline with 5 checkers, autofix, and scorer
  - phase: 07-qa-pipeline-deck-operations (07-02)
    provides: DeckOperations service and CostEstimator
provides:
  - Batch render endpoint (POST /v1/batch/render) for parallel multi-IR rendering
  - Batch variations endpoint (POST /v1/batch/variations) for theme-based fan-out
  - Webhook registration CRUD (POST/GET/DELETE /v1/webhooks) with HMAC-SHA256 signing
  - QA pipeline wired into every render path (sync, async, batch) with quality_score
  - BatchJob and WebhookRegistration DB models with repositories
affects: [08-deployment, api-documentation]

# Tech tracking
tech-stack:
  added: [hmac, secrets]
  patterns: [HMAC-SHA256 webhook signing, batch fan-out via ARQ, registered webhook delivery]

key-files:
  created:
    - src/deckforge/db/models/batch_job.py
    - src/deckforge/db/models/webhook_registration.py
    - src/deckforge/db/repositories/batch.py
    - src/deckforge/db/repositories/webhook.py
    - src/deckforge/api/routes/batch.py
    - src/deckforge/api/routes/webhooks.py
    - src/deckforge/api/schemas/batch_schemas.py
    - src/deckforge/api/schemas/webhook_schemas.py
    - alembic/versions/003_batch_webhook_tables.py
    - tests/test_batch_webhooks.py
  modified:
    - src/deckforge/workers/tasks.py
    - src/deckforge/workers/webhooks.py
    - src/deckforge/api/routes/render.py
    - src/deckforge/api/app.py
    - src/deckforge/db/models/__init__.py
    - src/deckforge/db/models/job.py
    - src/deckforge/db/repositories/__init__.py
    - src/deckforge/db/repositories/job.py

key-decisions:
  - "Python-side event filtering for webhook get_by_event (portable across SQLite and PostgreSQL)"
  - "Webhook secret masked in list response (only shown once at creation time)"
  - "render_pipeline returns tuple (bytes, QAReport) -- all callers updated to destructure"
  - "Batch completion checks total_done = completed + failed vs total_items for status transitions"

patterns-established:
  - "HMAC-SHA256 webhook signing: sign_webhook_payload(payload_bytes, secret) -> (signature, timestamp)"
  - "Batch fan-out pattern: create BatchJob, create N individual Jobs with batch_id FK, enqueue each to ARQ"
  - "Registered webhook delivery: _fire_registered_webhooks looks up by event type and delivers with HMAC"

requirements-completed: [BATCH-01, BATCH-02, API-12]

# Metrics
duration: 8min
completed: 2026-03-29
---

# Phase 7 Plan 3: Batch Render, Webhook Registration, and QA Pipeline Integration Summary

**Batch render/variations endpoints with ARQ fan-out, HMAC-SHA256 webhook registration and delivery, and QA pipeline wired into every render path populating quality_score**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-29T03:28:33Z
- **Completed:** 2026-03-29T03:36:57Z
- **Tasks:** 2
- **Files modified:** 18

## Accomplishments
- Batch render and variations endpoints fan out to individual ARQ render jobs with atomic completion tracking
- Webhook registration with auto-generated HMAC-SHA256 secrets for payload signing and verification
- QA pipeline integrated into every render path (sync API, async worker, content generation) storing quality_score on decks
- 8 passing tests covering HMAC signing, model construction, and repository operations

## Task Commits

Each task was committed atomically:

1. **Task 1: Batch and webhook DB models, repositories, and enhanced webhook delivery** - `dcf3398` (test: TDD RED) + `3b0fb40` (feat: TDD GREEN)
2. **Task 2: Batch + webhook API routes and wire QA into render pipeline** - `56f31a9` (feat)

## Files Created/Modified
- `src/deckforge/db/models/batch_job.py` - BatchJob model with total/completed/failed tracking
- `src/deckforge/db/models/webhook_registration.py` - WebhookRegistration with URL, events, HMAC secret
- `src/deckforge/db/repositories/batch.py` - BatchRepository with atomic increment_completed/increment_failed
- `src/deckforge/db/repositories/webhook.py` - WebhookRepository with get_by_event filtering
- `src/deckforge/api/routes/batch.py` - POST /v1/batch/render, POST /v1/batch/variations, GET /v1/batch/{id}
- `src/deckforge/api/routes/webhooks.py` - POST/GET/DELETE /v1/webhooks CRUD with event validation
- `src/deckforge/api/schemas/batch_schemas.py` - BatchRenderRequest, BatchVariationsRequest, BatchResponse
- `src/deckforge/api/schemas/webhook_schemas.py` - WebhookCreateRequest, WebhookResponse, WebhookListResponse
- `src/deckforge/workers/webhooks.py` - Enhanced with sign_webhook_payload and HMAC header injection
- `src/deckforge/workers/tasks.py` - render_pipeline returns (bytes, QAReport), batch/webhook integration
- `src/deckforge/api/routes/render.py` - Sync path includes quality_score and X-Quality-Score header
- `src/deckforge/api/app.py` - Batch and webhook routers registered
- `src/deckforge/db/models/job.py` - Added batch_id FK column
- `src/deckforge/db/repositories/job.py` - create() accepts batch_id parameter
- `alembic/versions/003_batch_webhook_tables.py` - Migration for batch_jobs, webhook_registrations, jobs.batch_id
- `tests/test_batch_webhooks.py` - 8 tests for HMAC signing, models, and repositories

## Decisions Made
- **Python-side event filtering for get_by_event:** JSON contains queries differ between SQLite and PostgreSQL. Loading all webhooks for the key and filtering in Python is portable and correct for the expected cardinality (few webhooks per key).
- **Webhook secret shown once:** The HMAC secret is returned only at creation time. List responses mask it (****last8chars) for security.
- **render_pipeline returns tuple:** Changed from `bytes` to `tuple[bytes, QAReport]` so all callers (sync, async, generate) get QA results. All existing callers updated to destructure.
- **Batch completion logic:** Uses `completed + failed >= total` check with status differentiation (complete, partial_failure, failed) based on failure count.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test assertions for SQLAlchemy mapped_column defaults**
- **Found during:** Task 1 (TDD GREEN)
- **Issue:** Tests asserted Python-level defaults (e.g., `batch.completed_items == 0`) but SQLAlchemy `mapped_column(default=X)` only applies at DB insert time, not Python construction
- **Fix:** Updated tests to pass explicit values matching the project's existing pattern (Job model behaves the same way)
- **Files modified:** tests/test_batch_webhooks.py
- **Verification:** All 8 tests pass
- **Committed in:** 3b0fb40 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor test adjustment to match SQLAlchemy convention used throughout the project. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 07 now fully complete (3/3 plans done)
- QA pipeline integrated into all render paths
- Batch operations and webhook subscriptions ready for production
- Ready for Phase 08 (deployment/packaging) if applicable

## Self-Check: PASSED

All 10 created files verified present. All 3 task commits (dcf3398, 3b0fb40, 56f31a9) verified in git log. 8/8 tests passing.

---
*Phase: 07-qa-pipeline-deck-operations*
*Completed: 2026-03-29*
