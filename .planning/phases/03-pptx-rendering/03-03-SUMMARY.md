---
phase: 03-pptx-rendering
plan: 03
subsystem: api
tags: [fastapi, pptx, streaming-response, thumbnail, libreoffice, pillow, pdf2image]

# Dependency graph
requires:
  - phase: 03-pptx-rendering/03-01
    provides: PptxRenderer orchestrator with element renderers
  - phase: 03-pptx-rendering/03-02
    provides: Native chart renderers for 9 chart types
  - phase: 02-layout-engine-theme-system
    provides: LayoutEngine, ThemeRegistry, TextMeasurer
provides:
  - render_pipeline() shared helper (IR -> LayoutEngine -> PptxRenderer -> bytes)
  - Sync render path for <=10 slides via StreamingResponse
  - Async worker task producing real PPTX (not stub JSON)
  - POST /v1/render/preview endpoint with base64 PNG thumbnails
  - Thumbnail generation with LibreOffice fallback
affects: [04-content-pipeline, 05-google-slides, 06-quality-pipeline]

# Tech tracking
tech-stack:
  added: [pdf2image (optional), libreoffice-impress (Docker), poppler-utils (Docker)]
  patterns: [sync-render-threshold, shared-render-pipeline, graceful-thumbnail-fallback]

key-files:
  created:
    - src/deckforge/rendering/thumbnail.py
    - src/deckforge/api/routes/preview.py
    - tests/unit/test_render_integration.py
    - tests/unit/test_preview_endpoint.py
  modified:
    - src/deckforge/workers/tasks.py
    - src/deckforge/api/routes/render.py
    - src/deckforge/api/schemas/responses.py
    - src/deckforge/api/app.py
    - pyproject.toml
    - Dockerfile

key-decisions:
  - "render_pipeline() as shared sync function callable from both API and worker"
  - "SYNC_RENDER_THRESHOLD=10 slides for sync vs async decision boundary"
  - "StreamingResponse with Content-Disposition for sync PPTX download"
  - "Graceful thumbnail fallback: Pillow placeholder when LibreOffice unavailable"
  - "pdf2image as optional dependency group (preview extra)"

patterns-established:
  - "Sync render path: <=10 slides rendered in API process, returned as StreamingResponse"
  - "Async render path: >10 slides enqueued to ARQ worker with S3 upload"
  - "Thumbnail fallback chain: LibreOffice -> pdf2image -> Pillow placeholder"

requirements-completed: [API-01, API-03]

# Metrics
duration: 6min
completed: 2026-03-29
---

# Phase 3 Plan 3: Render Pipeline Integration Summary

**Full PPTX render pipeline wired end-to-end with sync render for <=10 slides, async worker for larger decks, and PNG thumbnail preview endpoint with LibreOffice fallback**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-29T01:57:29Z
- **Completed:** 2026-03-29T02:03:54Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Worker task now runs full render pipeline (IR -> LayoutEngine -> PptxRenderer) producing real PPTX bytes instead of stub JSON
- POST /v1/render returns .pptx file directly as StreamingResponse for <=10-slide presentations (sync path)
- POST /v1/render/preview returns base64-encoded PNG thumbnails with graceful LibreOffice fallback
- All 135 Phase 3 tests pass (24 integration + preview tests added in this plan)
- End-to-end smoke test: 2-slide presentation -> 34KB valid PPTX file

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire render pipeline into worker task and add sync render path** - `1300a7c` (feat)
2. **Task 2: Preview endpoint and thumbnail generation** - `0b0f050` (feat)

## Files Created/Modified
- `src/deckforge/workers/tasks.py` - Full render pipeline replacing stub; render_pipeline() shared helper
- `src/deckforge/api/routes/render.py` - Sync path (<=10 slides) + async path (>10 slides)
- `src/deckforge/rendering/thumbnail.py` - PPTX to PNG via LibreOffice with Pillow fallback
- `src/deckforge/api/routes/preview.py` - POST /v1/render/preview endpoint
- `src/deckforge/api/schemas/responses.py` - PreviewResponse and ThumbnailItem schemas
- `src/deckforge/api/app.py` - Preview router registration
- `pyproject.toml` - pdf2image optional dependency group
- `Dockerfile` - LibreOffice and poppler-utils for production thumbnails
- `tests/unit/test_render_integration.py` - 11 pipeline integration tests
- `tests/unit/test_preview_endpoint.py` - 13 preview/thumbnail tests

## Decisions Made
- Used `render_pipeline()` as a standalone sync function shared between the API sync path and the async worker task, avoiding code duplication
- Set SYNC_RENDER_THRESHOLD at 10 slides to balance response time vs server load
- Used FastAPI StreamingResponse with Content-Disposition header for direct PPTX download
- Thumbnail generation uses a 3-tier fallback chain: LibreOffice headless -> pdf2image -> Pillow placeholder PNGs
- Added pdf2image as optional `[preview]` dependency group to keep base install lightweight
- Chart element IR uses `chart_data` field (not `content`) with top-level categories/series per chart type schema

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed chart element IR structure in tests**
- **Found during:** Task 1 (integration test creation)
- **Issue:** Test helper used `content.data.categories/series` structure but ChartElement uses `chart_data.categories/series` at top level
- **Fix:** Updated `_chart_slide()` helper to use correct `chart_data` field with `categories` and `series` at top level
- **Files modified:** tests/unit/test_render_integration.py
- **Verification:** All integration tests pass
- **Committed in:** 1300a7c (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Test-only fix, no scope change.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 3 (PPTX Rendering) is now complete with all 3 plans done
- Full rendering pipeline operational: IR -> Layout -> PPTX with sync and async paths
- Preview endpoint available for thumbnail generation
- Ready for Phase 4 (Content Pipeline) and Phase 5 (Google Slides) which both depend on Phase 3

## Self-Check: PASSED

- All 9 key files verified present on disk
- Commit 1300a7c (Task 1) verified in git log
- Commit 0b0f050 (Task 2) verified in git log
- 135 Phase 3 tests pass (1 skipped: LibreOffice integration)

---
*Phase: 03-pptx-rendering*
*Completed: 2026-03-29*
