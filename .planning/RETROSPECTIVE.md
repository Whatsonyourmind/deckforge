# DeckForge Retrospective

## Milestone: v1.0 — DeckForge MVP

**Shipped:** 2026-03-30
**Phases:** 11 | **Plans:** 31 | **Commits:** 150
**Timeline:** 2 days (2026-03-28 to 2026-03-30)
**Codebase:** 23,832 lines Python + 2,639 lines TypeScript

### What Was Built

1. Complete IR schema (32 slide types, 27 elements, 24 charts) as Pydantic discriminated unions
2. Constraint-based layout engine with kiwisolver, 9 patterns covering all slide types, adaptive overflow
3. PPTX renderer with 27 element renderers, 9 native chart types, transitions, speaker notes
4. Google Slides renderer with Sheets-backed editable charts, OAuth, temp spreadsheet cleanup
5. 4-stage content pipeline (intent → outline → expand → refine) with 4 LLM adapters
6. 10 Plotly static chart renderers + 9 finance slide type renderers (comp table, DCF, waterfall, etc.)
7. 5-pass QA pipeline with auto-fix and executive readiness scoring (0-100)
8. TypeScript SDK with fluent builder API, 67 tests, npm-publishable
9. Stripe billing (3 tiers) + x402 USDC machine payments + Unkey API key management
10. MCP server (6 tools), landing page, growth content (Show HN, Dev.to, PH kit, demo decks)
11. Production scripts (bootstrap-db, smoke-test, validate-demos, setup-stripe), CI/CD, deployment docs

### What Worked

- **Parallel wave execution** — Phases 4+5 ran simultaneously; within phases, Wave 1 plans parallelized. Saved ~40% wall-clock time.
- **GSD workflow** — Research → plan → verify → execute cycle caught issues early (INFRA-05 coverage gap, QA pipeline integration gaps).
- **Aither prior art** — 865-line production PPTX generator provided patterns for finance slides, color palettes, and element rendering.
- **IR-first architecture** — Designing the IR schema in Phase 1 made everything downstream clean: layout operates on IR, themes merge into IR, both renderers consume IR.
- **Auto mode** — YOLO + auto-advance eliminated 50+ approval gates across 31 plans.

### What Was Inefficient

- **Test fixes after QA integration** — When Phase 7 wired QA into render_pipeline (returning tuple instead of bytes), 18 tests broke across multiple files. Should have updated callers in the same plan.
- **Browser-based directory submissions** — MCP directories (Smithery, Glama) all require account creation + CAPTCHAs. Can't be automated. Should have documented as manual-only from the start.
- **Usage limit hit** — Phase 8 Wave 1 agents (SDK + billing) both hit the usage cap mid-execution. Required retry.

### Patterns Established

- **Renderer registry pattern** — `ELEMENT_RENDERERS`, `CHART_RENDERERS`, `FINANCE_SLIDE_RENDERERS`, `PATTERN_REGISTRY` all use the same dispatch-by-type dict pattern.
- **AuthContext dataclass** — Unified auth result across Unkey, DB, and x402 paths with backwards-compatible `.id` property.
- **render_pipeline() shared function** — Same pipeline for sync API path and async worker task.
- **Deep merge with protected keys** — Brand kit overlay pattern (theme + brand kit → resolved theme) with spacing/typography as protected.

### Key Lessons

1. **IR schema is the product** — Get this right in Phase 1 and everything downstream is clean.
2. **Layout engine is R&D** — Pattern-based approach with constraint verification was the right call over full general-purpose solver.
3. **Finance vertical is genuinely differentiated** — No competitor has API-first + comp tables + DCF + waterfall. This is the wedge.
4. **Agents want determinism** — Same IR → same visual output. This is why the structured API matters more than the NL endpoint.
5. **QA pipeline changes contracts** — render_pipeline returning (bytes, QAReport) instead of bytes broke 18 tests. Always update all callers when changing return types.

### Cost Observations

- Model mix: ~85% Opus (execution), ~10% Sonnet (verification/checking), ~5% Haiku (none used)
- Sessions: 1 extended session spanning 2 calendar days
- Notable: Average plan execution was 7.3 minutes. Growth/marketing plans were fastest (~3 min). Content pipeline was slowest (~13 min due to complex mocking).

---

## Cross-Milestone Trends

| Metric | v1.0 |
|---|---|
| Phases | 11 |
| Plans | 31 |
| Avg plan time | 7.3 min |
| Total build time | ~4 hours |
| Lines of code | 26,471 |
| Test lines | 13,763 |
| Test:Code ratio | 0.52 |
