# Feature Landscape

**Domain:** API-first AI slide generation platform
**Researched:** 2026-03-26

## Table Stakes

Features users expect. Missing = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| PPTX output | Universal format, every enterprise expects it | Medium | python-pptx handles this. Core pipeline. |
| Text slides (title, bullets, two-column) | Minimum viable presentation content | Low | 80% of slide content is text-based |
| Table slides | Data presentation is fundamental | Medium | python-pptx table API works but formatting is verbose |
| Basic charts (bar, line, pie) | Cannot have a presentation tool without charts | Medium | python-pptx native editable charts |
| Professional styling | "Executive-ready" is the brand promise | High | Theme engine + typography scale + color theory |
| API key authentication | API products require auth | Low | Standard FastAPI middleware |
| OpenAPI documentation | Developers expect auto-docs | Low | FastAPI provides this free |
| Rate limiting | Standard API protection | Low | Redis-backed sliding window |
| Async generation with status | NL generation takes 10-25s | Medium | ARQ + SSE streaming |
| HTTPS and CORS | Security baseline | Low | Infrastructure config |

## Differentiators

Features that set product apart. Not expected, but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Structured IR API | Agents can construct slides deterministically -- same input = same output | High | The IR schema IS the product backbone |
| Constraint-based layout | Content adapts to fit (3 bullets vs 12 bullets get different layouts) | Very High | Custom kiwisolver build. No off-the-shelf solution. |
| 5-pass QA pipeline | "No clipped text ever ships" -- automated quality guarantee | High | Text overflow, brand compliance, accessibility, data integrity |
| Finance vertical | DCF, comp tables, waterfall, deal overview -- competitors lack this depth | High | Leverages Aither production renderer experience |
| Native Google Slides output | Editable in Workspace, not just an uploaded PPTX | High | Slides API + Sheets-backed charts |
| Model-agnostic LLM | Agents bring their own keys (Claude, GPT, Gemini, Ollama) | Medium | LiteLLM abstraction layer |
| Brand kit overlay | Enterprise stickiness -- upload logo, colors, fonts once | Medium | Theme deep merge with protected properties |
| Composable operations | Append/replace/reorder/retheme slides on existing decks | Medium | IR-level operations, re-render affected slides |
| Batch operations | Generate 10 theme variations in one call | Medium | ARQ fan-out pattern |
| Self-describing API | Discovery endpoints for themes, slide types, capabilities | Low | Static metadata endpoints |
| Webhook callbacks | Async completion notifications for agent integrations | Low | ARQ result then POST to webhook URL |
| Cost estimation endpoint | Agents can estimate credit cost before generation | Low | Static cost calculation from IR metadata |

## Anti-Features

Features to explicitly NOT build.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Web-based slide editor UI | Scope creep, competing with Google Slides/PowerPoint. DeckForge is API-only. | Let users edit output in their preferred editor |
| Real-time collaboration | Google Slides handles this. Duplicating it is years of work. | Output to Google Slides for collaboration |
| Template marketplace | Quality control nightmare. Curated themes only. | 15 curated themes + brand kit overlay |
| Video/animation authoring | Different domain entirely. Static presentations only. | Support basic transitions in IR but do not render video |
| Custom LLM fine-tuning | Massive R&D cost, unclear ROI. Prompt engineering is sufficient. | Model-agnostic with optimized prompts |
| White-label hosting | Hosting a presentation viewer is not the core product | API delivers files; users host their own |
| PDF generation | Scope creep; can be added later via LibreOffice headless or client-side | Mark as future Enterprise feature |
| Mobile app | API-first product. No mobile-specific UX needed. | TypeScript SDK works in React Native if needed |
| Slide-level caching | Over-optimization that complicates IR-to-output determinism | Cache at the full deck level via request_id idempotency |

## Feature Dependencies

```
IR Schema -> PPTX Renderer -> Google Slides Renderer
IR Schema -> Layout Engine -> PPTX Renderer
IR Schema -> Layout Engine -> Google Slides Renderer
IR Schema -> Content Pipeline (produces IR)
Theme Engine -> Layout Engine (provides resolved values)
Brand Kit -> Theme Engine (overlay merge)
Chart Builder -> PPTX Renderer (native charts)
Chart Builder -> Google Slides Renderer (Sheets-backed charts)
Chart Builder -> Plotly/Kaleido (static fallback)
QA Pipeline -> PPTX Renderer (validates output)
QA Pipeline -> Layout Engine (checks overflow)
Auth System -> API Routes -> All endpoints
Billing System -> Auth System (credit checks before generation)
Webhook System -> ARQ Workers (fires on completion)
SSE Streaming -> ARQ Workers (publishes progress events)
TypeScript SDK -> OpenAPI Schema (auto-generated)
```

## MVP Recommendation

**Prioritize (Phase 1-3):**
1. IR schema with Pydantic validation (the product backbone)
2. PPTX renderer for 10 core slide types (title, bullets, two-column, table, chart, section divider, key message, stats callout, image, thank you)
3. Basic layout engine (grid-based positioning, not full constraint solving yet)
4. 3 curated themes (executive-light, startup-pitch, finance-institutional)
5. API key auth + structured /v1/render endpoint
6. Async rendering via ARQ

**Defer to Phase 4-5:**
- NL generation endpoint (requires LLM orchestration)
- Full constraint-based layout solver (start with simpler grid positioning)
- Finance vertical slide types
- Google Slides output
- Brand kit overlay
- QA pipeline

**Defer to Phase 6+:**
- TypeScript SDK
- Stripe billing
- Batch operations
- Webhook callbacks
- Remaining 22 slide types

**Rationale:** Ship a working structured render API for core slide types as fast as possible. The IR API is the product -- validate it with real agent consumers before investing in NL generation and the full feature set.

## Sources

- DeckForge Design Spec (docs/superpowers/specs/2026-03-28-deckforge-design.md) - 32 slide types, 6 intelligence layers
- [Top 5 AI Presentation APIs 2025](https://slidespeak.co/guides/top-5-ai-presentation-apis-2025) - Competitive landscape
- [Best Presentation APIs 2025](https://plusai.com/blog/best-presentation-apis) - Market comparison
- [Google Slides API Guide](https://www.flashdocs.com/post/google-slides-api-comprehensive-guide-for-developers) - Slides API capabilities and limitations
