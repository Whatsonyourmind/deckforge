# @deckforge/sdk

[![npm version](https://img.shields.io/npm/v/@deckforge/sdk)](https://www.npmjs.com/package/@deckforge/sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5+-3178c6)](https://www.typescriptlang.org/)

**Executive-ready presentations, one API call away.**

Generate and render professional PowerPoint decks from TypeScript with an immutable builder API, 32 slide types, 15 themes, and real-time streaming.

```bash
npm install @deckforge/sdk
```

---

## Quick Start

```typescript
import { DeckForge, Presentation, Slide } from '@deckforge/sdk';

const df = new DeckForge({ apiKey: 'dk_live_...' });

const pptx = await df.render(
  Presentation.create('Q4 Results')
    .theme('corporate-blue')
    .addSlide(Slide.title({ title: 'Q4 2026', subtitle: 'Board Presentation' }))
    .addSlide(Slide.bullets({
      title: 'Key Metrics',
      items: ['Revenue +23% YoY', 'EBITDA $4.2M', 'NRR 118%'],
    }))
    .build()
);

console.log(pptx.download_url); // https://api.deckforge.io/v1/files/...
```

Five lines of code. A board-ready deck.

---

## Features

- **32 Slide Types** -- Title, bullets, charts, tables, comparisons, timelines, org charts, and 9 finance-specific types (DCF, comps, waterfall, deal overview, returns analysis, capital structure, market landscape, risk matrix, investment thesis).

- **15 Built-in Themes** -- Professionally designed themes with WCAG AA contrast validation: corporate-blue, executive-dark, finance-pro, minimal-light, modern-gradient, and more.

- **24 Chart Types** -- Bar, line, pie, donut, scatter, bubble, waterfall, funnel, treemap, radar, tornado, football field, sensitivity, heatmap, Sankey, Gantt, sunburst, and combo charts.

- **Immutable Builder API** -- Fluent, type-safe construction of presentations. Every mutation returns a new instance -- no side effects, easy composition.

- **Real-time Streaming** -- Stream AI-generated presentation progress via SSE. Watch slides appear in real time.

- **Finance Vertical** -- Purpose-built slide types for investment banking, private equity, and equity research: comp tables, DCF summaries, waterfall bridges, deal overviews, and returns analysis.

---

## Pricing

| Tier | Price | Credits/mo | Rate Limit | Overage |
|------|-------|------------|------------|---------|
| **Starter** | Free | 50 | 10 req/min | $0.50/credit |
| **Pro** | $79/mo | 500 | 60 req/min | $0.30/credit |
| **Enterprise** | Custom | 10,000+ | 300 req/min | $0.10/credit |

**x402 Per-Call Pricing** (machine-to-machine, no subscription required):

| Operation | Price |
|-----------|-------|
| Render presentation | $0.05 |
| Generate from prompt | $0.15 |
| Estimate cost | Free |
| List themes / slide types | Free |

---

## API Reference

### DeckForge Client

```typescript
import { DeckForge } from '@deckforge/sdk';

const df = new DeckForge({
  apiKey: 'dk_live_...',        // Required
  baseUrl: 'https://api.deckforge.io', // Optional
  timeout: 30_000,              // Optional (ms)
  maxRetries: 2,                // Optional
});
```

#### Core Methods

| Method | Description |
|--------|-------------|
| `df.render(ir)` | Render a Presentation IR to PPTX. Returns `RenderResult` with `download_url`. |
| `df.renderToBuffer(ir)` | Render and download as `ArrayBuffer`. |
| `df.estimate(ir)` | Estimate credit cost before rendering. Returns `CostEstimate`. |
| `df.getJob(jobId)` | Poll async job status for large presentations. |

#### Deck Operations

| Method | Description |
|--------|-------------|
| `df.decks.list(opts?)` | List saved decks with pagination. |
| `df.decks.get(id)` | Get deck details by ID. |
| `df.decks.getIR(id)` | Get the raw IR for a deck. |
| `df.decks.delete(id)` | Delete a deck. |
| `df.decks.appendSlides(id, slides)` | Append slides to an existing deck. |
| `df.decks.replaceSlide(id, index, slide)` | Replace a single slide at an index. |
| `df.decks.reorderSlides(id, order)` | Reorder slides by providing new index array. |
| `df.decks.retheme(id, theme)` | Apply a new theme to an existing deck. |

#### Generation

| Method | Description |
|--------|-------------|
| `df.generate.start(prompt, opts?)` | Start AI generation from natural language prompt. |
| `df.generate.stream(prompt, opts?)` | Stream generation progress as `AsyncGenerator<ProgressEvent>`. |

---

## Builder API

### Presentation

```typescript
import { Presentation } from '@deckforge/sdk';

const ir = Presentation.create('Annual Review')
  .theme('executive-dark')
  .language('en')
  .addSlide(/* ... */)
  .addSlide(/* ... */)
  .build();
```

The builder is immutable -- every method returns a new `PresentationBuilder` instance. Call `.build()` to produce the final `PresentationIR` object.

### Slide Factories

All 32 slide types have typed factory functions:

```typescript
import { Slide } from '@deckforge/sdk';

// Universal slides
Slide.title({ title: 'Hello World', subtitle: 'Subtitle' })
Slide.agenda({ title: 'Agenda', items: ['Topic 1', 'Topic 2'] })
Slide.bullets({ title: 'Key Points', items: ['Point A', 'Point B'] })
Slide.sectionDivider({ title: 'Section 2' })
Slide.keyMessage({ title: 'Revenue grew 42% YoY' })
Slide.twoColumnText({ title: 'Before & After', left: '...', right: '...' })
Slide.comparison({ title: 'Options', headers: [...], rows: [...] })
Slide.timeline({ title: 'Milestones', items: [...] })
Slide.processFlow({ title: 'Workflow', items: [...] })
Slide.orgChart({ title: 'Leadership' })
Slide.teamSlide({ title: 'Our Team' })
Slide.quoteSlide({ title: 'Quote text', attribution: 'Author' })
Slide.imageWithCaption({ title: 'Product', imageUrl: '...' })
Slide.iconGrid({ title: 'Services', items: [...] })
Slide.statsCallout({ title: 'Metrics', kpis: [...] })
Slide.tableSlide({ title: 'Data', headers: [...], rows: [...] })
Slide.chart({ title: 'Revenue', chart: Chart.bar({ ... }) })
Slide.matrix({ title: 'Priority Matrix', headers: [...], rows: [...] })
Slide.funnel({ title: 'Sales Funnel', items: [...] })
Slide.mapSlide({ title: 'Global Presence' })
Slide.thankYou({ title: 'Thank You', contact: '...' })
Slide.appendix({ title: 'Appendix' })
Slide.qAndA({ title: 'Questions?' })

// Finance slides
Slide.dcfSummary({ title: 'DCF', headers: [...], rows: [...] })
Slide.compTable({ title: 'Comps', headers: [...], rows: [...] })
Slide.waterfallChart({ title: 'EBITDA Bridge', chart: Chart.waterfall({ ... }) })
Slide.dealOverview({ title: 'Transaction', headers: [...], rows: [...] })
Slide.returnsAnalysis({ title: 'Returns', headers: [...], rows: [...] })
Slide.capitalStructure({ title: 'Cap Structure', headers: [...], rows: [...] })
Slide.marketLandscape({ title: 'TAM/SAM/SOM', items: [...] })
Slide.riskMatrix({ title: 'Risks', headers: [...], rows: [...] })
Slide.investmentThesis({ title: 'Thesis', items: [...] })
```

### Chart Factories

All 24 chart types:

```typescript
import { Chart } from '@deckforge/sdk';

// Standard charts
Chart.bar({ categories: ['Q1', 'Q2'], series: [{ name: 'Rev', values: [10, 15] }] })
Chart.stackedBar({ ... })
Chart.groupedBar({ ... })
Chart.horizontalBar({ ... })
Chart.line({ ... })
Chart.multiLine({ ... })
Chart.area({ ... })
Chart.stackedArea({ ... })
Chart.pie({ categories: ['A', 'B'], values: [60, 40] })
Chart.donut({ ... })
Chart.scatter({ points: [{ x: 1, y: 2 }] })
Chart.bubble({ ... })
Chart.combo({ ... })
Chart.radar({ ... })

// Finance charts
Chart.waterfall({ categories: ['Start', '+Rev', '-Cost', 'End'], values: [100, 30, -10, 120] })
Chart.funnel({ stages: ['Leads', 'Qualified', 'Closed'], values: [1000, 250, 50] })
Chart.treemap({ ... })
Chart.tornado({ ... })
Chart.footballField({ ... })
Chart.sensitivityTable({ ... })
Chart.heatmap({ ... })
Chart.sankey({ ... })
Chart.gantt({ ... })
Chart.sunburst({ ... })
```

### Element Factories

For advanced slide construction:

```typescript
import { Element } from '@deckforge/sdk';

Element.heading('Title Text')
Element.subheading('Subtitle')
Element.body('Paragraph text...')
Element.bullets(['Item 1', 'Item 2', 'Item 3'])
Element.numberedList(['Step 1', 'Step 2'])
Element.table({ headers: ['Col A', 'Col B'], rows: [['1', '2']] })
Element.kpiCard({ label: 'Revenue', value: '$42M' })
Element.callout({ text: 'Important note', style: 'info' })
Element.image({ url: 'https://...', alt: 'Description' })
```

---

## Streaming

Generate presentations with real-time progress updates:

```typescript
const df = new DeckForge({ apiKey: 'dk_live_...' });

for await (const event of df.generate.stream(
  'Create a 15-slide pitch deck for a fintech startup',
  { slide_count: 15, theme: 'modern-gradient' }
)) {
  console.log(`[${event.stage}] ${(event.progress * 100).toFixed(0)}%`);

  if (event.stage === 'complete') {
    console.log('Download:', event.download_url);
  }
}
```

Progress stages: `parsing` -> `outlining` -> `writing` -> `rendering` -> `complete`

---

## Error Handling

The SDK throws typed errors for all failure modes:

```typescript
import {
  DeckForgeError,
  AuthenticationError,
  ValidationError,
  RateLimitError,
  InsufficientCreditsError,
  NotFoundError,
} from '@deckforge/sdk';

try {
  await df.render(ir);
} catch (err) {
  if (err instanceof RateLimitError) {
    // Automatic retry with backoff (up to maxRetries)
    console.log('Rate limited, retrying...');
  } else if (err instanceof AuthenticationError) {
    console.error('Invalid API key');
  } else if (err instanceof ValidationError) {
    console.error('IR schema error:', err.message);
  } else if (err instanceof InsufficientCreditsError) {
    console.error('Upgrade your plan or add credits');
  }
}
```

All errors extend `DeckForgeError` with a `statusCode` property. The client automatically retries on 429 (rate limit) and 5xx errors up to `maxRetries` times with exponential backoff.

---

## Finance Slides

DeckForge has first-class support for financial presentations:

```typescript
import { DeckForge, Presentation, Slide, Chart } from '@deckforge/sdk';

const df = new DeckForge({ apiKey: 'dk_live_...' });

const deck = Presentation.create('Acme Corp - Investment Memo')
  .theme('finance-pro')
  .addSlide(Slide.title({
    title: 'Acme Corp',
    subtitle: 'Investment Committee Memorandum',
  }))
  .addSlide(Slide.investmentThesis({
    title: 'Investment Thesis',
    items: [
      'Market leader in $12B addressable market',
      '30% recurring revenue with 95% net retention',
      'Clear path to 25%+ EBITDA margins by 2028',
    ],
  }))
  .addSlide(Slide.compTable({
    title: 'Public Comparable Companies',
    headers: ['Company', 'EV/Revenue', 'EV/EBITDA', 'P/E'],
    rows: [
      ['Peer A', '8.2x', '22.1x', '35.4x'],
      ['Peer B', '6.5x', '18.3x', '28.7x'],
      ['Peer C', '9.1x', '25.0x', '41.2x'],
      ['Median', '8.2x', '22.1x', '35.4x'],
    ],
  }))
  .addSlide(Slide.dcfSummary({
    title: 'DCF Valuation Summary',
    headers: ['Metric', 'Bear', 'Base', 'Bull'],
    rows: [
      ['Enterprise Value', '$8.2B', '$10.5B', '$13.1B'],
      ['Equity Value', '$6.8B', '$9.1B', '$11.7B'],
      ['Implied Share Price', '$45', '$60', '$78'],
    ],
  }))
  .addSlide(Slide.waterfallChart({
    title: 'EBITDA Bridge',
    chart: Chart.waterfall({
      categories: ['2025 EBITDA', 'Revenue Growth', 'Cost Savings', 'Investments', '2026E EBITDA'],
      values: [100, 30, 15, -10, 135],
    }),
  }))
  .addSlide(Slide.returnsAnalysis({
    title: 'Returns Analysis',
    headers: ['Scenario', 'IRR', 'MOIC', 'Payback'],
    rows: [
      ['Base', '22%', '2.8x', '4.2 years'],
      ['Upside', '28%', '3.5x', '3.5 years'],
      ['Downside', '14%', '1.8x', '5.8 years'],
    ],
  }))
  .build();

const result = await df.render(deck);
```

---

## Benchmarks

Performance measured on standard cloud infrastructure:

| Operation | Slides | Time |
|-----------|--------|------|
| Render (PPTX) | 10 slides | <3s |
| Render (PPTX) | 30 slides | <8s |
| Generate (NL to PPTX) | 10 slides | <12s |
| Generate (NL to PPTX) | 30 slides | <15s |
| Estimate cost | Any | <100ms |
| List themes | -- | <50ms |

Sync rendering (<=10 slides) returns the file directly. Larger decks use async rendering with job polling or SSE streaming.

---

## MCP Integration

DeckForge is also available as an MCP (Model Context Protocol) server, making it discoverable by AI agents like Claude, GPT, and Copilot:

```json
{
  "mcpServers": {
    "deckforge": {
      "command": "python",
      "args": ["-m", "deckforge.mcp.server"]
    }
  }
}
```

The MCP server exposes 6 tools: `render`, `generate`, `themes`, `slide_types`, `cost_estimate`, and `pricing`.

---

## Requirements

- Node.js 18+
- TypeScript 5.5+ (for type-safe builder)

## License

MIT

---

Built by [DeckForge](https://deckforge.dev) -- Professional presentations at API speed.
