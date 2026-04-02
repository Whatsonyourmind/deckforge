# Show HN: DeckForge -- API-first presentation generation (32 slide types, finance vertical, MCP server)

**URL:** https://github.com/Whatsonyourmind/deckforge

**Text:**

I built DeckForge because there's a gap between python-pptx (too low-level -- you position every shape manually, 530 open issues, effectively maintenance mode) and the GUI tools like Gamma/Tome (no API, no programmatic access). If you need to generate slides from code or an AI agent, there's nothing that takes structured JSON and returns a polished .pptx. So I built that.

DeckForge is a FastAPI service that accepts either a JSON intermediate representation (IR) or a natural language prompt and returns a rendered PowerPoint file. The IR schema covers 32 slide types (23 universal like title, bullets, chart, comparison, timeline, funnel, matrix -- plus 9 finance-specific: DCF summary, comp table, returns waterfall, deal overview, capital structure). Layout is handled by a kiwisolver constraint solver on a 12-column grid, so content overflow is handled automatically instead of clipping. There are 24 chart types rendered via Plotly as static PNGs at 300 DPI, 15 YAML-defined themes with WCAG AA contrast validation, and a 5-pass QA pipeline that scores output and auto-fixes issues like contrast violations or text overflow.

The finance vertical is the wedge I'm pursuing. PE firms and investment banks generate hundreds of standardized decks per deal -- IC memos, teasers, CIMs -- and the formatting is tedious, repetitive work. The 9 finance slide types encode domain conventions (e.g., comp tables with proper conditional formatting, waterfalls with correct bridge logic). But the universal slide types work fine for any presentation use case.

On the integration side: there's an MCP server with 6 tools so Claude/GPT/etc. can discover and invoke DeckForge directly, a TypeScript SDK (`@lukastan/deckforge` on npm) with a fluent builder pattern, and x402 USDC micropayments on Base L2 for autonomous AI agents that want to pay per-call instead of holding an API key. Auth is dual-path: Unkey API keys for human developers, x402 payment signatures for machines. Stripe billing handles subscriptions (Free/Pro $79/mo/Enterprise).

This is v0.1 -- the API is live on Render, the landing page is up, but it's pre-revenue and I'm the sole developer. 808 tests passing, MIT licensed.

Quick test (renders a 10-slide pitch deck, no auth required on the generate endpoint):

```bash
curl -X POST https://deckforge-api.onrender.com/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a pitch deck for an AI-powered logistics startup",
    "theme": "midnight",
    "slides": 10
  }' \
  --output pitch.pptx
```

Or render from structured IR:

```bash
curl -X POST https://deckforge-api.onrender.com/v1/render \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Q4 Board Update",
    "theme": "corporate-blue",
    "slides": [
      {
        "slide_type": "title_slide",
        "elements": [
          {"type": "title", "content": "Q4 2026 Board Update"},
          {"type": "subtitle", "content": "Acme Corp"}
        ]
      },
      {
        "slide_type": "stats_callout",
        "elements": [
          {"type": "title", "content": "Key Metrics"},
          {"type": "metric", "content": "$4.2M", "label": "ARR"},
          {"type": "metric", "content": "142%", "label": "YoY Growth"}
        ]
      }
    ]
  }' \
  --output board-update.pptx
```

Looking for feedback on: (1) API design -- is the IR schema intuitive or overengineered? (2) Output quality -- do the PPTX files look professional enough to send to a client? (3) What slide types or chart types are missing? (4) Is the x402 machine payment angle interesting or premature?

GitHub: https://github.com/Whatsonyourmind/deckforge
Landing page: https://landing-two-beta-63.vercel.app
npm SDK: https://www.npmjs.com/package/@lukastan/deckforge
API docs: https://deckforge-api.onrender.com/docs
