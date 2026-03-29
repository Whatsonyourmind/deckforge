# Roadmap: DeckForge

## Overview

DeckForge delivers an API-first presentation generation platform in eight phases, following the dependency chain from IR schema (the backbone) through rendering engines, content intelligence, and quality assurance, to SDK and billing that wrap a working product. The IR schema must exist before any renderer; PPTX rendering proves the pipeline before Google Slides duplicates it; the layout engine addresses the highest R&D risk early; content generation develops after rendering is proven; charts and finance build on renderer infrastructure; QA validates the complete pipeline; and SDK + billing ship last because they wrap a working product.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation + IR Schema** - Project infrastructure, IR Pydantic models, API skeleton, auth, async workers (completed 2026-03-29)
- [x] **Phase 2: Layout Engine + Theme System** - Constraint-based layout solver, 15 curated themes, brand kit overlay (completed 2026-03-29)
- [x] **Phase 3: PPTX Rendering** - python-pptx renderer for all 23 universal slide types with sync render endpoint (completed 2026-03-29)
- [x] **Phase 4: Content Generation Pipeline** - NL-to-IR via model-agnostic LLM orchestration with async generation (completed 2026-03-29)
- [x] **Phase 5: Chart Engine + Finance Vertical** - Native/static charts and all 9 finance-specific slide types (completed 2026-03-29)
- [x] **Phase 6: Google Slides Output** - Native Google Slides renderer with Sheets-backed editable charts (completed 2026-03-29)
- [x] **Phase 7: QA Pipeline + Deck Operations** - 5-pass quality assurance, auto-fix, deck composability, batch ops (completed 2026-03-29)
- [x] **Phase 8: TypeScript SDK + Billing + Launch** - npm SDK, Stripe billing, discovery endpoints, launch readiness (completed 2026-03-29)
- [x] **Phase 9: Monetization and Go-To-Market** - x402 machine payments, Unkey API keys, MCP server, landing page, npm SDK publishing, analytics (completed 2026-03-29)
- [x] **Phase 10: Zero-Budget Growth Engine** - MCP directory listings, content marketing, demo decks, agent framework integrations, finance community outreach (completed 2026-03-29)
- [ ] **Phase 11: Production Launch** - README, .env, bootstrap scripts, verification, CI/CD, deployment docs, Stripe/Unkey/x402 setup

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
**Plans:** 3/3 plans complete

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
**Plans:** 3/3 plans complete

Plans:
- [x] 02-01-PLAN.md -- Layout foundation: types, 12-column grid system, kiwisolver wrapper, Pillow text measurer (Wave 1)
- [x] 02-02-PLAN.md -- Theme system: 15 YAML themes, variable resolver, brand kit merger, WCAG contrast checker (Wave 1)
- [x] 02-03-PLAN.md -- Layout patterns for all 32 slide types, adaptive overflow handler, LayoutEngine orchestrator (Wave 2)

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
**Plans:** 3 plans

Plans:
- [ ] 03-01-PLAN.md -- Core PPTX renderer: element renderers (text, table, image, shape, data viz), PptxRenderer orchestrator, transitions, speaker notes (Wave 1)
- [ ] 03-02-PLAN.md -- Native editable chart rendering: bar, line, area, pie, donut, scatter, bubble, combo, radar via python-pptx (Wave 1)
- [ ] 03-03-PLAN.md -- Wire into API: sync render for <=10 slides, preview endpoint with PNG thumbnails, worker task integration (Wave 2)

### Phase 4: Content Generation Pipeline
**Goal**: A natural language prompt produces a complete, coherent presentation IR through multi-stage LLM orchestration
**Depends on**: Phase 3
**Requirements**: CONTENT-01, CONTENT-02, CONTENT-03, CONTENT-04, CONTENT-05, CONTENT-06, API-02, API-13
**Success Criteria** (what must be TRUE):
  1. POST /v1/generate with a plain English prompt returns a job ID, and SSE events stream intent-parsed, outline-generated, slides-expanded, and refinement-complete progress stages
  2. The generated IR produces a presentation with a logical narrative arc -- not a random sequence of slides but a structured argument
  3. A user can provide their own LLM API key (OpenAI, Anthropic, Google, or Ollama endpoint) and generation uses that model instead of the default
  4. Cross-slide consistency is enforced: no contradictory terminology, consistent tense and capitalization, no redundant slides
**Plans:** 2 plans

**Plans:** 2/2 plans complete

Plans:
- [x] 04-01-PLAN.md -- LLM adapters: abstract base, Claude/OpenAI/Gemini/Ollama implementations, router with fallback chains, BYO key support (Wave 1)
- [x] 04-02-PLAN.md -- Content pipeline: intent parser, outliner, slide writer, cross-slide refiner, prompt templates, POST /v1/generate with SSE streaming (Wave 2)

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
**Plans:** 3 plans

Plans:
- [x] 05-01-PLAN.md -- Static chart engine: Plotly renderers for waterfall, heatmap, sankey, gantt, football field, sensitivity, funnel, treemap, tornado, sunburst + chart recommender (Wave 1)
- [ ] 05-02-PLAN.md -- Finance data layer: financial number formatter, conditional formatting engine, CSV/Excel data ingestion with auto-mapping (Wave 1)
- [ ] 05-03-PLAN.md -- Finance slide renderers: comp_table, dcf_summary, waterfall_chart, deal_overview, returns_analysis, capital_structure, market_landscape, investment_thesis, risk_matrix + PptxRenderer integration (Wave 2)

### Phase 6: Google Slides Output
**Goal**: The same IR that produces PPTX also produces a native Google Slides presentation with editable Sheets-backed charts
**Depends on**: Phase 5
**Requirements**: GSLIDES-01, GSLIDES-02, GSLIDES-03, GSLIDES-04, GSLIDES-05, GSLIDES-06
**Success Criteria** (what must be TRUE):
  1. Given the same IR, the Google Slides output contains the same content, layout, and styling as the PPTX output -- visual parity across formats
  2. Charts in Google Slides are backed by Google Sheets and a user can click through to edit the underlying data
  3. A user authenticates via OAuth 2.0 and the generated presentation appears in their Google Drive with a shareable URL
  4. Temporary Sheets spreadsheets created for chart data are cleaned up after chart creation completes
**Plans:** 2 plans

Plans:
- [ ] 06-01-PLAN.md -- Google Slides renderer core: EMU converter, batchUpdate request builders for all element types + finance slides, OAuth handler, GoogleSlidesRenderer orchestrator (Wave 1)
- [ ] 06-02-PLAN.md -- Sheets-backed charts + API integration: SheetsChartBuilder for editable charts, temp spreadsheet cleanup, OAuth endpoints, output_format=gslides on /v1/render (Wave 2)

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
**Plans:** 3 plans

Plans:
- [ ] 07-01-PLAN.md -- 5-pass QA pipeline: structural, text, visual, data, brand checkers + auto-fix engine + executive readiness scorer (Wave 1)
- [ ] 07-02-PLAN.md -- Deck operations: CRUD endpoints, append/replace/reorder/retheme mutations, cost estimation endpoint (Wave 1)
- [ ] 07-03-PLAN.md -- Batch render/variations with ARQ fan-out, webhook registration with HMAC signing, wire QA into render pipeline (Wave 2)

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
**Plans:** 3/3 plans complete

Plans:
- [x] 08-01-PLAN.md -- TypeScript SDK: project scaffold, OpenAPI type generation, DeckForge client, fluent builder API, SSE streaming helper (Wave 1)
- [x] 08-02-PLAN.md -- Stripe billing: tier definitions, credit reservation/deduction/release, Stripe subscriptions + metering, usage dashboard, credit middleware (Wave 1)
- [x] 08-03-PLAN.md -- Discovery endpoints (/v1/themes, /v1/slide-types, /v1/capabilities), slide type registry, production Dockerfile, Fly.io deployment config (Wave 2)

### Phase 9: Monetization and Go-To-Market
**Goal:** DeckForge is discoverable, purchasable, and payable by both humans (Stripe subscriptions) and AI agents (x402 machine payments in USDC) -- with landing page, MCP server, npm SDK published, and dual revenue streams active
**Depends on:** Phase 8
**Requirements**: GTM-01, GTM-02, GTM-03, GTM-04, GTM-05, GTM-06, GTM-07, GTM-08, GTM-09, GTM-10, GTM-11, GTM-12
**Success Criteria** (what must be TRUE):
  1. An AI agent can discover DeckForge via MCP server, call render/generate tools, and pay per-call in USDC via x402 protocol
  2. A human developer can visit the landing page, sign up, get an API key, and generate their first deck within 5 minutes
  3. The npm SDK (@deckforge/sdk) is published and installable, with working examples in the README
  4. Unkey manages all API key lifecycle (creation, rotation, revocation, usage tracking) in production
  5. GET /v1/pricing returns tier details and per-call x402 pricing that agents can parse programmatically
**Plans:** 3 plans

Plans:
- [ ] 09-01-PLAN.md -- x402 machine payments + Unkey API keys: dual auth middleware, x402 payment verification/settlement, Unkey replacing custom auth, per-call pricing config, GET /v1/pricing (Wave 1)
- [ ] 09-02-PLAN.md -- MCP server + SDK publishing: 6-tool MCP server, GitHub Actions npm publish workflow, marketing README, issue templates, contribution guide (Wave 1)
- [ ] 09-03-PLAN.md -- Landing page + onboarding + analytics: static landing page, developer onboarding flow, PaymentEvent model, usage analytics dashboard with Stripe/x402 revenue split (Wave 2)

### Phase 10: Zero-Budget Growth Engine
**Goal:** DeckForge is listed on all major MCP directories, has content assets driving organic traffic, demo decks proving product quality, agent framework integrations expanding ecosystem reach, and finance community presence targeting highest-value customers -- all with zero paid ad spend
**Depends on:** Phase 9
**Requirements**: GROWTH-01, GROWTH-02, GROWTH-03, GROWTH-04, GROWTH-05, GROWTH-06, GROWTH-07, GROWTH-08, GROWTH-09, GROWTH-10
**Success Criteria** (what must be TRUE):
  1. DeckForge MCP server is submitted to or listed on 5+ MCP directories (Smithery, Glama, mcpservers.org, OpenTools, Cursor Directory)
  2. GitHub repo has optimized topics, social preview spec, and README badges for maximum discoverability
  3. npm SDK has 19+ search-optimized keywords covering powerpoint, mcp, ai-agents, finance, pitch-deck
  4. 5 demo deck IRs exist showcasing McKinsey strategy, PE deal memo, startup pitch, board update, and product launch
  5. Content assets ready for launch: Show HN post, 2 Dev.to articles, Twitter thread, Reddit posts, Product Hunt kit
  6. Agent framework tool wrappers exist for LangChain, CrewAI, AutoGen, and Claude/MCP
  7. Finance community content targets IB/PE professionals with quantified value propositions
  8. SEO comparison page positions DeckForge against Beautiful.ai, Gamma, and SlidesAI
**Plans:** 3/3 plans complete

Plans:
- [x] 10-01-PLAN.md -- Distribution channels: MCP directory submissions, GitHub/npm optimization, install configs (Wave 1)
- [x] 10-02-PLAN.md -- Content engine: demo decks, Show HN, Dev.to articles, Twitter thread, Reddit posts, Product Hunt kit (Wave 1)
- [x] 10-03-PLAN.md -- Agent ecosystem + finance outreach: LangChain/CrewAI/AutoGen/Claude integrations, LinkedIn, WSO, comparison page (Wave 2)

### Phase 11: Production Launch
**Goal:** Anyone can clone, configure, deploy, and start earning with DeckForge within 30 minutes -- with production README, complete environment docs, verification scripts, CI/CD pipeline, and deployment documentation for all external services
**Depends on:** Phase 10
**Requirements**: LAUNCH-01, LAUNCH-02, LAUNCH-03, LAUNCH-04, LAUNCH-05, LAUNCH-06, LAUNCH-07, LAUNCH-08, LAUNCH-09, LAUNCH-10, LAUNCH-11, LAUNCH-12
**Success Criteria** (what must be TRUE):
  1. A developer can go from `git clone` to running API in under 10 minutes following README instructions
  2. `cp .env.example .env` produces a working local config with every setting documented
  3. Docker Compose starts all services and health check returns 200
  4. The full render pipeline produces a valid .pptx file end-to-end
  5. All 5 demo decks render to valid .pptx files
  6. GitHub Actions CI runs tests on every push, deploy workflow ships to Fly.io
  7. Stripe products and webhook are configurable via setup script
  8. Deployment documentation covers Fly.io, Unkey, x402, and npm SDK publishing
**Plans:** 3 plans

Plans:
- [ ] 11-01-PLAN.md -- Developer experience: README.md, .env.example, bootstrap-db.sh, CLAUDE.md (Wave 1)
- [ ] 11-02-PLAN.md -- Verification: Docker smoke test, e2e render test, demo deck validation (Wave 1)
- [ ] 11-03-PLAN.md -- Deployment and CI/CD: GitHub Actions, Stripe setup, Fly.io/Unkey/x402/npm docs (Wave 2)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10 -> 11
Note: Phase 4 and Phase 5 both depend on Phase 3 and could execute in parallel.
Note: Phase 9 Plans 01 and 02 can execute in parallel (Wave 1). Plan 03 depends on both (Wave 2).
Note: Phase 10 Plans 01 and 02 can execute in parallel (Wave 1). Plan 03 depends on both (Wave 2).
Note: Phase 11 Plans 01 and 02 can execute in parallel (Wave 1). Plan 03 depends on both (Wave 2).

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation + IR Schema | 3/3 | Complete   | 2026-03-29 |
| 2. Layout Engine + Theme System | 3/3 | Complete    | 2026-03-29 |
| 3. PPTX Rendering | 3/3 | Complete | 2026-03-29 |
| 4. Content Generation Pipeline | 2/2 | Complete | 2026-03-29 |
| 5. Chart Engine + Finance Vertical | 3/3 | Complete | 2026-03-29 |
| 6. Google Slides Output | 2/2 | Complete | 2026-03-29 |
| 7. QA Pipeline + Deck Operations | 3/3 | Complete | 2026-03-29 |
| 8. TypeScript SDK + Billing + Launch | 3/3 | Complete | 2026-03-29 |
| 9. Monetization and Go-To-Market | 3/3 | Complete | 2026-03-29 |
| 10. Zero-Budget Growth Engine | 3/3 | Complete    | 2026-03-29 |
| 11. Production Launch | 0/3 | Planning | - |
