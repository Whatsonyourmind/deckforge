# DeckForge Launch Thread (Twitter/X)

**Account:** @deckforge
**Format:** 15-tweet thread
**When to post:** Launch day, 9:00 AM EST
**Scheduling:** Use Typefully or Buffer for thread scheduling

---

## Tweet 1 (Hook)

I built an API that generates executive-ready slides for AI agents.

32 slide types. 15 themes. 24 chart types. One API call.

Here's how DeckForge works:

[THREAD]

[IMAGE: Hero screenshot showing a generated McKinsey strategy deck with corporate-blue theme, multiple slide types visible in slide sorter view]

---

## Tweet 2 (Problem)

The problem: AI agents generate excellent text.

But they cannot produce visual documents.

No layout engine. No chart rendering. No brand compliance. No quality checks.

The output is either ugly python-pptx code or markdown that no executive would accept in a boardroom.

---

## Tweet 3 (Solution - IR)

The solution: an Intermediate Representation.

Think HTML for slides. You describe WHAT goes on each slide -- not WHERE.

DeckForge handles layout, styling, charts, and quality.

Same idea as React: declare what you want, let the engine figure out how to render it.

[IMAGE: Side-by-side showing JSON IR input on left, rendered PowerPoint slide on right]

---

## Tweet 4 (SDK Code)

Five lines of TypeScript. A board-ready deck.

```typescript
const pptx = await df.render(
  Presentation.create('Q4 Results')
    .theme('executive-dark')
    .addSlide(Slide.title({ title: 'Q4 2026' }))
    .addSlide(Slide.chart({ chart_type: 'bar', ... }))
    .build()
);
```

@deckforge/sdk on npm. Fluent builder API. Full type safety.

[IMAGE: Screenshot of the TypeScript code in VS Code with IntelliSense showing Slide type options]

---

## Tweet 5 (Constraint Layout)

Most slide tools use templates with fixed coordinates.

DeckForge uses a constraint-based layout engine (kiwisolver).

3 bullets? Bigger fonts, more spacing.
12 bullets? Tighter layout, smaller fonts.
Text overflow? Auto-cascade: reduce font -> reflow -> split slide.

Content adapts. Always fits. Never clips.

---

## Tweet 6 (Themes)

15 professionally designed themes.

One line to switch:

```json
"theme": "executive-dark"
```

Same deck. Completely different look. All WCAG AA compliant.

corporate-blue | executive-dark | finance-pro | minimal-light | modern-gradient | startup-bold | consulting-clean | tech-dark | healthcare-soft | legal-formal | education-warm | creative-vibrant | government-formal | nonprofit-green | sales-energy

[IMAGE: Same 3-slide deck rendered in corporate-blue, executive-dark, and modern-gradient themes side by side]

---

## Tweet 7 (Finance Vertical)

Finance vertical: 9 specialized slide types for institutional-grade output.

- Comp tables with median highlights and EV/EBITDA formatting
- DCF summaries with sensitivity matrices
- Waterfall charts with positive/negative coloring
- Deal overviews, returns analysis, capital structure
- Risk matrices, market landscapes, investment theses

Built for IB analysts who spend 4 hours formatting IC decks.

[IMAGE: 2x2 grid showing comp_table, dcf_summary, waterfall_chart, and returns_analysis slides from the PE deal memo demo]

---

## Tweet 8 (Charts)

24 chart types. Native editable in PowerPoint.

Bar, line, pie, donut, scatter, bubble, combo, radar, area (native).

Waterfall, heatmap, Sankey, Gantt, treemap, tornado, football field, sensitivity, funnel, sunburst (high-res static via Plotly).

Click any native chart in PowerPoint. Edit the data. It just works.

[IMAGE: 3x3 grid showing 9 different chart types rendered by DeckForge: bar, waterfall, pie, heatmap, Gantt, funnel, Sankey, radar, treemap]

---

## Tweet 9 (QA Pipeline)

Every deck runs through a 5-pass QA pipeline before delivery:

1. Structural: slide count, required elements
2. Text: overflow detection + auto-fix
3. Visual: WCAG AA contrast (4.5:1 ratio)
4. Data: chart values sum correctly, percentages total 100%
5. Brand: fonts, colors, logo compliance

Quality score 0-100. Decks score 85+ or issues get auto-fixed.

---

## Tweet 10 (MCP)

MCP server: 6 tools for AI agent discovery.

Claude Desktop, Cursor, Windsurf -- any MCP client can discover and use DeckForge.

Tools:
- render: IR to PPTX
- generate: prompt to presentation
- themes: list available themes
- slide_types: list all 32 types
- estimate: credit cost
- pricing: per-call rates

Add to config. Start generating.

[IMAGE: Screenshot of Claude Desktop conversation where user asks "create a board update for Q4" and DeckForge MCP tool is invoked, showing the rendered deck link]

---

## Tweet 11 (x402 Payments)

x402: machine-to-machine payments.

AI agents pay per-call in USDC on Base. No API keys. No subscriptions. No human in the loop.

POST /v1/render -> 402 Payment Required ($0.05)
POST /v1/render + payment proof -> 200 OK + PPTX

The internet of payments for AI agents is here.

---

## Tweet 12 (TypeScript SDK)

TypeScript SDK with the fluent builder API every developer wants:

```typescript
Presentation.create()
  .addSlide(Slide.title({...}))
  .addSlide(Slide.comp_table({...}))
  .addSlide(Slide.chart({...}))
  .theme('finance-pro')
  .build()
```

Immutable. Every method returns a new instance. No side effects. Easy composition.

Full type safety for all 32 slide types and 24 chart types.

[IMAGE: TypeScript types dropdown showing all 32 slide type options with JSDoc descriptions]

---

## Tweet 13 (Numbers)

The numbers:

- 32 slide types (23 universal + 9 finance)
- 15 themes (WCAG AA compliant)
- 24 chart types (9 native + 15 static)
- 5-pass QA pipeline
- 6 MCP tools
- 0-100 quality scoring
- $0.05 per render (x402)
- $0.15 per NL generation
- 50 free credits on Starter tier

All open source. MIT license.

---

## Tweet 14 (Tech Stack)

Built with:

- Python FastAPI (API server)
- python-pptx (PPTX rendering)
- kiwisolver (constraint-based layout)
- Plotly (static chart rendering)
- Pydantic v2 (IR schema + validation)
- TypeScript SDK (@deckforge/sdk)
- FastMCP (MCP server)
- Stripe (billing)
- Unkey (API key management)
- x402 (machine payments)

6 months of building. 25 execution phases. ~200 files.

---

## Tweet 15 (CTA)

Try it now:

```bash
pip install deckforge
```

GitHub: github.com/Whatsonyourmind/deckforge
npm: npmjs.com/package/@deckforge/sdk
Landing: deckforge.dev
Demos: github.com/Whatsonyourmind/deckforge/tree/master/demos

Star the repo if this is useful. Every star helps us get discovered.

The era of ugly AI-generated slides is over.

[IMAGE: DeckForge logo + tagline "Executive-ready slides, one API call away" + GitHub stars badge]

---

## Image Preparation Checklist

| Tweet | Image Needed | How to Capture |
|-------|-------------|----------------|
| 1 | Hero deck screenshot | Render mckinsey-strategy demo, PowerPoint slide sorter view |
| 3 | IR input -> rendered output | JSON in editor left, rendered slide right |
| 4 | TypeScript in VS Code | SDK code with IntelliSense dropdown |
| 6 | 3 themes comparison | Same deck rendered 3 times, side by side |
| 7 | Finance slides grid | 4 finance slides from pe-deal-memo demo |
| 8 | Chart variety grid | 9 different chart types in 3x3 grid |
| 10 | Claude Desktop + MCP | Claude conversation with DeckForge tool call |
| 12 | TypeScript types | VS Code with type completion dropdown |
| 15 | Logo + CTA | Branded hero image with links |

**Total images needed: 9**
