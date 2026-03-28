# DeckForge — SOTA AI Slide Maker Design Spec

**Date:** 2026-03-28
**Status:** Approved
**Product:** DeckForge — Executive-ready slides, one API call away.

---

## 1. Overview

DeckForge is an API-first platform for generating professional, executive-ready presentations. It outputs both PPTX files and native Google Slides presentations. It serves two audiences: AI agents (structured API) and humans (natural language endpoint). The finance vertical is the wedge; horizontal presentation types are the scale play.

### Key Decisions

| Decision | Choice |
|---|---|
| Input model | Structured IR API + Natural language endpoint |
| Output formats | PPTX (python-pptx) + Native Google Slides API |
| Tech stack | Python FastAPI + TypeScript SDK (@deckforge/sdk) |
| Architecture | Modular monolith + async workers (ARQ/Redis) |
| Design system | 15 curated themes + brand kit overlay |
| AI content | Model-agnostic (Claude, GPT, Gemini, Ollama) |
| Scope | 32 slide types (23 universal + 9 finance vertical) |
| Charts | Native editable + static image fallback |
| Pricing | Tiered subscriptions (Starter/Pro/Enterprise) + credit usage |

---

## 2. The DeckForge Moat — 6 Intelligence Layers

No competitor has more than 2 of these. DeckForge has all 6, composable.

### Layer 1: Narrative Intelligence
- Story arc, argument structure, McKinsey/BCG/Bain frameworks
- Pyramid principle, MECE, situation-complication-resolution
- Board deck flows differently than a sales pitch

### Layer 2: Content Intelligence
- Concise, impactful, executive-grade slide copy
- Data-aware: interprets tables/CSVs and decides what to visualize
- Knows when to use bullets vs chart vs callout vs full-bleed image

### Layer 3: Layout Intelligence
- Constraint-based layout solver (not templates)
- Visual hierarchy, information density, whitespace management
- Adapts layout to content volume — 3 bullets vs 12 bullets get different layouts
- 12-column grid, golden ratio proportions

### Layer 4: Design Intelligence
- Color theory engine — palette generation, WCAG AA contrast validation
- Typography scale — modular scale, kerning, line height rules
- Visual rhythm — consistent spacing, alignment snapping, optical centering
- Aesthetic differentiation between "tech startup" and "private equity"

### Layer 5: Data Visualization Intelligence
- Chooses right chart type for data
- Formats axes, labels, legends for maximum readability
- Financial-grade: waterfall, bridge, football field, sensitivity tables
- Annotation engine — auto-highlights key data points

### Layer 6: Quality Assurance Intelligence
- Text overflow detection — no clipped text ever ships
- Brand compliance checker
- Accessibility audit (contrast, font sizes, alt text)
- Consistency scanner
- Executive readiness score (0-100) before delivery

---

## 3. Intermediate Representation (IR)

The IR is the product's backbone. It's what the structured API accepts, what the NL endpoint produces, what themes operate on, and what both renderers consume.

### Presentation Structure

```
Presentation
├── metadata
│   ├── title, subtitle, author, company, date
│   ├── language (i18n-ready)
│   ├── purpose: enum (board_meeting | investor_update | sales_pitch |
│   │   training | project_update | strategy | research | deal_memo |
│   │   ic_presentation | quarterly_review | all_hands | keynote)
│   ├── audience: enum (c_suite | board | investors | team | clients | public)
│   └── confidentiality: enum (public | internal | confidential | restricted)
│
├── brand_kit (optional override)
│   ├── colors: { primary, secondary, accent[], background, text, muted }
│   ├── fonts: { heading, body, mono, caption }
│   ├── logo: { url, placement, size_constraints }
│   ├── footer: { text, include_page_numbers, include_date, include_logo }
│   └── tone: enum (formal | professional | conversational | bold)
│
├── theme: string (references curated theme ID)
│
├── slides[]
│   ├── slide_type: enum (32 types — see taxonomy)
│   ├── layout_hint: enum (full | split_left | split_right | split_top |
│   │   two_column | three_column | grid_2x2 | grid_3x3 |
│   │   centered | title_only | blank)
│   ├── transition: enum (none | fade | slide | push)
│   ├── speaker_notes: string (markdown)
│   ├── build_animations: [] (element appear order)
│   └── elements[]
│       ├── type: enum (element taxonomy)
│       ├── position: { x, y, width, height } (optional — layout engine fills)
│       ├── style_overrides: {} (optional — theme fills defaults)
│       └── content: (type-specific payload)
│
└── generation_options
    ├── target_slide_count: int | range
    ├── density: enum (sparse | balanced | dense)
    ├── chart_style: enum (minimal | detailed | annotated)
    ├── emphasis: enum (visual | data | narrative)
    └── quality_target: enum (draft | presentation_ready | board_ready)
```

### Slide Type Taxonomy (32 types)

**Universal (23):**
title_slide, agenda, section_divider, key_message, bullet_points, two_column_text, comparison, timeline, process_flow, org_chart, team_slide, quote_slide, image_with_caption, icon_grid, stats_callout, table_slide, chart_slide, matrix, funnel, map_slide, thank_you, appendix, q_and_a

**Finance Vertical (9):**
dcf_summary, comp_table, waterfall_chart, deal_overview, returns_analysis, capital_structure, market_landscape, risk_matrix, investment_thesis

### Element Type Taxonomy

**Text:** heading, subheading, body_text, bullet_list, numbered_list, callout_box, pull_quote, footnote, label

**Data:** table, chart, kpi_card, metric_group, progress_bar, gauge, sparkline

**Visual:** image, icon, shape, divider, spacer, logo, background

**Layout:** container, column, row, grid_cell

### Chart Subtypes

**Native editable:** bar, stacked_bar, grouped_bar, horizontal_bar, line, multi_line, area, stacked_area, pie, donut, scatter, bubble, combo, waterfall, funnel, treemap, radar, tornado, football_field, sensitivity_table

**Static fallback:** heatmap, sankey, gantt, sunburst

---

## 4. Core Architecture

Modular monolith with async workers.

```
Client → FastAPI (auth, routing, billing)
  ├── Structured input → validate → Rendering Worker → output
  └── NL input → Content Worker (LLM) → IR → Rendering Worker → output
```

### Module Boundaries

| Module | Responsibility | Input | Output |
|---|---|---|---|
| api/ | HTTP routes, auth, rate limiting, billing | HTTP requests | HTTP responses |
| content/ | LLM orchestration, prompts, outline, copywriting | NL prompt + config | IR |
| ir/ | Pydantic IR schema, validation | JSON | Validated IR models |
| layout/ | Constraint-based layout solver, grid system | IR + Theme | Layout IR (positioned) |
| rendering/pptx/ | python-pptx renderer | Layout IR | .pptx bytes |
| rendering/gslides/ | Google Slides API renderer | Layout IR | Slides URL |
| themes/ | Theme registry, brand kit overlay | theme_id + brand_kit | Resolved Theme |
| charts/ | Native chart builder + static fallback | Chart element + theme | Chart object/image |
| finance/ | Finance layouts, calculations, formatting | Financial data | Finance IR elements |
| qa/ | 5-pass QA pipeline, autofix, scoring | Rendered deck + IR | QA report + fixes |
| workers/ | Async task definitions, webhooks, storage | Job payloads | Task results |

### Module Communication Contracts

- content/ ONLY produces IR, never touches rendering
- rendering/ consumes IR, never calls LLMs
- layout/ adds geometry, never modifies content
- themes/ resolves variable references to concrete values
- qa/ is read-only by default; autofix returns patches
- llm/ adapters normalize ALL models to same output schema

---

## 5. Layout Engine

Constraint-based layout solver (not fixed templates).

### Pipeline

1. **Content Analysis** — Measure text bounding boxes, count elements, classify complexity, determine density score
2. **Layout Selection** — Match slide_type + content profile to candidates, score on whitespace/hierarchy/reading flow/density, select best (or use layout_hint)
3. **Constraint Solving** — 12-column grid on 16:9 aspect ratio, margins (>=0.5"), gutters (>=0.25"), min font sizes (14pt body, 24pt heading), visual hierarchy enforcement
4. **Adaptive Refinement** — Overflow → reduce font (floor 12pt) → reflow → split to multi-slide if needed; sparse → increase sizes; snap to grid, optical alignment
5. **Polish Pass** — Consistent spacing (+-2px), alignment groups, WCAG AA contrast, orphan/widow detection

---

## 6. Theme Engine

### Theme Structure (YAML)

Each theme defines: colors (palette + semantic + chart_series), typography (families, weights, tracking, modular scale), spacing (margins, gaps, grid), shapes (radius, shadow, dividers), and slide_masters (per-slide-type defaults).

### 15 Curated Themes

executive-dark, executive-light, consulting-classic, consulting-modern, startup-pitch, startup-minimal, finance-institutional, finance-modern, tech-product, tech-engineering, corporate-standard, corporate-bold, research-academic, sales-closer, training-workshop

### Brand Kit Overlay

Users can overlay: primary/secondary colors, logo, fonts, footer text. Protected properties (grid, typography scale) cannot be overridden to preserve layout integrity. Merge strategy: deep merge (theme defaults + user overrides).

---

## 7. QA Pipeline

5-pass automatic QA runs before every delivery.

1. **Structural Integrity** — Every slide has title, no empty slides, narrative flow, section dividers present
2. **Text Quality** — No overflow, no orphans/widows, consistent capitalization, bullet consistency, max bullet count
3. **Visual Quality** — WCAG AA contrast, font size floors, alignment consistency, spacing consistency, no overlaps, image resolution check
4. **Data Integrity** — Chart data matches source, table totals correct, percentages sum, consistent number formatting, axis scales appropriate
5. **Brand Compliance** — Only approved colors/fonts, logo placement, confidentiality marking, disclaimers

**Output:** quality_score (0-100), issues array, auto_fixes applied, executive_readiness rating (draft | needs_review | presentation_ready | board_ready)

**Auto-fix:** QA auto-corrects font sizes, spacing, contrast issues before reporting. Only unfixable issues are surfaced.

---

## 8. Agent-First API Design

### 10 Principles

1. **Deterministic output** — Same IR → same visual output
2. **Schema-first** — Full OpenAPI 3.1, JSON Schema for IR
3. **Streaming progress** — SSE for long-running generations
4. **Idempotent operations** — Client request_id prevents duplicates
5. **Partial results** — Preview, outline-only, single-slide endpoints
6. **Composable operations** — Append, replace, reorder, retheme slides
7. **Webhook callbacks** — Async completion notifications
8. **Batch operations** — Multiple decks or theme variations per call
9. **Cost transparency** — Estimate endpoint before generation
10. **Self-describing** — Discovery endpoints for themes, slide types, capabilities

### Full API Surface

**Generation:** POST /v1/generate, /v1/render, /v1/render/preview, /v1/render/outline, /v1/render/single-slide, /v1/estimate

**Deck Operations:** GET/DELETE /v1/decks/{id}, GET /v1/decks/{id}/ir, POST /v1/decks/{id}/export

**Slide Operations:** POST /v1/decks/{id}/slides/append, PUT /v1/decks/{id}/slides/{n}, PATCH /v1/decks/{id}/slides/reorder, POST /v1/decks/{id}/retheme

**Batch:** POST /v1/batch/render, /v1/batch/variations

**Themes & Assets:** GET/POST /v1/themes, /v1/brand-kits, /v1/icons, POST /v1/images/upload

**Discovery:** GET /v1/capabilities, /v1/slide-types, /v1/chart-types, /v1/templates

**Account:** GET /v1/usage, /v1/usage/estimate, POST /v1/webhooks, GET /v1/health

---

## 9. Content Generation Pipeline

### Multi-Model Orchestration

LLMAdapter interface with adapters for Claude, OpenAI, Gemini, Ollama. User provides provider + api_key + model, or uses platform default (Claude). Fallback chains configurable.

### NL → IR Pipeline

1. **Intent Parsing** — Extract purpose, audience, slide_count, topics, tone, language, domain
2. **Outline Generation** — Narrative arc (pyramid principle for board, problem-solution for pitches), assign slide_types
3. **Content Expansion** — Per-slide generation (parallelized), headlines (8 words max), bullets (12 words max), speaker notes, chart recommendations
4. **Content Refinement** — Cross-slide consistency, redundancy elimination, "so what?" test, executive summary generation

---

## 10. Finance Vertical

### Capabilities

- **Data Ingestion:** CSV/Excel auto-detect, JSON structured data, template placeholder data
- **comp_table:** Auto-formats EV/EBITDA, P/E, highlights median/selected, conditional formatting
- **dcf_summary:** Assumptions table, 2-var sensitivity matrix, football field valuation range
- **waterfall_chart:** Revenue bridge, EBITDA walk, auto-colors positive/negative, running total
- **returns_analysis:** IRR/MOIC/CoC matrix, entry/exit sensitivity, J-curve, distribution waterfall
- **deal_overview:** One-pager layout, traffic light indicators, unit economics, risks/mitigants
- **capital_structure:** Sources & uses, debt stack visualization, coverage ratios
- **market_landscape:** TAM/SAM/SOM, growth with CAGR, competitive positioning
- **investment_thesis:** Numbered thesis points with evidence, risk/reward framework

---

## 11. TypeScript SDK

### Design Philosophy

Not just an HTTP wrapper — a fluent builder API for constructing IR naturally, plus typed client for all endpoints.

### Key Features

- `DeckForge` client class with full typed methods
- `Presentation.create()` fluent builder
- `Slide.*()` factory methods for all 32 slide types
- `Elements.*()` factory methods for charts, tables, KPIs
- `df.generate.stream()` → AsyncGenerator<ProgressEvent>
- Auto-generated types from Pydantic via OpenAPI
- Typed error classes (RateLimitError, InsufficientCreditsError)
- Published to npm as @deckforge/sdk

---

## 12. Authentication & Billing

### Auth

- **API Keys:** dk_live_<hex> / dk_test_<hex>, scoped (read/generate/full), rotatable with 24h grace
- **OAuth 2.0:** PKCE for SPAs, authorization code for servers, required for Google Slides output

### Pricing Tiers

| | Starter ($0/mo) | Pro ($79/mo) | Enterprise (Custom) |
|---|---|---|---|
| Credits/mo | 50 | 500 | Unlimited |
| Overage | $0.50/credit | $0.30/credit | Volume |
| Rate limit | 10/min | 60/min | Custom |
| Themes | 5 basic | All 15 | All + custom |
| Brand kits | 1 | 5 | Unlimited |
| Output | PPTX | PPTX + Slides | PPTX + Slides + PDF |
| Max slides | 20/deck | 50/deck | 100/deck |
| Finance | No | Yes | Yes + custom verticals |
| BYO model | No | Yes | Yes |
| Batch | No | 10/batch | 100/batch |

### Credit Costs

- Structured render 1-10 slides: 1 credit
- Structured render 11-25 slides: 2 credits
- NL generate: render cost + 1 credit per 10 slides (platform LLM) or +0 (BYO key)
- Google Slides output: +1 credit
- Finance slides: +0.5 credit per finance slide
- Batch discount: -20% for 10+

---

## 13. Deployment

### Infrastructure

FastAPI + uvicorn API servers, ARQ workers (content + render), Redis (queue + rate limits + SSE pubsub), PostgreSQL (users, decks, usage), S3/R2 (files).

### Phases

1. **MVP:** Railway/Fly.io, single API + 2 workers, Upstash Redis, Neon PostgreSQL, Cloudflare R2. ~$50-100/mo
2. **Growth:** AWS ECS / GCP Cloud Run, auto-scaling 2-8 API + 2-16 workers. ~$500-2000/mo
3. **Scale:** Kubernetes, multi-region, CDN. Scales with revenue.

### Performance Targets

- /v1/render (<=10 slides): p50 800ms, p95 2.5s
- /v1/render (11-50 slides): p50 3s, p95 8s
- /v1/generate (10-slide NL): p50 12s, p95 25s
- /v1/render/preview: p50 1.5s

---

## 14. Project Structure

```
SlideMaker/
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── src/
│   ├── deckforge/
│   │   ├── config.py
│   │   ├── api/ (app, deps, middleware/, routes/, schemas/)
│   │   ├── ir/ (schema, elements, slides, charts, validators, examples/)
│   │   ├── content/ (pipeline, intent, outliner, writer, refiner, prompts/, llm/)
│   │   ├── layout/ (solver, grid, measure, hierarchy, adaptive, patterns/)
│   │   ├── rendering/pptx/ (renderer, elements, charts, tables, images, fonts)
│   │   ├── rendering/gslides/ (renderer, elements, charts, auth, batch)
│   │   ├── themes/ (registry, engine, brand_kit, colors, typography, builtins/)
│   │   ├── charts/ (builder, native, static, recommender, formatter, financial)
│   │   ├── finance/ (layouts, calculations, formatting, templates, data_ingestion)
│   │   ├── qa/ (pipeline, structural, text, visual, data, brand, autofix, scoring)
│   │   ├── workers/ (tasks, callbacks, storage)
│   │   ├── icons/ (registry, sets/)
│   │   └── db/ (models, migrations/, repository)
│   └── sdk/ (TypeScript — package.json, src/, tests/)
├── tests/ (unit/, integration/, rendering/, fixtures/, benchmarks/)
├── docs/ (api/, ir-reference/, themes/, examples/)
└── deploy/ (k8s/, terraform/, scripts/)
```

---

## Appendix: Data Flow Diagrams

### NL Flow
Client → POST /v1/generate → 202 {job_id, sse_url} → Content Worker (intent → outline → expand → refine → IR) → Rendering Worker (theme → layout → render → QA → autofix → upload) → SSE complete {download_url, quality_score, credits_used} → webhook fired

### Structured Flow
Client → POST /v1/render → validate IR → Rendering Worker (theme → layout → render → QA → autofix → upload) → 200 {download_url, quality_score, credits_used}

### Google Slides Flow
Rendering Worker → slides.presentations.create() → presentations.batchUpdate() (all slides) → For charts: create temp Sheets spreadsheet → link chart into Slides → return slides_url + presentation_id
