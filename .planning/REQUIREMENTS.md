# Requirements: DeckForge

**Defined:** 2026-03-28
**Core Value:** Any agent or human can produce a board-ready presentation in a single API call -- with professional layout, consistent branding, and verified quality.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### IR Schema & Core Models

- [ ] **IR-01**: IR schema defines all 32 slide types as Pydantic discriminated unions
- [ ] **IR-02**: IR schema defines all element types (text, data, visual, layout) with typed payloads
- [ ] **IR-03**: IR schema defines all chart subtypes with data models
- [ ] **IR-04**: IR schema validates input and returns descriptive errors for malformed payloads
- [ ] **IR-05**: IR supports generation_options (target_slide_count, density, chart_style, quality_target)
- [ ] **IR-06**: IR supports metadata (title, purpose, audience, confidentiality, language)

### API & Infrastructure

- [ ] **API-01**: POST /v1/render accepts IR JSON and returns rendered PPTX synchronously (<=10 slides)
- [ ] **API-02**: POST /v1/generate accepts NL prompt and returns deck asynchronously with job tracking
- [ ] **API-03**: POST /v1/render/preview returns first N slides as PNG thumbnails
- [ ] **API-04**: POST /v1/estimate returns credit cost estimate for a given IR or prompt
- [ ] **API-05**: GET /v1/themes lists all available themes with metadata
- [ ] **API-06**: GET /v1/slide-types lists all slide types with example IR
- [ ] **API-07**: GET /v1/capabilities returns API capabilities and limits
- [ ] **API-08**: GET /v1/health returns API health status
- [ ] **API-09**: API key authentication (dk_live_/dk_test_ format) with scoped permissions
- [ ] **API-10**: Rate limiting per API key per tier (10/60/custom req/min)
- [ ] **API-11**: OpenAPI 3.1 spec auto-generated from Pydantic models
- [ ] **API-12**: Webhook registration and async completion notifications
- [ ] **API-13**: SSE streaming for generation progress events
- [ ] **API-14**: Idempotent operations via client-provided request_id

### PPTX Rendering

- [ ] **PPTX-01**: Render all 23 universal slide types to well-formatted PPTX
- [ ] **PPTX-02**: Render native editable charts (bar, line, pie, scatter, combo, area, donut, radar, funnel, treemap)
- [ ] **PPTX-03**: Render static image charts via Plotly for unsupported types (waterfall, heatmap, sankey, gantt, football_field)
- [ ] **PPTX-04**: Render data tables with header/body/footer rows, conditional formatting, and proper alignment
- [ ] **PPTX-05**: Embed images from URLs or base64 with proper sizing and positioning
- [ ] **PPTX-06**: Support slide transitions (none, fade, slide, push)
- [ ] **PPTX-07**: Include speaker notes from IR in generated PPTX
- [ ] **PPTX-08**: 16:9 widescreen aspect ratio (13.333" x 7.5")

### Google Slides Rendering

- [ ] **GSLIDES-01**: Render all 23 universal slide types to native Google Slides via API
- [ ] **GSLIDES-02**: Create Sheets-backed editable charts linked into Slides
- [ ] **GSLIDES-03**: Handle OAuth 2.0 for user's Google Drive access
- [ ] **GSLIDES-04**: Use batchUpdate for efficient API usage
- [ ] **GSLIDES-05**: Clean up temporary Sheets spreadsheets after chart creation
- [ ] **GSLIDES-06**: Return Slides URL and presentation_id

### Layout Engine

- [ ] **LAYOUT-01**: Constraint-based layout solver using kiwisolver on 12-column grid
- [ ] **LAYOUT-02**: Text measurement via Pillow + FreeType for bounding box calculation
- [ ] **LAYOUT-03**: Adaptive content handling: overflow -> reduce font -> reflow -> split to multi-slide
- [ ] **LAYOUT-04**: Visual hierarchy enforcement (title -> subtitle -> body -> footnote)
- [ ] **LAYOUT-05**: Consistent spacing verification (+-2px tolerance) and alignment snapping
- [ ] **LAYOUT-06**: Layout patterns per slide type (title, bullets, two_column, chart, table, etc.)

### Theme Engine

- [ ] **THEME-01**: 15 curated themes defined in YAML with full color/typography/spacing specs
- [ ] **THEME-02**: Theme registry that loads and resolves variable references ($colors.primary -> #0A1E3D)
- [ ] **THEME-03**: Brand kit overlay system (colors, fonts, logo placement) merging on top of themes
- [ ] **THEME-04**: Slide masters per slide type within each theme
- [ ] **THEME-05**: Color theory engine with WCAG AA contrast validation (4.5:1 text, 3:1 large)

### Content Generation

- [ ] **CONTENT-01**: Intent parsing from NL prompt (purpose, audience, slide_count, topics, tone)
- [ ] **CONTENT-02**: Outline generation with narrative arc (pyramid principle, MECE, situation-complication-resolution)
- [ ] **CONTENT-03**: Per-slide content expansion (headlines <=8 words, bullets <=12 words, speaker notes)
- [ ] **CONTENT-04**: Cross-slide consistency refinement (terminology, tense, style, redundancy elimination)
- [ ] **CONTENT-05**: Model-agnostic LLM adapter (Claude, OpenAI, Gemini, Ollama) with fallback chains
- [ ] **CONTENT-06**: BYO model key support -- user provides their own API key and model choice

### Chart Engine

- [ ] **CHART-01**: Native editable PPTX charts for supported types
- [ ] **CHART-02**: Static image fallback via Plotly/Kaleido for unsupported chart types
- [ ] **CHART-03**: Chart type recommender (data -> best chart type suggestion)
- [ ] **CHART-04**: Axis, label, legend formatting with theme-aware styling
- [ ] **CHART-05**: Financial chart types: waterfall (stacked bar workaround), sensitivity table, football field

### Finance Vertical

- [ ] **FIN-01**: comp_table slide type with EV/EBITDA, P/E formatting, median highlight, conditional formatting
- [ ] **FIN-02**: dcf_summary slide type with assumptions table and 2-variable sensitivity matrix
- [ ] **FIN-03**: waterfall_chart slide type with auto-color positive/negative bars and running total
- [ ] **FIN-04**: deal_overview one-pager with traffic light indicators and unit economics
- [ ] **FIN-05**: returns_analysis with IRR/MOIC/CoC matrix and scenario table
- [ ] **FIN-06**: capital_structure with sources & uses and debt stack visualization
- [ ] **FIN-07**: market_landscape with TAM/SAM/SOM and competitive positioning
- [ ] **FIN-08**: investment_thesis with numbered thesis points and risk/reward framework
- [ ] **FIN-09**: risk_matrix heat map with likelihood/impact axes
- [ ] **FIN-10**: Financial data ingestion from CSV/Excel with auto-detect structure
- [ ] **FIN-11**: Currency/percentage/multiple formatting engine

### QA Pipeline

- [ ] **QA-01**: Structural integrity check (every slide has title, no empty slides, narrative flow)
- [ ] **QA-02**: Text quality check (no overflow, no orphans/widows, consistent capitalization)
- [ ] **QA-03**: Visual quality check (WCAG AA contrast, font size floors, alignment consistency)
- [ ] **QA-04**: Data integrity check (chart data matches source, table totals correct, percentages sum)
- [ ] **QA-05**: Brand compliance check (approved colors/fonts only, logo placement, confidentiality marking)
- [ ] **QA-06**: Auto-fix engine that corrects font sizes, spacing, and contrast before delivery
- [ ] **QA-07**: Executive readiness scoring (0-100) with quality report in API response

### Deck Operations

- [ ] **DECK-01**: List, get, delete generated decks with metadata
- [ ] **DECK-02**: Get the IR that produced a deck (reproducibility)
- [ ] **DECK-03**: Re-export deck to different format (pptx <-> gslides)
- [ ] **DECK-04**: Append slides to existing deck
- [ ] **DECK-05**: Replace specific slides in existing deck
- [ ] **DECK-06**: Reorder slides in existing deck
- [ ] **DECK-07**: Retheme existing deck with different theme

### Batch Operations

- [ ] **BATCH-01**: Batch render multiple decks in one request
- [ ] **BATCH-02**: Batch variations -- same content with multiple themes

### TypeScript SDK

- [ ] **SDK-01**: DeckForge client class with typed methods for all API endpoints
- [ ] **SDK-02**: Fluent builder API (Presentation.create(), Slide.titleSlide(), Elements.lineChart())
- [ ] **SDK-03**: SSE streaming helper (df.generate.stream() -> AsyncGenerator)
- [ ] **SDK-04**: Auto-generated types from Pydantic IR via OpenAPI
- [ ] **SDK-05**: Published to npm as @deckforge/sdk

### Billing & Auth

- [ ] **BILL-01**: Three tiers: Starter ($0/50 credits), Pro ($79/500 credits), Enterprise (custom)
- [ ] **BILL-02**: Credit cost model (1 credit per 10-slide structured render, surcharges for NL/finance/gslides)
- [ ] **BILL-03**: Credit reservation pre-flight, actual deduction on completion
- [ ] **BILL-04**: Stripe integration for payments and subscription management
- [ ] **BILL-05**: Usage dashboard (credits remaining, history, projected spend)
- [ ] **BILL-06**: Overage billing at tier-specific rates ($0.50/$0.30/volume)

### Async & Workers

- [ ] **WORKER-01**: ARQ + Redis task queue for content generation and rendering jobs
- [ ] **WORKER-02**: Separate content worker pool (I/O-bound) and render worker pool (CPU-bound)
- [ ] **WORKER-03**: S3/R2 file storage for generated presentations
- [ ] **WORKER-04**: Webhook delivery on job completion
- [ ] **WORKER-05**: Job status tracking with progress events

### Infrastructure

- [ ] **INFRA-01**: Docker Compose for local development (API + workers + Redis + PostgreSQL + MinIO)
- [ ] **INFRA-02**: Dockerfile with bundled TrueType fonts for headless text measurement
- [ ] **INFRA-03**: PostgreSQL database with SQLAlchemy models (users, api_keys, decks, usage_events)
- [ ] **INFRA-04**: Alembic migrations
- [ ] **INFRA-05**: Railway/Fly.io deployment configuration for MVP launch

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Advanced Features

- **V2-01**: PDF export via LibreOffice headless
- **V2-02**: MCP server integration for agent discovery
- **V2-03**: Custom theme YAML upload (enterprise)
- **V2-04**: Multi-language support (i18n for slide content)
- **V2-05**: Slide-level analytics (views, engagement tracking)
- **V2-06**: Version history for decks
- **V2-07**: Team/organization accounts with shared brand kits
- **V2-08**: SAML/OIDC SSO for enterprise
- **V2-09**: Icon library with 1000+ searchable business icons
- **V2-10**: Image generation integration (DALL-E, Midjourney) for slide backgrounds

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Web-based slide editor UI | API-only product; editing happens in PowerPoint/Google Slides |
| Real-time collaboration | Google Slides handles this natively |
| Template marketplace | Quality control nightmare; curated themes only |
| Video/animation authoring | Different domain; static presentations only |
| Custom LLM fine-tuning | Prompt engineering sufficient; massive R&D cost |
| White-label hosting | API delivers files; no presentation viewer needed |
| Mobile app | API-first; TypeScript SDK works in React Native if needed |
| Slide-level caching | Complicates determinism; cache at deck level via request_id |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| IR-01 | Phase 1: Foundation + IR Schema | Pending |
| IR-02 | Phase 1: Foundation + IR Schema | Pending |
| IR-03 | Phase 1: Foundation + IR Schema | Pending |
| IR-04 | Phase 1: Foundation + IR Schema | Pending |
| IR-05 | Phase 1: Foundation + IR Schema | Pending |
| IR-06 | Phase 1: Foundation + IR Schema | Pending |
| API-01 | Phase 3: PPTX Rendering | Pending |
| API-02 | Phase 4: Content Generation Pipeline | Pending |
| API-03 | Phase 3: PPTX Rendering | Pending |
| API-04 | Phase 7: QA Pipeline + Deck Operations | Pending |
| API-05 | Phase 8: TypeScript SDK + Billing + Launch | Pending |
| API-06 | Phase 8: TypeScript SDK + Billing + Launch | Pending |
| API-07 | Phase 8: TypeScript SDK + Billing + Launch | Pending |
| API-08 | Phase 1: Foundation + IR Schema | Pending |
| API-09 | Phase 1: Foundation + IR Schema | Pending |
| API-10 | Phase 1: Foundation + IR Schema | Pending |
| API-11 | Phase 1: Foundation + IR Schema | Pending |
| API-12 | Phase 7: QA Pipeline + Deck Operations | Pending |
| API-13 | Phase 4: Content Generation Pipeline | Pending |
| API-14 | Phase 1: Foundation + IR Schema | Pending |
| PPTX-01 | Phase 3: PPTX Rendering | Pending |
| PPTX-02 | Phase 3: PPTX Rendering | Pending |
| PPTX-03 | Phase 3: PPTX Rendering | Pending |
| PPTX-04 | Phase 3: PPTX Rendering | Pending |
| PPTX-05 | Phase 3: PPTX Rendering | Pending |
| PPTX-06 | Phase 3: PPTX Rendering | Pending |
| PPTX-07 | Phase 3: PPTX Rendering | Pending |
| PPTX-08 | Phase 3: PPTX Rendering | Pending |
| GSLIDES-01 | Phase 6: Google Slides Output | Pending |
| GSLIDES-02 | Phase 6: Google Slides Output | Pending |
| GSLIDES-03 | Phase 6: Google Slides Output | Pending |
| GSLIDES-04 | Phase 6: Google Slides Output | Pending |
| GSLIDES-05 | Phase 6: Google Slides Output | Pending |
| GSLIDES-06 | Phase 6: Google Slides Output | Pending |
| LAYOUT-01 | Phase 2: Layout Engine + Theme System | Pending |
| LAYOUT-02 | Phase 2: Layout Engine + Theme System | Pending |
| LAYOUT-03 | Phase 2: Layout Engine + Theme System | Pending |
| LAYOUT-04 | Phase 2: Layout Engine + Theme System | Pending |
| LAYOUT-05 | Phase 2: Layout Engine + Theme System | Pending |
| LAYOUT-06 | Phase 2: Layout Engine + Theme System | Pending |
| THEME-01 | Phase 2: Layout Engine + Theme System | Pending |
| THEME-02 | Phase 2: Layout Engine + Theme System | Pending |
| THEME-03 | Phase 2: Layout Engine + Theme System | Pending |
| THEME-04 | Phase 2: Layout Engine + Theme System | Pending |
| THEME-05 | Phase 2: Layout Engine + Theme System | Pending |
| CONTENT-01 | Phase 4: Content Generation Pipeline | Pending |
| CONTENT-02 | Phase 4: Content Generation Pipeline | Pending |
| CONTENT-03 | Phase 4: Content Generation Pipeline | Pending |
| CONTENT-04 | Phase 4: Content Generation Pipeline | Pending |
| CONTENT-05 | Phase 4: Content Generation Pipeline | Pending |
| CONTENT-06 | Phase 4: Content Generation Pipeline | Pending |
| CHART-01 | Phase 5: Chart Engine + Finance Vertical | Pending |
| CHART-02 | Phase 5: Chart Engine + Finance Vertical | Pending |
| CHART-03 | Phase 5: Chart Engine + Finance Vertical | Pending |
| CHART-04 | Phase 5: Chart Engine + Finance Vertical | Pending |
| CHART-05 | Phase 5: Chart Engine + Finance Vertical | Pending |
| FIN-01 | Phase 5: Chart Engine + Finance Vertical | Pending |
| FIN-02 | Phase 5: Chart Engine + Finance Vertical | Pending |
| FIN-03 | Phase 5: Chart Engine + Finance Vertical | Pending |
| FIN-04 | Phase 5: Chart Engine + Finance Vertical | Pending |
| FIN-05 | Phase 5: Chart Engine + Finance Vertical | Pending |
| FIN-06 | Phase 5: Chart Engine + Finance Vertical | Pending |
| FIN-07 | Phase 5: Chart Engine + Finance Vertical | Pending |
| FIN-08 | Phase 5: Chart Engine + Finance Vertical | Pending |
| FIN-09 | Phase 5: Chart Engine + Finance Vertical | Pending |
| FIN-10 | Phase 5: Chart Engine + Finance Vertical | Pending |
| FIN-11 | Phase 5: Chart Engine + Finance Vertical | Pending |
| QA-01 | Phase 7: QA Pipeline + Deck Operations | Pending |
| QA-02 | Phase 7: QA Pipeline + Deck Operations | Pending |
| QA-03 | Phase 7: QA Pipeline + Deck Operations | Pending |
| QA-04 | Phase 7: QA Pipeline + Deck Operations | Pending |
| QA-05 | Phase 7: QA Pipeline + Deck Operations | Pending |
| QA-06 | Phase 7: QA Pipeline + Deck Operations | Pending |
| QA-07 | Phase 7: QA Pipeline + Deck Operations | Pending |
| DECK-01 | Phase 7: QA Pipeline + Deck Operations | Pending |
| DECK-02 | Phase 7: QA Pipeline + Deck Operations | Pending |
| DECK-03 | Phase 7: QA Pipeline + Deck Operations | Pending |
| DECK-04 | Phase 7: QA Pipeline + Deck Operations | Pending |
| DECK-05 | Phase 7: QA Pipeline + Deck Operations | Pending |
| DECK-06 | Phase 7: QA Pipeline + Deck Operations | Pending |
| DECK-07 | Phase 7: QA Pipeline + Deck Operations | Pending |
| BATCH-01 | Phase 7: QA Pipeline + Deck Operations | Pending |
| BATCH-02 | Phase 7: QA Pipeline + Deck Operations | Pending |
| SDK-01 | Phase 8: TypeScript SDK + Billing + Launch | Pending |
| SDK-02 | Phase 8: TypeScript SDK + Billing + Launch | Pending |
| SDK-03 | Phase 8: TypeScript SDK + Billing + Launch | Pending |
| SDK-04 | Phase 8: TypeScript SDK + Billing + Launch | Pending |
| SDK-05 | Phase 8: TypeScript SDK + Billing + Launch | Pending |
| BILL-01 | Phase 8: TypeScript SDK + Billing + Launch | Pending |
| BILL-02 | Phase 8: TypeScript SDK + Billing + Launch | Pending |
| BILL-03 | Phase 8: TypeScript SDK + Billing + Launch | Pending |
| BILL-04 | Phase 8: TypeScript SDK + Billing + Launch | Pending |
| BILL-05 | Phase 8: TypeScript SDK + Billing + Launch | Pending |
| BILL-06 | Phase 8: TypeScript SDK + Billing + Launch | Pending |
| WORKER-01 | Phase 1: Foundation + IR Schema | Pending |
| WORKER-02 | Phase 1: Foundation + IR Schema | Pending |
| WORKER-03 | Phase 1: Foundation + IR Schema | Pending |
| WORKER-04 | Phase 1: Foundation + IR Schema | Pending |
| WORKER-05 | Phase 1: Foundation + IR Schema | Pending |
| INFRA-01 | Phase 1: Foundation + IR Schema | Pending |
| INFRA-02 | Phase 1: Foundation + IR Schema | Pending |
| INFRA-03 | Phase 1: Foundation + IR Schema | Pending |
| INFRA-04 | Phase 1: Foundation + IR Schema | Pending |
| INFRA-05 | Phase 8: TypeScript SDK + Billing + Launch | Pending |

**Coverage:**
- v1 requirements: 104 total
- Mapped to phases: 104
- Unmapped: 0

---
*Requirements defined: 2026-03-28*
*Last updated: 2026-03-26 after roadmap creation (traceability populated)*
