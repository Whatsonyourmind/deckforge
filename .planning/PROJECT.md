# DeckForge

## What This Is

DeckForge is a shipped, production-ready API-first platform for generating executive-ready presentations. It outputs both PPTX and native Google Slides from a single IR (Intermediate Representation). Serves AI agents via structured API (deterministic, same input = same output) and humans via natural language endpoint. The finance vertical (IC decks, deal one-pagers, comp tables, DCF summaries) is the enterprise wedge; 23 universal slide types provide horizontal scale.

## Core Value

Any agent or human can produce a board-ready presentation in a single API call — with professional layout, consistent branding, and verified quality — without design skills or manual formatting.

## Current State (v1.0 Shipped)

- **Codebase:** 23,832 lines Python + 2,639 lines TypeScript
- **Tests:** 800+ tests across 58 files
- **Repository:** https://github.com/Whatsonyourmind/deckforge
- **Release:** v0.1.0 published

## Requirements

### Validated

- ✓ Structured IR API (32 slide types, full validation) — v1.0
- ✓ Natural language endpoint with 4-stage content pipeline — v1.0
- ✓ PPTX output via python-pptx with native editable charts — v1.0
- ✓ Google Slides output via Slides API with Sheets-backed charts — v1.0
- ✓ Constraint-based layout engine (kiwisolver, 9 patterns, adaptive overflow) — v1.0
- ✓ 15 curated themes with YAML definitions + WCAG AA contrast — v1.0
- ✓ Brand kit overlay system (colors, fonts, logo, protected properties) — v1.0
- ✓ Model-agnostic LLM (Claude, GPT, Gemini, Ollama with BYO key) — v1.0
- ✓ 5-pass QA pipeline with auto-fix and executive readiness scoring — v1.0
- ✓ TypeScript SDK with fluent builder API — v1.0
- ✓ Stripe billing (3 tiers + credits) — v1.0
- ✓ x402 machine payments (USDC on Base) — v1.0
- ✓ MCP server (6 tools for agent discovery) — v1.0
- ✓ Unkey API key management — v1.0
- ✓ Finance vertical (9 slide types, financial formatter, data ingestion) — v1.0
- ✓ Batch operations, webhooks, deck composability — v1.0
- ✓ CI/CD pipeline (GitHub Actions) — v1.0
- ✓ Landing page, growth content, agent framework integrations — v1.0

### Active

(Next milestone — see /gsd:new-milestone)

### Out of Scope

- Mobile app — API-first, consumers build their own UI
- Real-time collaborative editing — Google Slides handles this natively
- Video/animation authoring — static presentation generation only
- Custom LLM fine-tuning — prompt engineering sufficient
- White-label hosting — API only, no presentation viewer
- Template marketplace — curated themes only for quality control

## Context

- **Shipped:** v1.0 with 11 phases, 31 plans, 150 commits in 2 days
- **Architecture:** Modular monolith (FastAPI + ARQ workers + Redis + PostgreSQL + S3)
- **TAM:** $34.5B presentation + AI tools market; SAM $4.2B API-first segment
- **Competitive moat:** Only product combining API-first + constraint layout + finance vertical + QA pipeline + MCP + x402
- **Growth assets ready:** MCP directory submissions, Show HN draft, Dev.to articles, Twitter thread, Product Hunt kit, demo decks

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python FastAPI + TS SDK | python-pptx strongest, Google client official | ✓ Good |
| Modular monolith + async workers | Ship fast, scale when needed | ✓ Good |
| IR as product backbone | Deterministic, composable, format-agnostic | ✓ Good |
| Constraint layout (kiwisolver) | Adapts to content volume unlike templates | ✓ Good |
| Custom LLM adapters (not LiteLLM) | LiteLLM supply chain attack March 2026 | ✓ Good |
| x402 + Stripe dual revenue | Agents pay per-call, humans subscribe | — Pending |
| Finance vertical as wedge | Aither experience, high willingness to pay | — Pending |

---
*Last updated: 2026-03-30 after v1.0 milestone*
