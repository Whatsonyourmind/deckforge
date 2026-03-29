---
phase: 01-foundation-ir-schema
plan: 01
subsystem: ir
tags: [pydantic, discriminated-union, ir-schema, validation, python]

# Dependency graph
requires: []
provides:
  - "Complete IR Pydantic v2 schema with 32 slide types, 27 element types, 24 chart subtypes"
  - "SlideUnion, ElementUnion, ChartUnion discriminated unions"
  - "Presentation top-level model with metadata, brand_kit, generation_options"
  - "148 unit tests covering all IR types and validation"
  - "pyproject.toml with all project dependencies"
affects: [layout-engine, pptx-renderer, gslides-renderer, content-pipeline, qa-pipeline, api]

# Tech tracking
tech-stack:
  added: [pydantic>=2.12, fastapi>=0.135.2, uvicorn>=0.42.0, sqlalchemy>=2.0.48, arq>=0.26.1, redis>=5.0, boto3>=1.36, httpx>=0.28, pytest>=8.3, ruff>=0.9]
  patterns: [pydantic-discriminated-union, literal-type-discriminator, model-rebuild-for-forward-refs, src-layout-packaging]

key-files:
  created:
    - pyproject.toml
    - src/deckforge/ir/enums.py
    - src/deckforge/ir/elements/base.py
    - src/deckforge/ir/elements/text.py
    - src/deckforge/ir/elements/data.py
    - src/deckforge/ir/elements/visual.py
    - src/deckforge/ir/elements/layout.py
    - src/deckforge/ir/elements/__init__.py
    - src/deckforge/ir/charts/types.py
    - src/deckforge/ir/charts/__init__.py
    - src/deckforge/ir/slides/base.py
    - src/deckforge/ir/slides/universal.py
    - src/deckforge/ir/slides/finance.py
    - src/deckforge/ir/slides/__init__.py
    - src/deckforge/ir/metadata.py
    - src/deckforge/ir/brand_kit.py
    - src/deckforge/ir/presentation.py
    - src/deckforge/ir/validators.py
    - src/deckforge/ir/__init__.py
    - tests/unit/test_ir_elements.py
    - tests/unit/test_ir_charts.py
    - tests/unit/test_ir_slides.py
    - tests/unit/test_ir_validation.py
    - tests/unit/test_ir_metadata.py
  modified: []

key-decisions:
  - "Used Literal-based discriminators (not enum) for slide_type/type/chart_type to work with Pydantic v2 discriminated unions"
  - "Pinned redis<6 to resolve arq 0.27.0 dependency conflict (arq requires redis<6)"
  - "Used model_rebuild() pattern for forward references between slides->elements->charts hierarchy"
  - "Used build_backend = setuptools.build_meta (not legacy backend) for Python 3.14 compatibility"

patterns-established:
  - "Discriminated union: Annotated[Union[...], Field(discriminator='field_name')] for type routing"
  - "Module organization: enums.py, base.py, category files, __init__.py with Union + model_rebuild"
  - "Forward reference resolution: TYPE_CHECKING guard + model_rebuild() in __init__.py"
  - "Content model pattern: each element has a typed content model (HeadingContent, TableContent, etc.)"

requirements-completed: [IR-01, IR-02, IR-03, IR-04, IR-05, IR-06]

# Metrics
duration: 9min
completed: 2026-03-29
---

# Phase 1 Plan 1: IR Schema Summary

**Complete Pydantic v2 IR schema with 32 slide types, 27 element types, 24 chart subtypes using discriminated unions -- 148 tests passing, full OpenAPI JSON schema (127 definitions) generates cleanly**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-29T00:12:28Z
- **Completed:** 2026-03-29T00:21:45Z
- **Tasks:** 2
- **Files modified:** 24

## Accomplishments
- All 32 slide types (23 universal + 9 finance) validate via SlideUnion discriminated union
- All 27 element types (9 text + 7 data + 7 visual + 4 layout) validate via ElementUnion discriminated union
- All 24 chart subtypes validate via ChartUnion discriminated union with typed data schemas
- Presentation model composes metadata, brand_kit, theme, slides, generation_options with JSON round-trip
- Full OpenAPI-compatible JSON schema generates (127 definitions, ~141KB)
- 148 unit tests covering all types, validation errors, and edge cases

## Task Commits

Each task was committed atomically:

1. **Task 1: Project scaffold + IR enums, element types, chart types** - `f677651` (feat)
2. **Task 2: Slide types, Presentation model, metadata, validation** - `1a2a428` (feat)

_Both tasks followed TDD: RED (failing tests) -> GREEN (implementation) -> commit._

## Files Created/Modified
- `pyproject.toml` - Project config with all dependencies (Python >=3.12)
- `src/deckforge/ir/enums.py` - 14 enums: SlideType(32), ElementType(27), ChartType(24), etc.
- `src/deckforge/ir/elements/base.py` - BaseElement with Position model
- `src/deckforge/ir/elements/text.py` - 9 text element types with content models
- `src/deckforge/ir/elements/data.py` - 7 data element types (table, chart, kpi, etc.)
- `src/deckforge/ir/elements/visual.py` - 7 visual element types (image, icon, shape, etc.)
- `src/deckforge/ir/elements/layout.py` - 4 layout element types (container, column, row, grid_cell)
- `src/deckforge/ir/elements/__init__.py` - ElementUnion discriminated union + model_rebuild
- `src/deckforge/ir/charts/types.py` - 24 chart data models with ChartUnion
- `src/deckforge/ir/slides/base.py` - BaseSlide with elements, layout_hint, transition, speaker_notes
- `src/deckforge/ir/slides/universal.py` - 23 universal slide models
- `src/deckforge/ir/slides/finance.py` - 9 finance slide models with domain-specific fields
- `src/deckforge/ir/slides/__init__.py` - SlideUnion discriminated union + model_rebuild
- `src/deckforge/ir/metadata.py` - PresentationMetadata + GenerationOptions
- `src/deckforge/ir/brand_kit.py` - BrandColors, BrandFonts, LogoConfig, FooterConfig, BrandKit
- `src/deckforge/ir/presentation.py` - Top-level Presentation model with validators
- `src/deckforge/ir/__init__.py` - Public re-exports of all IR types
- `tests/unit/test_ir_elements.py` - 67 tests for element types and ElementUnion
- `tests/unit/test_ir_charts.py` - 34 tests for chart types and ChartUnion
- `tests/unit/test_ir_slides.py` - 50+ tests for slide types and SlideUnion
- `tests/unit/test_ir_validation.py` - Presentation model tests with JSON round-trip
- `tests/unit/test_ir_metadata.py` - Metadata, generation options, and brand kit tests

## Decisions Made
- Used Literal-based discriminators for Pydantic v2 discriminated unions (not enum values)
- Pinned redis<6 to resolve arq 0.27.0 dependency conflict
- Used model_rebuild() pattern for forward references in slide->element->chart hierarchy
- Used setuptools.build_meta backend (not legacy) for Python 3.14 compatibility

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed build backend for Python 3.14**
- **Found during:** Task 1 (dependency installation)
- **Issue:** `setuptools.backends._legacy:_Backend` does not exist in current setuptools
- **Fix:** Changed to `setuptools.build_meta`
- **Files modified:** pyproject.toml
- **Verification:** `pip install -e ".[dev]"` succeeds
- **Committed in:** f677651

**2. [Rule 3 - Blocking] Fixed redis version constraint for arq compatibility**
- **Found during:** Task 1 (dependency installation)
- **Issue:** arq 0.27.0 requires redis<6, but plan specified redis>=7.1.1
- **Fix:** Changed to `redis>=5.0,<6` and `arq>=0.26.1`
- **Files modified:** pyproject.toml
- **Verification:** All dependencies install cleanly
- **Committed in:** f677651

**3. [Rule 3 - Blocking] Added model_rebuild() for slide forward references**
- **Found during:** Task 2 (slide union validation)
- **Issue:** BaseSlide.elements uses forward ref to ElementUnion via TYPE_CHECKING; Pydantic cannot resolve
- **Fix:** Added model_rebuild() for all 32 slide models + BaseSlide in slides/__init__.py
- **Files modified:** src/deckforge/ir/slides/__init__.py
- **Verification:** All 148 tests pass, discriminated union works correctly
- **Committed in:** 1a2a428

---

**Total deviations:** 3 auto-fixed (all Rule 3 - blocking issues)
**Impact on plan:** All fixes necessary for correct operation. No scope creep.

## Issues Encountered
None beyond the auto-fixed blocking issues above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- IR schema is complete and fully tested -- the backbone for all downstream modules
- ElementUnion, SlideUnion, ChartUnion are ready for layout engine (Phase 2)
- Presentation model ready for API endpoint consumption
- JSON schema ready for OpenAPI documentation

## Self-Check: PASSED

- All 24 created files verified present on disk
- Commit f677651 (Task 1) verified in git history
- Commit 1a2a428 (Task 2) verified in git history
- 148/148 unit tests passing

---
*Phase: 01-foundation-ir-schema*
*Completed: 2026-03-29*
