# Roadmap: DeckForge

## Overview

DeckForge delivers an API-first presentation generation platform in eight phases, following the dependency chain from IR schema (the backbone) through rendering engines, content intelligence, and quality assurance, to SDK and billing that wrap a working product. The IR schema must exist before any renderer; PPTX rendering proves the pipeline before Google Slides duplicates it; the layout engine addresses the highest R&D risk early; content generation develops after rendering is proven; charts and finance build on renderer infrastructure; QA validates the complete pipeline; and SDK + billing ship last because they wrap a working product.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation + IR Schema** - Project infrastructure, IR Pydantic models, API skeleton, auth, async workers
- [ ] **Phase 2: Layout Engine + Theme System** - Constraint-based layout solver, 15 curated themes, brand kit overlay
- [ ] **Phase 3: PPTX Rendering** - python-pptx renderer for all 23 universal slide types with sync render endpoint
- [ ] **Phase 4: Content Generation Pipeline** - NL-to-IR via model-agnostic LLM orchestration with async generation
- [ ] **Phase 5: Chart Engine + Finance Vertical** - Native/static charts and all 9 finance-specific slide types
- [ ] **Phase 6: Google Slides Output** - Native Google Slides renderer with Sheets-backed editable charts
- [ ] **Phase 7: QA Pipeline + Deck Operations** - 5-pass quality assurance, auto-fix, deck composability, batch ops
- [ ] **Phase 8: TypeScript SDK + Billing + Launch** - npm SDK, Stripe billing, discovery endpoints, launch readiness

## Phase Details

### Phase 1: Foundation + IR Schema
**Goal**: A running API server with the complete IR schema that accepts, validates, and rejects slide payloads -- plus the async infrastructure that all later phases depend on
**Depends on**: Nothing (first phase)
**Requirements**: IR-01, IR-02, IR-03, IR-04, IR-05, IR-06, INFRA-01, INFRA-02, INFRA-03, INFRA-04, API-08, API-09, API-10, API-11, API-14, WORKER-01, WORKER-02, WORKER-03, WORKER-04, WORKER-05
**Success Criteria** (what must be TRUE):
  1. An API client can POST a valid IR JSON payload and receive a 200 response with the parsed IR echoed back; an invalid payload returns a descriptive 422 error
  2. An API client can authenticate with a dk_live_ or dk_test_ API key and receives 401 for missing/invalid keys
  3. Docker Compose brings up the full local stack (API + Redis + PostgreSQL + MinIO + workers) with a single command
  4. An async job submitted to the worker queue is picked up, executed, and its completion status is retrievable via the API
  5. The OpenAPI spec is auto-generated and accessible at /docs with all IR models documented
**Plans:** 3 plans

Plans:
- [ ] 01-01-PLAN.md -- Complete IR schema: 32 slide types, element types, chart subtypes, metadata, validation (Wave 1)
- [ ] 01-02-PLAN.md -- Infrastructure: Docker Compose, Dockerfile, SQLAlchemy models, Alembic, config (Wave 1)
- [ ] 01-03-PLAN.md -- API skeleton + auth + rate limiting + workers + OpenAPI + idempotency (Wave 2)

### Phase 2: Layout Engine + Theme System
**Goal**: Slides are positioned and styled by a constraint-based solver and theme definitions -- no hard-coded coordinates, content adapts to volume
**Depends on**: Phase 1
**Requirements**: LAYOUT-01, LAYOUT-02, LAYOUT-03, LAYOUT-04, LAYOUT-05, LAYOUT-06, THEME-01, THEME-02, THEME-03, THEME-04, THEME-05
**Success Criteria** (what must be TRUE):
  1. Given IR with varying content lengths, the layout solver produces different but visually correct element positions (short bullet list vs. long bullet list do not produce identical layouts)
  2. Text that exceeds its bounding box triggers the adaptive cascade: reduce font, reflow, then split to multiple slides -- never clips or overflows
  3. A theme YAML file fully controls colors, typography, and spacing of a rendered slide, and switching themes produces visually distinct but structurally identical output
  4. A brand kit overlay (custom colors, fonts, logo) merges on top of any theme and the logo appears in the specified position on every slide
  5. All text meets WCAG AA contrast ratios (4.5:1 for body text, 3:1 for large text) against its background
**Plans**: TBD

Plans:
- [ ] 02-01: TBD
- [ ] 02-02: TBD
- [ ] 02-03: TBD

### Phase 3: PPTX Rendering
**Goal**: A complete PPTX file with all 23 universal slide types renders correctly and opens in PowerPoint/LibreOffice without errors
**Depends on**: Phase 2
**Requirements**: PPTX-01, PPTX-02, PPTX-03, PPTX-04, PPTX-05, PPTX-06, PPTX-07, PPTX-08, API-01, API-03
**Success Criteria** (what must be TRUE):
  1. POST /v1/render with a 10-slide IR returns a downloadable .pptx file in under 3 seconds that opens without errors in PowerPoint
  2. All 23 universal slide types (title, agenda, bullets, two_column, chart, table, quote, image, etc.) render with correct element positioning from the layout engine
  3. Tables render with header/body/footer rows, proper alignment, and conditional formatting applied
  4. POST /v1/render/preview returns PNG thumbnail images of the first N slides
  5. Generated PPTX includes speaker notes and slide transitions as specified in the IR
**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD
- [ ] 03-03: TBD

### Phase 4: Content Generation Pipeline
**Goal**: A natural language prompt produces a complete, coherent presentation IR through multi-stage LLM orchestration
**Depends on**: Phase 3
**Requirements**: CONTENT-01, CONTENT-02, CONTENT-03, CONTENT-04, CONTENT-05, CONTENT-06, API-02, API-13
**Success Criteria** (what must be TRUE):
  1. POST /v1/generate with a plain English prompt returns a job ID, and SSE events stream intent-parsed, outline-generated, slides-expanded, and refinement-complete progress stages
  2. The generated IR produces a presentation with a logical narrative arc -- not a random sequence of slides but a structured argument
  3. A user can provide their own LLM API key (OpenAI, Anthropic, Google, or Ollama endpoint) and generation uses that model instead of the default
  4. Cross-slide consistency is enforced: no contradictory terminology, consistent tense and capitalization, no redundant slides
**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD

### Phase 5: Chart Engine + Finance Vertical
**Goal**: Data visualizations render as native editable charts (or static fallbacks), and all 9 finance-specific slide types produce institutional-grade output
**Depends on**: Phase 3
**Requirements**: CHART-01, CHART-02, CHART-03, CHART-04, CHART-05, FIN-01, FIN-02, FIN-03, FIN-04, FIN-05, FIN-06, FIN-07, FIN-08, FIN-09, FIN-10, FIN-11
**Success Criteria** (what must be TRUE):
  1. Bar, line, pie, scatter, combo, area, donut, radar, and funnel charts render as native editable charts in PPTX -- a user can click the chart in PowerPoint and modify the data
  2. Waterfall, heatmap, sankey, gantt, and football field charts render as high-resolution static images via Plotly and are visually indistinguishable from native charts at presentation scale
  3. A comp_table slide with EV/EBITDA and P/E multiples renders with median highlight, conditional formatting, and proper financial number formatting (1x, 2.5x, $1.2B)
  4. A DCF summary with sensitivity matrix, a waterfall chart with positive/negative coloring, and a deal overview one-pager all render correctly from structured IR input
  5. CSV or Excel file data can be ingested and auto-mapped to the appropriate finance slide type
**Plans**: TBD

Plans:
- [ ] 05-01: TBD
- [ ] 05-02: TBD
- [ ] 05-03: TBD

### Phase 6: Google Slides Output
**Goal**: The same IR that produces PPTX also produces a native Google Slides presentation with editable Sheets-backed charts
**Depends on**: Phase 5
**Requirements**: GSLIDES-01, GSLIDES-02, GSLIDES-03, GSLIDES-04, GSLIDES-05, GSLIDES-06
**Success Criteria** (what must be TRUE):
  1. Given the same IR, the Google Slides output contains the same content, layout, and styling as the PPTX output -- visual parity across formats
  2. Charts in Google Slides are backed by Google Sheets and a user can click through to edit the underlying data
  3. A user authenticates via OAuth 2.0 and the generated presentation appears in their Google Drive with a shareable URL
  4. Temporary Sheets spreadsheets created for chart data are cleaned up after chart creation completes
**Plans**: TBD

Plans:
- [ ] 06-01: TBD
- [ ] 06-02: TBD

### Phase 7: QA Pipeline + Deck Operations
**Goal**: Every deck passes automated quality checks before delivery, and users can compose, modify, and batch-process existing decks
**Depends on**: Phase 6
**Requirements**: QA-01, QA-02, QA-03, QA-04, QA-05, QA-06, QA-07, DECK-01, DECK-02, DECK-03, DECK-04, DECK-05, DECK-06, DECK-07, BATCH-01, BATCH-02, API-04, API-12
**Success Criteria** (what must be TRUE):
  1. A deck with intentional issues (clipped text, broken contrast, wrong totals) is auto-fixed before delivery -- the output file has no text overflow, all contrast ratios pass, and data totals are correct
  2. Every API response includes an executive readiness score (0-100) and a quality report detailing any issues found and fixes applied
  3. A user can append, replace, reorder, and retheme slides on an existing deck through the API and receive the modified deck
  4. POST /v1/estimate returns accurate credit cost for a given IR, and webhook callbacks fire on async job completion
  5. Batch render produces multiple decks (or theme variations of one deck) in a single request
**Plans**: TBD

Plans:
- [ ] 07-01: TBD
- [ ] 07-02: TBD
- [ ] 07-03: TBD

### Phase 8: TypeScript SDK + Billing + Launch
**Goal**: Developers can integrate DeckForge via a typed npm package, usage is metered and billed, and the API is publicly discoverable
**Depends on**: Phase 7
**Requirements**: SDK-01, SDK-02, SDK-03, SDK-04, SDK-05, BILL-01, BILL-02, BILL-03, BILL-04, BILL-05, BILL-06, API-05, API-06, API-07, INFRA-05
**Success Criteria** (what must be TRUE):
  1. A TypeScript developer can npm install @deckforge/sdk and generate a presentation using the fluent builder API (Presentation.create().addSlide(...).render()) with full type safety
  2. The SDK streams generation progress via an async generator and all types are auto-generated from the OpenAPI spec
  3. A new user signs up on Starter tier (free, 50 credits), generates decks, sees credit balance decrease, and hits the limit -- upgrade to Pro unlocks 500 credits with Stripe payment
  4. GET /v1/themes, /v1/slide-types, and /v1/capabilities return complete self-describing API metadata that an agent can use to discover what DeckForge can do
  5. Credit costs are estimated before generation (pre-flight reservation) and actual charges reflect surcharges for NL, finance, and Google Slides output
**Plans**: TBD

Plans:
- [ ] 08-01: TBD
- [ ] 08-02: TBD
- [ ] 08-03: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8
Note: Phase 4 and Phase 5 both depend on Phase 3 and could execute in parallel.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation + IR Schema | 1/3 | In Progress | - |
| 2. Layout Engine + Theme System | 0/3 | Not started | - |
| 3. PPTX Rendering | 0/3 | Not started | - |
| 4. Content Generation Pipeline | 0/2 | Not started | - |
| 5. Chart Engine + Finance Vertical | 0/3 | Not started | - |
| 6. Google Slides Output | 0/2 | Not started | - |
| 7. QA Pipeline + Deck Operations | 0/3 | Not started | - |
| 8. TypeScript SDK + Billing + Launch | 0/3 | Not started | - |
