---
phase: 11-production-launch
plan: 02
subsystem: testing
tags: [bash, python, docker, smoke-test, pptx-validation, ci-scripts]

# Dependency graph
requires:
  - phase: 03-pptx-rendering
    provides: render_pipeline producing .pptx bytes from IR
  - phase: 10-zero-budget-growth-engine
    provides: 5 demo deck IRs in demos/ directory
provides:
  - Docker Compose service health verification script
  - End-to-end render pipeline smoke test
  - Demo deck IR validation and rendering script
  - CI-compatible verification suite (exit codes 0/1)
affects: [11-03-deployment-ci-cd]

# Tech tracking
tech-stack:
  added: []
  patterns: [bash-health-check, pptx-pk-header-validation, dual-mode-python-script]

key-files:
  created:
    - scripts/verify-docker.sh
    - scripts/smoke-test.sh
    - scripts/validate-demos.py
  modified: []

key-decisions:
  - "Smoke test IR uses actual schema types (title_slide, bullet_points, two_column_text) with elements array matching Presentation model"
  - "Render endpoint body is raw Presentation JSON (not wrapped in presentation key)"
  - "validate-demos.py uses render_pipeline directly in --direct mode to avoid server dependency"
  - "Docker verify uses grep-based service detection for portability across Compose v1/v2"

patterns-established:
  - "PK header validation: read first 2 bytes, compare to b'PK' for PPTX/ZIP verification"
  - "Dual-mode scripts: API mode for integration testing, direct mode for unit-level verification"

requirements-completed: [LAUNCH-05, LAUNCH-06, LAUNCH-07]

# Metrics
duration: 3min
completed: 2026-03-29
---

# Phase 11 Plan 02: Verification Scripts Summary

**Docker health verification, end-to-end render smoke test, and 5-demo IR validation scripts for CI-compatible production readiness checking**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-29T21:19:57Z
- **Completed:** 2026-03-29T21:23:06Z
- **Tasks:** 2
- **Files created:** 3

## Accomplishments
- Created Docker Compose verification script checking all 6 services (api, content-worker, render-worker, postgres, redis, minio) with infrastructure health probes
- Created end-to-end smoke test that sends a 3-slide IR to /v1/render and validates the .pptx output (PK zip header, >5KB file size)
- Created demo deck validation script supporting both API mode and direct render mode for all 5 demo IRs

## Task Commits

Each task was committed atomically:

1. **Task 1: Docker Compose verification and end-to-end smoke test scripts** - `314595f` (feat)
2. **Task 2: Demo deck validation script** - `3d581aa` (feat)

## Files Created/Modified
- `scripts/verify-docker.sh` - Checks all 6 Docker Compose services running, PostgreSQL/Redis health, API health endpoint with retry logic
- `scripts/smoke-test.sh` - End-to-end render pipeline test: health check, API key verification, 3-slide IR render with .pptx validation, optional generate test
- `scripts/validate-demos.py` - Validates all 5 demo deck IRs against Pydantic schema, renders via API or direct render_pipeline, verifies .pptx output

## Decisions Made
- Used grep-based service detection in verify-docker.sh instead of JSON parsing for portability across Docker Compose v1 and v2 (different JSON output formats)
- Smoke test IR body uses actual Presentation schema types (title_slide, bullet_points, two_column_text with elements array) matching the real schema, not simplified names
- validate-demos.py uses render_pipeline from deckforge.workers.tasks in direct mode, which already orchestrates layout engine, PPTX renderer, and QA pipeline
- Render endpoint receives raw Presentation JSON (not wrapped), matching the FastAPI body: Presentation signature

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected IR body structure in smoke-test.sh**
- **Found during:** Task 1 (smoke test creation)
- **Issue:** Plan's suggested IR body used simplified field names (slide_type: "title", "bullets", "two_column") and field-based properties (title, subtitle, bullets) that don't match the actual Pydantic schema
- **Fix:** Used correct slide types (title_slide, bullet_points, two_column_text) with elements array containing typed element objects (type: text, role: title/subtitle/body)
- **Files modified:** scripts/smoke-test.sh
- **Verification:** IR structure matches demos/mckinsey-strategy/ir.json pattern and Presentation.model_validate() contract

**2. [Rule 1 - Bug] Corrected API body shape in smoke-test.sh and validate-demos.py**
- **Found during:** Task 1 and Task 2
- **Issue:** Plan suggested wrapping IR in {"presentation": ir_data} for API calls, but render endpoint accepts Presentation object directly as body
- **Fix:** POST body is the raw IR JSON (the Presentation object), not wrapped
- **Files modified:** scripts/smoke-test.sh, scripts/validate-demos.py
- **Verification:** Matches render route signature: body: Presentation

---

**Total deviations:** 2 auto-fixed (2 bugs in plan's suggested code)
**Impact on plan:** Both fixes necessary for correctness. Without them, the render endpoint would reject the payload with 422 validation errors. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 3 verification scripts ready for CI/CD integration in 11-03
- Scripts can be referenced in GitHub Actions workflows for automated verification
- verify-docker.sh and smoke-test.sh are immediately usable for local development verification

## Self-Check: PASSED

- [x] scripts/verify-docker.sh exists
- [x] scripts/smoke-test.sh exists
- [x] scripts/validate-demos.py exists
- [x] Commit 314595f exists (Task 1)
- [x] Commit 3d581aa exists (Task 2)

---
*Phase: 11-production-launch*
*Completed: 2026-03-29*
