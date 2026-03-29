---
title: "How I Built a 6-Layer AI Slide Generation Engine"
published: true
description: "Deep dive into DeckForge's architecture: constraint-based layout with kiwisolver, 5-pass QA pipeline, 32 slide types, and why Intermediate Representations beat templates."
tags: mcp, ai, python, typescript, presentations
canonical_url: https://deckforge.dev/blog/how-i-built-deckforge
cover_image: https://deckforge.dev/images/blog/architecture-hero.png
---

# How I Built a 6-Layer AI Slide Generation Engine

I spent 5 years in finance watching smart people waste 3-5 hours formatting presentations that should take 30 minutes. The content was always ready fast. The formatting was the bottleneck: aligning text boxes, fixing overflow, adjusting chart styles, applying brand colors. Every deck. Every time.

When AI started generating content, I thought the problem was finally solved. It wasn't. LLMs produce excellent structured text, but they cannot produce visual documents. The output is markdown (useless for boardrooms), screenshots (not editable), or raw python-pptx code that produces slides so ugly you'd be embarrassed to present them.

So I built DeckForge: an API that takes structured input and produces executive-ready PowerPoint files. One call. No templates. No pixel-pushing.

This post walks through the architecture -- the 6 layers, the technical decisions, and what I learned building it.

## The Architecture: 6 Layers of Separation

DeckForge processes every presentation through 6 independent layers:

```
Input (JSON IR)
  -> Layer 1: IR Schema Validation
  -> Layer 2: Layout Engine (kiwisolver constraints)
  -> Layer 3: Theme Resolution
  -> Layer 4: Element Rendering (python-pptx / Google Slides)
  -> Layer 5: Content Pipeline (optional NL-to-IR)
  -> Layer 6: QA Pipeline (5-pass verification + auto-fix)
Output (.pptx file)
```

Each layer has a single responsibility. Each is independently testable. The layers communicate through well-defined interfaces -- primarily the Intermediate Representation (IR) and layout result objects.

Why 6 layers instead of a simpler pipeline? Because the problem has 6 genuinely independent concerns. Validation is not layout. Layout is not styling. Styling is not rendering. Conflating them -- as most slide generation tools do -- produces systems that are impossible to debug and impossible to extend.

## Layer 1: The Intermediate Representation

The IR is the backbone. Every other layer reads from it or writes to it.

```json
{
  "schema_version": "1.0",
  "metadata": { "title": "Q4 Board Update", "author": "CFO" },
  "theme": "executive-dark",
  "slides": [
    {
      "slide_type": "chart",
      "elements": [
        { "type": "text", "content": "Revenue Growth", "role": "title" },
        {
          "type": "chart",
          "chart_type": "bar",
          "data": {
            "categories": ["Q1", "Q2", "Q3", "Q4"],
            "series": [{ "name": "Revenue", "values": [12.4, 14.1, 15.8, 18.2] }]
          }
        }
      ]
    }
  ]
}
```

The IR defines 32 slide types: `title`, `bullets`, `chart`, `table`, `comparison`, `timeline`, `process`, `pyramid`, `funnel`, `quote`, `team`, `metrics`, `swot`, `closing`, and 9 finance-specific types (`comp_table`, `dcf_summary`, `waterfall_chart`, `deal_overview`, `returns_analysis`, `capital_structure`, `market_landscape`, `investment_thesis`, `risk_matrix`).

Why not templates? Because templates encode layout assumptions. A "3-bullet template" breaks when you have 8 bullets. A "financial table template" assumes a specific number of columns. Templates are rigid. The IR is flexible -- it describes *what* you want, not *how* to render it.

The IR is implemented as Pydantic v2 models with discriminated unions:

```python
class Slide(BaseModel):
    slide_type: Literal["title", "bullets", "chart", ...]
    elements: list[ElementUnion]
    speaker_notes: str | None = None
```

Pydantic handles validation, serialization, and generates the OpenAPI schema automatically. Invalid IRs get descriptive 422 errors with exact field paths.

## Layer 2: Constraint-Based Layout (The Hard Part)

This is the most technically interesting layer. Every slide runs through a constraint solver that determines element positions based on content volume.

Most slide tools use fixed coordinates:
- Title: x=50, y=30, width=860, height=60
- Body: x=50, y=110, width=860, height=400

This works until content varies. A 3-line bullet list gets the same box as a 15-line list. Result: either wasted space or text overflow.

DeckForge uses [kiwisolver](https://github.com/nucleic/kiwi), a Python binding for the Cassowary constraint-solving algorithm (the same algorithm that powers macOS Auto Layout). Instead of fixed positions, I define relationships:

```python
# Constraints for a bullets slide
solver.addConstraint(title.bottom + spacing <= body.top)
solver.addConstraint(body.bottom <= slide.height - margin)
solver.addConstraint(body.height >= min_body_height)
solver.addConstraint(title.height >= measured_title_height)
```

The solver finds positions that satisfy all constraints simultaneously. Short content gets more spacing. Long content gets tighter layout. The result always fits.

I implemented 9 layout patterns covering all 32 slide types:

| Pattern | Slide Types | Approach |
|---------|-------------|----------|
| Single Region | title, closing, quote, big_number | One content area, centered |
| Title + Body | bullets, executive_summary | Title with flexible body |
| Two Column | two_column, comparison | Left/right with equal distribution |
| Three Column | three_column | Three equal columns |
| Grid | table, metrics, icon_grid | Row/column grid system |
| Chart | chart, funnel, pyramid | Chart area + optional annotation |
| Timeline | timeline, process | Horizontal/vertical flow |
| Team | team, org_chart | Photo/name grid |
| Finance | comp_table, dcf_summary, etc. | Full-slide custom rendering |

When constraints are unsatisfiable (content genuinely won't fit), the **adaptive overflow cascade** kicks in:

1. **Reduce font size** -- 2pt steps down to minimums (10pt body, 14pt title)
2. **Reflow content** -- redistribute across available space
3. **Split slide** -- duplicate slide, divide content across both

This cascade runs automatically. No developer intervention needed.

One important detail: I add a 5% safety margin on all text measurements because font rendering differs slightly across operating systems. A title that fits on macOS might overflow by 2px on Windows. The safety margin absorbs this.

## Layer 3: Theme System

The theme system uses a 3-tier YAML structure:

```yaml
# corporate-blue.yaml
colors:
  navy: "#1A2F54"
  blue_accent: "#3B82F6"
  white: "#FFFFFF"

palette:
  primary: "$navy"
  accent: "$blue_accent"
  background: "$white"
  text: "$navy"

slide_masters:
  title:
    background: "$primary"
    title_color: "$white"
  bullets:
    background: "$background"
    title_color: "$primary"
```

Layer 1 (raw colors) defines hex values. Layer 2 (palette) creates semantic references. Layer 3 (slide masters) maps to specific slide type styling. The `ThemeResolver` processes tiers in order, resolving `$variable` references at each level.

There are 15 themes: `corporate-blue`, `executive-dark`, `finance-pro`, `minimal-light`, `modern-gradient`, and 10 more. Switching themes is a single line change in the IR -- the slide structure and content stay identical.

Brand kit overlay lets companies merge custom colors, fonts, and logos on top of any theme. Protected keys (`spacing`, `typography.scale`, `typography.line_height`) cannot be overridden to prevent breaking layout.

Every theme is WCAG AA validated at load time. Text-background combinations are checked for 4.5:1 contrast ratio (body) and 3:1 (large text). Violations get logged as warnings. This means every DeckForge deck is accessible by default.

## Layer 4: Rendering

The renderer translates layout results + theme + IR into actual PowerPoint elements. The architecture uses a registry pattern:

```python
ELEMENT_RENDERERS = {
    "text": TextRenderer(),
    "list": ListRenderer(),
    "table": TableRenderer(),
    "chart": ChartRenderer(),
    "image": ImageRenderer(),
    "shape": ShapeRenderer(),
    "timeline": TimelineRenderer(),
    "data_viz": DataVizRenderer(),
}
```

Each renderer handles one element type. The `PptxRenderer` orchestrator iterates slides, looks up the renderer for each element, and calls `render(element, position, theme, pptx_slide)`.

Charts get special treatment. 9 chart types (bar, line, pie, donut, scatter, combo, area, radar, bubble) render as **native editable charts** in PowerPoint -- users can click and edit the data. The remaining 15 types (waterfall, heatmap, Sankey, Gantt, treemap, etc.) render as **high-resolution static PNGs** via Plotly at 300 DPI. At presentation scale, the static charts are visually indistinguishable from native ones.

One war story: python-pptx (the library that writes .pptx files) has no API for combo charts. I had to inject raw Open XML (a `lineChart` element into the `plotArea`) via lxml. Similarly, donut chart hole size and slide transitions required XML manipulation because python-pptx doesn't expose those properties.

## Layer 5: Content Pipeline

This optional layer converts natural language prompts to IR through 4-stage LLM orchestration:

```
"Create a board update for Q4 2026"
  -> Intent Parser (what type, how many slides, what data)
  -> Outliner (slide-by-slide structure)
  -> Slide Writer (full content + chart data per slide)
  -> Cross-Slide Refiner (consistency, terminology, narrative flow)
```

Each stage uses structured output -- `tool_use` for Claude, `json_schema` for OpenAI, `response_schema` for Gemini. The pipeline is model-agnostic: you provide your own API key and choose your model.

The cross-slide refiner is the secret weapon. Without it, AI-generated decks have inconsistent terminology (saying "revenue" on one slide and "top-line" on another), tense switches, and redundant points. The refiner catches and fixes these in a final pass.

## Layer 6: QA Pipeline

Every deck runs through 5 automated checks before delivery:

1. **Structural Checker** -- slide count, required elements, slide type validity
2. **Text Checker** -- overflow detection, reading level, bullet consistency, title length
3. **Visual Checker** -- WCAG contrast, color consistency, spacing uniformity
4. **Data Checker** -- chart values sum correctly, percentages total 100%, table row counts match headers
5. **Brand Checker** -- fonts from approved list, colors within brand palette, logo present if required

Each checker produces issues with severity levels. The `AutoFixEngine` resolves what it can:
- Text overflow: font reduction -> reflow -> split (cascade)
- Contrast failures: linear interpolation toward black/white until WCAG AA passes
- Data errors: logged as warnings (not auto-fixed -- data integrity requires human judgment)

The `ExecutiveReadinessScorer` computes a 0-100 score across 5 categories (20 points each). A score of 85+ means the deck is board-ready. Below 70 triggers a warning.

## Results

DeckForge today:
- **32 slide types** including 9 finance-specific
- **15 themes** with WCAG AA compliance
- **24 chart types** (9 native editable + 15 static via Plotly)
- **MCP server** with 6 tools for AI agent discovery
- **TypeScript SDK** (`@deckforge/sdk` on npm) with fluent builder API
- **x402 machine payments** for AI agent per-call billing in USDC

## Try It

```bash
pip install deckforge
```

```typescript
import { DeckForge, Presentation, Slide } from '@deckforge/sdk';

const df = new DeckForge({ apiKey: 'dk_live_...' });
const pptx = await df.render(
  Presentation.create('Q4 Results')
    .theme('executive-dark')
    .addSlide(Slide.title({ title: 'Q4 2026', subtitle: 'Board Review' }))
    .addSlide(Slide.chart({
      title: 'ARR Growth',
      chart_type: 'bar',
      categories: ['Q1', 'Q2', 'Q3', 'Q4'],
      series: [{ name: 'ARR ($M)', values: [28, 35, 42, 50] }]
    }))
    .build()
);
```

Five lines. A board-ready deck.

**GitHub:** https://github.com/Whatsonyourmind/deckforge
**npm:** https://www.npmjs.com/package/@deckforge/sdk
**Landing page:** https://deckforge.dev

If you have questions about the constraint solver, the QA pipeline, or the finance vertical, I'm happy to go deeper in the comments. And if you star the repo, I'll notice and appreciate it.
