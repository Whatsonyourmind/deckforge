---
phase: 07-qa-pipeline-deck-operations
plan: 02
subsystem: api
tags: [fastapi, crud, deck-mutations, cost-estimation, pydantic, sqlalchemy]

requires:
  - phase: 01-foundation-ir-schema
    provides: Presentation IR model, DeckRepository, DB models
  - phase: 03-pptx-rendering
    provides: render_pipeline() for re-rendering after mutations
provides:
  - Deck CRUD endpoints (list, get, get IR, soft delete)
  - Deck mutation endpoints (append, replace, reorder, retheme, export)
  - DeckOperations service with composable IR mutations
  - CostEstimator service with base + surcharge credit pricing
  - POST /v1/estimate endpoint for pre-render cost estimation
  - Extended DeckRepository (list_by_api_key, count_by_api_key, soft_delete, update_ir_snapshot)
affects: [08-deployment, api-tests, billing-integration]

tech-stack:
  added: []
  patterns: [services-layer, composable-ir-mutations, cost-estimation-model]

key-files:
  created:
    - src/deckforge/services/__init__.py
    - src/deckforge/services/deck_ops.py
    - src/deckforge/services/cost_estimator.py
    - src/deckforge/api/routes/decks.py
    - src/deckforge/api/routes/estimate.py
    - src/deckforge/api/schemas/deck_schemas.py
    - tests/unit/test_deck_ops.py
  modified:
    - src/deckforge/db/repositories/deck.py
    - src/deckforge/api/app.py

key-decisions:
  - "Stateless DeckOperations class operating on IR dicts with Presentation.model_validate() re-validation"
  - "CostEstimator uses ceil(slides/10) base + per-type surcharges (finance 0.5, chart 0.2, NL +2)"
  - "Prompt-based estimation assumes 10 slides with NL surcharge as conservative default"
  - "Mutation endpoints re-render via render_pipeline() and update ir_snapshot in-place"

patterns-established:
  - "Services layer pattern: stateless classes in src/deckforge/services/ for business logic"
  - "IR mutation pattern: deep copy, mutate, validate via Presentation.model_validate(), return"
  - "Deck ownership verification: _get_owned_deck helper checks existence + api_key_id match"

requirements-completed: [DECK-01, DECK-02, DECK-03, DECK-04, DECK-05, DECK-06, DECK-07, API-04]

duration: 6min
completed: 2026-03-29
---

# Phase 07 Plan 02: Deck CRUD + Mutation Operations Summary

**Deck CRUD with composable IR mutations (append/replace/reorder/retheme), re-export, and credit cost estimation via CostEstimator service**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-29T03:17:07Z
- **Completed:** 2026-03-29T03:23:27Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- CostEstimator with base credits (ceil(slides/10)) plus finance, chart, and NL generation surcharges
- DeckOperations service with append, replace, reorder, retheme mutations and IR re-validation
- Full deck CRUD API: list (paginated), get detail, get IR, soft delete
- Mutation endpoints that modify IR, re-validate, re-render, and persist updated snapshots
- POST /v1/estimate endpoint supporting both IR-based and prompt-based cost estimation
- 18 unit tests covering all cost estimation scenarios and mutation operations

## Task Commits

Each task was committed atomically:

1. **Task 1: Deck operations service and cost estimator** - `c785e89` (test: RED), `a8650df` (feat: GREEN)
2. **Task 2: Deck CRUD + mutation API routes and estimate endpoint** - `36155bc` (feat)

## Files Created/Modified
- `src/deckforge/services/__init__.py` - Services layer package init
- `src/deckforge/services/cost_estimator.py` - CostEstimator with FINANCE_TYPES set and surcharge model
- `src/deckforge/services/deck_ops.py` - DeckOperations with append/replace/reorder/retheme/re_render
- `src/deckforge/api/routes/decks.py` - 9 deck endpoints (CRUD + mutations + export)
- `src/deckforge/api/routes/estimate.py` - POST /v1/estimate endpoint
- `src/deckforge/api/schemas/deck_schemas.py` - Request/response models for all deck operations
- `src/deckforge/db/repositories/deck.py` - Extended with list_by_api_key, count_by_api_key, soft_delete, update_ir_snapshot
- `src/deckforge/api/app.py` - Wired decks_router and estimate_router into FastAPI app
- `tests/unit/test_deck_ops.py` - 18 unit tests for CostEstimator and DeckOperations

## Decisions Made
- Stateless DeckOperations class: all methods accept and return IR dicts, using deep copy to avoid mutation side effects
- CostEstimator pricing model: ceil(slides/10) base + 0.5 per finance slide + 0.2 per chart element + 2 for NL generation
- Prompt-based estimation assumes 10 default slides with NL surcharge (conservative)
- Mutation endpoints re-render synchronously via render_pipeline() -- async path can be added for large decks later
- Deck ownership verified by matching api_key_id on the deck record

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed slide_type discriminator tag in test helper**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** Test helper used `"title"` as slide_type but IR discriminated union requires `"title_slide"`
- **Fix:** Changed default slide_type to `"title_slide"` and removed non-existent `title` field from test slide dicts
- **Files modified:** tests/unit/test_deck_ops.py
- **Verification:** All 18 tests pass
- **Committed in:** a8650df (part of Task 1 GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor test fixture correction. No scope creep.

## Issues Encountered
None beyond the discriminator tag fix above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All deck CRUD and mutation endpoints registered and functional
- Cost estimation available for billing integration
- Ready for Phase 07 Plan 03 or Phase 08 deployment
- Services layer pattern established for future business logic

## Self-Check: PASSED

All 8 created files verified on disk. All 3 commit hashes (c785e89, a8650df, 36155bc) confirmed in git log.

---
*Phase: 07-qa-pipeline-deck-operations*
*Completed: 2026-03-29*
