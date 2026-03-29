---
phase: 04-content-generation-pipeline
plan: 02
subsystem: content, api
tags: [llm, pipeline, pydantic, sse, redis-pubsub, arq, fastapi, prompt-engineering]

# Dependency graph
requires:
  - phase: 04-01
    provides: LLMAdapter ABC, LLMRouter with fallback, CompletionResponse, LLMConfig
  - phase: 01-03
    provides: ARQ worker tasks, publish_progress, render_pipeline, API auth/rate-limit deps
  - phase: 03-03
    provides: render_pipeline synchronous rendering function
provides:
  - 4-stage content generation pipeline (IntentParser, Outliner, SlideWriter, CrossSlideRefiner)
  - ContentPipeline orchestrator producing valid Presentation IR from NL prompts
  - Prompt templates enforcing assertive headlines (<=8 words) and concise bullets (<=12 words)
  - POST /v1/generate endpoint accepting prompts and enqueuing to ARQ content queue
  - GET /v1/generate/{job_id}/stream SSE endpoint for real-time pipeline progress
  - GenerateRequest/GenerateResponse schemas with BYO API key support
  - Real generate_content worker task replacing the stub implementation
affects: [06-quality-assurance, 07-deployment, api-docs]

# Tech tracking
tech-stack:
  added: [sse-starlette]
  patterns: [4-stage LLM pipeline, structured output via complete_structured, progress callback pattern, SSE via Redis pub/sub]

key-files:
  created:
    - src/deckforge/content/__init__.py
    - src/deckforge/content/models.py
    - src/deckforge/content/intent_parser.py
    - src/deckforge/content/outliner.py
    - src/deckforge/content/slide_writer.py
    - src/deckforge/content/refiner.py
    - src/deckforge/content/pipeline.py
    - src/deckforge/content/prompts/__init__.py
    - src/deckforge/content/prompts/intent.py
    - src/deckforge/content/prompts/outline.py
    - src/deckforge/content/prompts/expand.py
    - src/deckforge/content/prompts/refine.py
    - src/deckforge/api/routes/generate.py
    - src/deckforge/api/schemas/requests.py
    - tests/unit/test_content_pipeline.py
    - tests/unit/test_generate_endpoint.py
  modified:
    - src/deckforge/api/schemas/responses.py
    - src/deckforge/api/app.py
    - src/deckforge/workers/tasks.py
    - tests/integration/test_workers.py

key-decisions:
  - "Local imports in generate_content worker task to avoid circular import with content.pipeline"
  - "Progress callback is async callable for Redis publish compatibility"
  - "SSE stream subscribes to Redis pub/sub channel with 120s server timeout and event IDs for reconnection"
  - "ExpandedSlide uses dict elements (not ElementUnion) to stay flexible before IR validation"
  - "Headline word count validated via field_validator in SlideOutline and ExpandedSlide models"

patterns-established:
  - "4-stage pipeline pattern: parse -> outline -> expand -> refine with progress callbacks"
  - "Prompt template pattern: SYSTEM_PROMPT + USER_TEMPLATE with Jinja-style f-string formatting"
  - "SSE streaming pattern: Redis pub/sub -> EventSourceResponse async generator"
  - "GenerateRequest schema pattern: prompt + optional generation_options + BYO llm_config"

requirements-completed: [CONTENT-01, CONTENT-02, CONTENT-03, CONTENT-04, API-02, API-13]

# Metrics
duration: 13min
completed: 2026-03-29
---

# Phase 04 Plan 02: Content Generation Pipeline Summary

**4-stage LLM pipeline (intent parser, outliner, slide writer, cross-slide refiner) with POST /v1/generate endpoint and SSE streaming via Redis pub/sub**

## Performance

- **Duration:** 13 min
- **Started:** 2026-03-29T02:33:03Z
- **Completed:** 2026-03-29T02:46:53Z
- **Tasks:** 2 (TDD: 4 commits total -- 2 RED, 2 GREEN)
- **Files modified:** 20

## Accomplishments
- Built complete 4-stage content generation pipeline transforming NL prompts to valid Presentation IR
- Prompt templates enforce consulting-quality constraints: assertive headlines (<=8 words), concise bullets (<=12 words), narrative arc frameworks (pyramid, SCR, MECE, chronological)
- POST /v1/generate endpoint with 202 async job pattern, BYO API key support, and ARQ content queue
- GET /v1/generate/{job_id}/stream SSE endpoint with Redis pub/sub, event IDs, and 120s timeout
- Replaced stub generate_content worker task with real ContentPipeline orchestration -> render_pipeline -> S3 upload
- 33 new tests (18 content pipeline + 15 endpoint) all passing with mocked LLM responses

## Task Commits

Each task was committed atomically (TDD: RED then GREEN):

1. **Task 1: Content pipeline models, 4 stages, and prompt templates**
   - `2af9a9d` (test) - RED: 18 failing tests for pipeline models and stages
   - `9fb2658` (feat) - GREEN: All 12 content package files implemented, 18 tests pass

2. **Task 2: POST /v1/generate endpoint, SSE streaming, and worker task integration**
   - `22292b5` (test) - RED: 15 failing tests for endpoint, SSE, and worker task
   - `87e3efc` (feat) - GREEN: Endpoint, schemas, worker task, app registration, 15 tests pass

## Files Created/Modified

### Created (16 files)
- `src/deckforge/content/__init__.py` - Package re-exports: ContentPipeline, models, stages
- `src/deckforge/content/models.py` - ParsedIntent, SlideOutline, PresentationOutline, ExpandedSlide, RefinedPresentation
- `src/deckforge/content/intent_parser.py` - IntentParser: NL prompt -> structured ParsedIntent via LLMRouter
- `src/deckforge/content/outliner.py` - Outliner: ParsedIntent -> PresentationOutline with narrative arc
- `src/deckforge/content/slide_writer.py` - SlideWriter: SlideOutline -> ExpandedSlide with IR elements
- `src/deckforge/content/refiner.py` - CrossSlideRefiner: All slides -> consistency checks + terminology unification
- `src/deckforge/content/pipeline.py` - ContentPipeline: Orchestrates all 4 stages with progress callbacks
- `src/deckforge/content/prompts/__init__.py` - Prompt templates package
- `src/deckforge/content/prompts/intent.py` - Intent parsing system/user prompts with few-shot example
- `src/deckforge/content/prompts/outline.py` - Outline generation prompts with narrative arc framework descriptions
- `src/deckforge/content/prompts/expand.py` - Slide expansion prompts with negative examples
- `src/deckforge/content/prompts/refine.py` - Cross-slide refinement prompts with review checklist
- `src/deckforge/api/routes/generate.py` - POST /v1/generate and GET /v1/generate/{job_id}/stream endpoints
- `src/deckforge/api/schemas/requests.py` - GenerateRequest with prompt, generation_options, llm_config
- `tests/unit/test_content_pipeline.py` - 18 tests: models, stages, pipeline e2e, prompt templates
- `tests/unit/test_generate_endpoint.py` - 15 tests: schemas, endpoint, SSE, worker task, app registration

### Modified (4 files)
- `src/deckforge/api/schemas/responses.py` - Added GenerateResponse and SSEProgressEvent models
- `src/deckforge/api/app.py` - Registered generate router under /v1 prefix
- `src/deckforge/workers/tasks.py` - Replaced stub generate_content with real ContentPipeline integration
- `tests/integration/test_workers.py` - Updated generate_content test to mock ContentPipeline

## Decisions Made
- **Local imports in generate_content**: Used local imports for ContentPipeline, create_router, LLMConfig, and GenerationOptions inside the worker task to avoid circular import issues (content -> ir -> elements chain)
- **Async progress callback**: Progress callback is an async callable `(stage, progress) -> None` to support direct Redis publish from within the pipeline
- **SSE with event IDs**: SSE stream includes incrementing event IDs for client reconnection support (Last-Event-ID header)
- **ExpandedSlide uses dict elements**: Elements are stored as `list[dict]` rather than `list[ElementUnion]` to keep flexibility -- the IR validation happens at the end via `Presentation.model_validate()`
- **Headline validation via field_validator**: Both SlideOutline and ExpandedSlide enforce <=8 word headlines using Pydantic field validators, catching violations at model creation time

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated integration test for new generate_content signature**
- **Found during:** Task 2 (worker task replacement)
- **Issue:** `tests/integration/test_workers.py::test_generate_content_produces_ir_and_publishes_progress` was written for the old stub and failed because the real implementation calls `create_router()` which needs LLM API keys
- **Fix:** Updated test to mock ContentPipeline and create_router, verifying pipeline is called and progress is published
- **Files modified:** tests/integration/test_workers.py
- **Verification:** All 8 integration worker tests pass
- **Committed in:** 87e3efc (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug fix)
**Impact on plan:** Necessary fix for test compatibility after replacing the stub. No scope creep.

## Issues Encountered
- Mock paths for worker task tests required patching at the actual import location (`deckforge.content.pipeline.ContentPipeline`) rather than the consuming module because the imports are local to the function body. Resolved by using the correct module paths in `unittest.mock.patch`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Content generation pipeline is complete and wired end-to-end
- Phase 4 fully done: LLM adapters (04-01) + content pipeline (04-02)
- Ready for Phase 6 (quality assurance) or Phase 7 (deployment)
- All 66 Phase 4 tests pass, no regressions in the 604 unit test suite

---
*Phase: 04-content-generation-pipeline*
*Completed: 2026-03-29*
