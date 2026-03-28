# DeckForge

## What This Is

DeckForge is an API-first platform for generating executive-ready presentations, outputting both PPTX files and native Google Slides. It serves AI agents via a structured IR (Intermediate Representation) API and humans via a natural language endpoint. The finance vertical (IC decks, deal one-pagers, comp tables) is the wedge into high-value enterprise clients; horizontal presentation types (pitch decks, board updates, strategy presentations) provide scale.

## Core Value

Any agent or human can produce a board-ready presentation in a single API call — with professional layout, consistent branding, and verified quality — without design skills or manual formatting.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Structured IR API that accepts JSON and renders slides
- [ ] Natural language endpoint that generates content + renders slides
- [ ] PPTX output via python-pptx with native editable charts
- [ ] Google Slides output via Slides API with Sheets-backed charts
- [ ] Constraint-based layout engine (not fixed templates)
- [ ] 15 curated professional themes with YAML definitions
- [ ] Brand kit overlay system (colors, fonts, logo on any theme)
- [ ] 32 slide types (23 universal + 9 finance vertical)
- [ ] Model-agnostic LLM orchestration (Claude, GPT, Gemini, Ollama)
- [ ] 5-pass QA pipeline with auto-fix and executive readiness scoring
- [ ] TypeScript SDK with fluent builder API published to npm
- [ ] Tiered subscription billing (Starter/Pro/Enterprise) with credit usage
- [ ] API key + OAuth 2.0 authentication
- [ ] Async workers (ARQ/Redis) for content generation and rendering
- [ ] SSE streaming for generation progress
- [ ] Webhook callbacks for async completion
- [ ] Batch operations (multiple decks, theme variations)
- [ ] Composable deck operations (append, replace, reorder, retheme slides)
- [ ] Finance vertical: DCF summary, comp table, waterfall, deal overview, returns analysis
- [ ] Self-describing API (discovery endpoints for themes, slide types, capabilities)

### Out of Scope

- Mobile app — API-first, consumers build their own UI
- Real-time collaborative editing — Google Slides handles this natively
- Video/animation authoring — static presentation generation only
- Custom LLM fine-tuning — use general-purpose models with prompt engineering
- White-label hosting — API only, no hosted presentation viewer
- Template marketplace — curated themes only for quality control

## Context

- **Prior art:** Aither (Project 2) has 865-line production PPTX generator with institutional-grade output, python-pptx 1.0.2, IC decks, deal one-pagers, AitherBranding dataclass, AI presentation service with Claude integration
- **Target market:** AI agents (primary buyer), enterprise teams, financial services, consulting firms
- **Competitive landscape:** Beautiful.ai (beautiful but dumb), Gamma (AI but limited API), SlidesAI (basic), none with agent-first API + finance vertical + QA pipeline
- **Pricing model:** Tiered subscriptions with credit-based usage — agents prefer per-call costs over subscriptions
- **Tech ecosystem:** python-pptx (PPTX), Google Slides API + Sheets API (native Google), FastAPI (HTTP), ARQ + Redis (async), PostgreSQL (persistence), S3/R2 (storage)

## Constraints

- **Tech stack**: Python FastAPI backend + TypeScript SDK — python-pptx is battle-tested, Google Slides Python client is official
- **Architecture**: Modular monolith with async workers — clean module boundaries, extractable to microservices later
- **Output fidelity**: Every deck must pass QA before delivery — no clipped text, no broken charts, no brand violations
- **Agent compatibility**: Structured API must be deterministic — same IR input produces same visual output
- **Performance**: Structured render <=10 slides must complete in <3s (sync); NL generation is always async with SSE

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python FastAPI + TS SDK (not hybrid) | python-pptx is strongest PPTX lib, Google Slides Python client is official, AI/ML is Python-native | — Pending |
| Modular monolith (not microservices) | Ship fast, scale when needed, IR schema enforces module boundaries | — Pending |
| IR as the product backbone | Structured API = IR; NL endpoint produces IR; themes operate on IR; both renderers consume IR | — Pending |
| Constraint-based layout (not templates) | Templates fail when content volume varies; solver adapts layout to content | — Pending |
| Model-agnostic from day 1 | Agents want to bring their own LLM keys; reduces vendor lock-in; wider market | — Pending |
| Credit-based pricing | Standard for API products sold to agents; no subscription friction for per-call usage | — Pending |
| Finance vertical as wedge | Aither experience gives genuine edge; high willingness to pay; competitors lack this depth | — Pending |
| 5-pass QA pipeline | "Executive-ready" is the brand promise; automated QA with auto-fix is the quality guarantee | — Pending |
| Curated themes + brand overlay | Opinionated themes = consistent quality; brand kit = enterprise stickiness | — Pending |
| Both PPTX + native Google Slides | PPTX is universal baseline; native Slides is premium differentiator | — Pending |

---
*Last updated: 2026-03-28 after initialization*
