---
phase: 08-typescript-sdk-billing-launch
plan: 01
subsystem: sdk
tags: [typescript, sdk, npm, tsup, vitest, sse, builder-pattern, fluent-api]

# Dependency graph
requires:
  - phase: 01-foundation-ir-schema
    provides: "IR Pydantic models that SDK types mirror"
  - phase: 07-qa-pipeline-deck-operations
    provides: "Deck operations and cost estimation API endpoints"
provides:
  - "@deckforge/sdk npm package with DeckForge client class"
  - "Fluent PresentationBuilder with immutable method chaining"
  - "Typed Slide, Element, Chart factory objects for all 32 slide types and 24 chart types"
  - "SSE streaming helper for generation progress events"
  - "Dual ESM/CJS build output ready for npm publish"
affects: [08-02-billing, 08-03-deployment]

# Tech tracking
tech-stack:
  added: [typescript ^5.5, tsup ^8.3, vitest ^2.1]
  patterns: [immutable-builder, factory-objects, discriminated-unions, sse-fetch-streaming]

key-files:
  created:
    - sdk/package.json
    - sdk/tsconfig.json
    - sdk/tsup.config.ts
    - sdk/src/index.ts
    - sdk/src/client.ts
    - sdk/src/types.ts
    - sdk/src/errors.ts
    - sdk/src/streaming.ts
    - sdk/src/builder/presentation.ts
    - sdk/src/builder/slides.ts
    - sdk/src/builder/elements.ts
    - sdk/tests/client.test.ts
    - sdk/tests/builder.test.ts
  modified: []

key-decisions:
  - "Hand-written TypeScript types mirroring Pydantic IR models (no OpenAPI codegen dependency)"
  - "Immutable builder pattern -- all mutation methods return new instances"
  - "fetch + ReadableStream for SSE (not EventSource) to support Authorization headers"
  - "Slide factory covers all 32 types with typed inputs that construct correct element arrays"
  - "Chart factory covers all 24 chart types with typed constructor functions"
  - "Exports ordering: types first for correct TypeScript resolution"

patterns-established:
  - "Immutable builder: PresentationBuilder returns new instance on every method call"
  - "Factory objects: Slide.*, Element.*, Chart.* as const objects with typed methods"
  - "SSE streaming: fetch + ReadableStream + manual line parsing for event-stream"
  - "Error hierarchy: DeckForgeError base with status-specific subclasses"

requirements-completed: [SDK-01, SDK-02, SDK-03, SDK-04, SDK-05]

# Metrics
duration: 6min
completed: 2026-03-29
---

# Phase 08 Plan 01: TypeScript SDK Summary

**@deckforge/sdk with DeckForge client, fluent PresentationBuilder, 32 slide factories, 24 chart factories, and SSE streaming helper -- 67 tests passing, dual ESM/CJS build**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-29T07:53:26Z
- **Completed:** 2026-03-29T07:59:45Z
- **Tasks:** 2
- **Files modified:** 15

## Accomplishments
- DeckForge client class with typed methods for render, estimate, getJob, decks.*, and generate.* (start + stream)
- Fluent PresentationBuilder with immutable method chaining producing validated PresentationIR
- Complete Slide factory covering all 32 slide types (23 universal + 9 finance) with typed inputs
- Element factory (20+ helpers) and Chart factory (24 chart types) for composable slide building
- SSE streaming helper using fetch + ReadableStream with Last-Event-ID reconnection
- Typed error hierarchy mapping HTTP status codes to specific error classes with retry logic
- 67 tests across client, builder, slide factories, element factories, chart factories, and SSE parsing

## Task Commits

Each task was committed atomically:

1. **Task 1: SDK project scaffold, OpenAPI type generation, and core client** - `df18e0c` (feat)
2. **Task 2: Fluent builder API and SSE streaming helper** - `163cc93` (feat)

## Files Created/Modified
- `sdk/package.json` - @deckforge/sdk npm package config with dual ESM/CJS exports
- `sdk/tsconfig.json` - TypeScript strict mode, ES2022 target, bundler resolution
- `sdk/tsup.config.ts` - tsup build config for ESM + CJS + dts output
- `sdk/.gitignore` - node_modules, dist, coverage exclusions
- `sdk/src/index.ts` - Re-exports all SDK public API (DeckForge, Presentation, Slide, Element, Chart, StreamingHelper)
- `sdk/src/types.ts` - 829-line hand-written IR types matching Python Pydantic models
- `sdk/src/errors.ts` - Error hierarchy (DeckForgeError, AuthenticationError, ValidationError, RateLimitError, etc.)
- `sdk/src/client.ts` - DeckForge class with _fetch, retry, render, estimate, decks.*, generate.*
- `sdk/src/streaming.ts` - SSE streaming via fetch + ReadableStream, parseSSELine utility
- `sdk/src/builder/presentation.ts` - PresentationBuilder with immutable create/theme/metadata/addSlide/build
- `sdk/src/builder/slides.ts` - Slide factory object with 32 typed slide constructors
- `sdk/src/builder/elements.ts` - Element (20+ types) and Chart (24 types) factory objects
- `sdk/tests/client.test.ts` - 18 tests: constructor, API routing, headers, error mapping, retry
- `sdk/tests/builder.test.ts` - 49 tests: builder, slides, elements, charts, SSE parsing

## Decisions Made
- Hand-written TypeScript types instead of OpenAPI codegen -- provides immediate type safety without build-time dependency on OpenAPI spec generation
- Immutable builder pattern (each method returns new instance) -- enables branching presentations without side effects
- fetch + ReadableStream for SSE instead of EventSource -- EventSource cannot set Authorization headers
- Slide factory constructs complete element arrays from simple typed inputs -- users never manually build element discriminated unions
- Chart factory maps 1:1 to all 24 chart_type discriminators in the IR schema
- Fixed package.json exports field ordering: types before import/require for correct Node.js + TypeScript resolution

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed package.json exports condition ordering**
- **Found during:** Task 2 (build verification)
- **Issue:** "types" condition after "import" and "require" causes tsup/esbuild warning and could affect TypeScript resolution
- **Fix:** Moved "types" to first position in exports conditions
- **Files modified:** sdk/package.json
- **Verification:** Clean build with no warnings
- **Committed in:** 163cc93 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor fix for correct npm package resolution. No scope creep.

## Issues Encountered
None -- previous attempt had left partial scaffold files (types, errors, client) which were complete and correct, allowing Task 1 to focus on adding tests and verifying.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- SDK package complete and buildable, ready for npm publish
- All types, builders, and client methods in place for Phase 08 Plans 02-03 (billing, deployment)
- 67 tests provide regression safety for future SDK changes

## Self-Check: PASSED

- All 14 created files exist on disk
- Commit df18e0c (Task 1) verified in git log
- Commit 163cc93 (Task 2) verified in git log
- 67/67 tests passing
- tsup build produces dist/index.js, dist/index.cjs, dist/index.d.ts
- TypeScript strict mode: zero errors

---
*Phase: 08-typescript-sdk-billing-launch*
*Completed: 2026-03-29*
