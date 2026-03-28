# Research Summary: DeckForge

**Domain:** API-first AI slide generation platform
**Researched:** 2026-03-26
**Overall confidence:** HIGH

## Executive Summary

DeckForge's technology stack is well-defined and grounded in mature, production-proven libraries. The core rendering pipeline (python-pptx for PPTX, Google Slides API for native Slides) represents the only serious approach for these output formats in Python -- there are no meaningful alternatives to evaluate. The API framework (FastAPI) and data layer (PostgreSQL + SQLAlchemy) are industry standards with no controversy. The async architecture (ARQ + Redis) is the right choice for I/O-bound LLM and API workloads, though ARQ's maintenance-only status means monitoring Taskiq as a backup.

The most significant technical risks are: (1) the constraint-based layout engine, which is a custom build on kiwisolver with no off-the-shelf equivalent -- this will consume the most R&D time; (2) LiteLLM's recent supply chain compromise requiring pinned versions and a fallback strategy; and (3) the Google Slides chart workaround (Sheets-backed charts), which adds architectural complexity to an already multi-format rendering pipeline.

The competitive landscape validates the opportunity: no existing product combines agent-first API + finance vertical + multi-pass QA. Gamma, Beautiful.ai, and SlidesAI all target human users through GUIs. The agent-first, API-only approach is genuinely differentiated.

The TypeScript SDK strategy of auto-generating from the OpenAPI spec (via @hey-api/openapi-ts) with a hand-written fluent builder layer is the modern best practice. This keeps the SDK in sync with the API automatically while providing the developer experience that matters for adoption.

## Key Findings

**Stack:** Python 3.12 + FastAPI 0.135+ + python-pptx 1.0.2 + Google APIs + LiteLLM (pinned 1.82.6) + ARQ/Redis + PostgreSQL + Cloudflare R2 + Stripe billing. TypeScript SDK auto-generated from OpenAPI.

**Architecture:** Modular monolith with async workers. IR (Intermediate Representation) is the backbone -- all inputs produce IR, all renderers consume IR. Constraint-based layout via kiwisolver sits between IR and renderers.

**Critical pitfall:** LiteLLM supply chain attack (March 2026) -- must pin to safe version and maintain a fallback adapter strategy. Layout engine is custom R&D with no off-the-shelf solution -- budget significant time.

## Implications for Roadmap

Based on research, suggested phase structure:

1. **Foundation + IR Schema** - Build the IR Pydantic models, FastAPI skeleton, database schema, and project infrastructure first
   - Addresses: Core IR schema, API framework setup, auth basics
   - Avoids: Building on unstable foundations

2. **PPTX Rendering Engine** - Implement the python-pptx renderer for core slide types (text, tables, basic charts)
   - Addresses: Core PPTX generation, table stakes slide types
   - Avoids: Over-engineering before validating the IR-to-output pipeline works

3. **Layout Engine + Theme System** - Build the constraint-based layout solver and theme YAML system
   - Addresses: Adaptive layouts, curated themes, brand kit overlay
   - Avoids: Hard-coding positions that break when content volume changes

4. **Content Generation Pipeline** - LLM orchestration (intent -> outline -> expand -> refine), model-agnostic adapter
   - Addresses: NL endpoint, multi-model support, content intelligence
   - Avoids: Building LLM integration before the rendering pipeline is proven

5. **Chart Engine + Finance Vertical** - Native editable charts in PPTX, static fallback via Plotly, finance-specific slide types
   - Addresses: Data visualization, comp tables, waterfall charts, DCF summaries
   - Avoids: Tackling the hardest rendering challenges before core pipeline is stable

6. **Google Slides Output** - Slides API renderer with Sheets-backed charts
   - Addresses: Premium Google Slides output, editable charts via Sheets
   - Avoids: Duplicating rendering effort before PPTX pipeline is mature

7. **QA Pipeline + Polish** - 5-pass quality assurance, auto-fix, executive readiness scoring
   - Addresses: "Board-ready" brand promise, text overflow detection, brand compliance
   - Avoids: QA on half-built rendering output

8. **TypeScript SDK + Billing + Launch** - SDK generation, Stripe integration, credit system, public API
   - Addresses: @deckforge/sdk, subscription tiers, usage metering
   - Avoids: Building billing before there is something to bill for

**Phase ordering rationale:**
- IR schema must exist before any renderer can be built (phases 1-2 dependency)
- PPTX rendering before Google Slides because PPTX is the universal baseline and simpler to implement
- Layout engine before content generation because layout issues are discovered during rendering, not generation
- Charts and finance after core rendering because they build on the same renderer infrastructure
- QA after all renderers because it validates the complete pipeline
- SDK and billing last because they wrap a working product

**Research flags for phases:**
- Phase 3 (Layout Engine): NEEDS DEEP RESEARCH -- constraint-based layout for slides has no off-the-shelf solution. Study iOS Auto Layout patterns, CSS Grid spec, and academic papers on adaptive document layout.
- Phase 5 (Charts): NEEDS RESEARCH -- python-pptx chart type support gaps vs what the spec demands. Test waterfall/football field/sensitivity table feasibility early.
- Phase 6 (Google Slides): NEEDS RESEARCH -- Sheets-backed chart embedding has API rate limit implications. Test batchUpdate size limits for large presentations.
- Phase 4 (Content Pipeline): Standard patterns -- LiteLLM/provider SDKs are well-documented for structured output.
- Phase 8 (Billing): Standard patterns -- Stripe Meters + Credits API is well-documented.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All core libraries verified on PyPI with current versions. python-pptx is the only option; FastAPI is industry standard. |
| Features | HIGH | Design spec is comprehensive. 32 slide types + 6 intelligence layers are well-defined. |
| Architecture | HIGH | Modular monolith + IR backbone is the right pattern. Module boundaries are clean. |
| Pitfalls | MEDIUM | LiteLLM supply chain risk is real and documented. Layout engine complexity is the biggest unknown. |

## Gaps to Address

- **Layout engine feasibility:** No off-the-shelf constraint-based slide layout exists. Need a spike/prototype to validate kiwisolver-based approach before committing to full implementation.
- **python-pptx chart gaps:** Need hands-on testing of waterfall charts (via stacked bar workaround) and other finance-specific chart types to confirm feasibility.
- **Google Slides batchUpdate limits:** Need to verify API rate limits and maximum request sizes for presentations with 50+ slides and Sheets-backed charts.
- **LiteLLM recovery timeline:** Monitor whether the project restores trust after the March 2026 supply chain attack. May need to build custom adapter layer.
- **Kaleido Docker integration:** Need to validate Chrome/Chromium in the Docker image works reliably for Plotly static export in CI and production.
