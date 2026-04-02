---
title: How I Built an x402-Monetized MCP Server for AI Presentation Generation
published: false
tags: mcp, ai, typescript, python
---

# How I Built an x402-Monetized MCP Server for AI Presentation Generation

AI agents can write code, search the web, query databases, and manage files. But ask one to create a PowerPoint deck and you get a code block with python-pptx boilerplate that positions shapes by pixel offset. The output looks like a 2003 corporate template, and it breaks the moment content overflows a text box.

I built [DeckForge](https://github.com/Whatsonyourmind/deckforge) to fix this: an API-first presentation generation platform with an MCP server that gives AI agents real slide creation capabilities. And because I wanted autonomous agents to pay per-call without API key management, I integrated x402 -- the HTTP-native micropayment protocol that settles in USDC on Base L2.

This article covers the architecture, the MCP integration, and how x402 payments work in practice.

## The Problem

There are three ways to generate slides programmatically today:

1. **python-pptx** -- the standard library. It gives you element-level control, but you manually position every shape (x, y, width, height in EMUs). There's no layout engine, no theme system, no chart rendering. It has 530 open issues on GitHub and the last meaningful update was years ago.

2. **GUI tools like Gamma and Tome** -- beautiful output, but zero API access. You can't call them from code or an agent.

3. **Ask an LLM to write python-pptx code** -- this sort of works, but the LLM doesn't know the actual dimensions of rendered text, so content overflow is guaranteed. And you're generating code that generates slides, which is one abstraction too many.

The gap is: send structured data, get a polished deck. That's DeckForge.

## Architecture

DeckForge is a FastAPI service with a JSON intermediate representation (IR) at the core:

```
Client (curl / SDK / MCP agent)
    |
    v
FastAPI API (/v1/render, /v1/generate)
    |
    +-- Auth middleware (Unkey API keys OR x402 payments)
    +-- Rate limiter (Redis token bucket)
    +-- Credit billing (reserve -> render -> deduct/release)
    |
    v
Render Pipeline (sync < 10 slides, async via ARQ workers)
    |
    +-- Layout engine (kiwisolver constraint solver, 12-col grid)
    +-- Theme resolver (15 YAML themes, WCAG AA contrast)
    +-- Chart renderer (24 types via Plotly at 300 DPI)
    +-- QA pipeline (5 passes: contrast, overflow, alignment, ...)
    |
    v
Output: .pptx file (or Google Slides via API)
```

The IR schema uses Pydantic discriminated unions. There are 32 slide types -- 23 universal (title, bullets, chart, table, comparison, timeline, funnel, matrix, org chart, stats callout, etc.) and 9 finance-specific (DCF summary, comp table, waterfall, deal overview, capital structure, market landscape, risk matrix, investment thesis, returns analysis).

The key insight: **layout is a constraint satisfaction problem, not a coordinate problem.** Instead of hardcoding positions, each slide type defines layout constraints (e.g., "title is anchored to top, content fills remaining space, metrics are evenly distributed"). Kiwisolver resolves these into coordinates at render time, and the overflow handler cascades through font reduction -> reflow -> slide splitting if content doesn't fit.

## MCP Integration

The [Model Context Protocol](https://modelcontextprotocol.io/) is how AI agents discover and invoke tools. DeckForge exposes 6 MCP tools via a FastMCP server:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "DeckForge",
    instructions=(
        "DeckForge is an API for generating and rendering executive-ready "
        "presentations. Use these tools to create PowerPoint decks from "
        "natural language prompts or structured IR."
    ),
)

@mcp.tool()
async def render(
    ir_json: str,
    theme: str = "corporate-blue",
    output_format: str = "pptx",
) -> dict:
    """Render a Presentation IR into a PowerPoint file.

    Takes a JSON string conforming to the DeckForge IR schema and
    produces a rendered PPTX. Returns slide count, quality score,
    and file size.
    """
    return await render_presentation(ir_json, theme, output_format)


@mcp.tool()
async def generate(
    prompt: str,
    slide_count: int = 10,
    theme: str = "corporate-blue",
) -> dict:
    """Generate a complete presentation from a natural language prompt.

    Transforms a text description into a fully structured presentation
    with professional layouts, content, and charts.
    """
    return await generate_presentation(prompt, slide_count, theme)


@mcp.tool()
async def themes() -> list[dict]:
    """List all 15 available themes."""
    return await list_themes()


@mcp.tool()
async def slide_types(category: str | None = None) -> list[dict]:
    """List 32 slide types. Filter by 'universal' or 'finance'."""
    return await list_slide_types(category)


@mcp.tool()
async def cost_estimate(ir_json: str) -> dict:
    """Estimate credit cost for rendering a presentation."""
    return await estimate_cost(ir_json)


@mcp.tool()
async def pricing() -> dict:
    """Get subscription tiers and x402 per-call rates."""
    return await get_pricing()
```

To use DeckForge with Claude Desktop or any MCP-compatible client, add this to your config:

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

Now Claude can do things like:

> "Create a 12-slide PE deal memo for a $500M healthcare LBO with a DCF summary, comp table, and returns waterfall. Use the finance-pro theme."

The agent calls `generate`, gets back a rendered PPTX, and the user downloads an actual PowerPoint file -- not a code snippet.

## x402: Machine-Native Payments

Here's the interesting part. Traditional API billing assumes a human signs up, enters a credit card, and manages an API key. But autonomous AI agents don't have credit cards. They have wallets.

[x402](https://x402.org) is an HTTP payment protocol that brings the `402 Payment Required` status code to life. The flow:

1. **Agent hits a protected endpoint without credentials.** DeckForge returns `402` with a pricing schedule:

```json
{
  "error": "payment_required",
  "x402": {
    "version": "1.0",
    "currency": "USDC",
    "network": "eip155:8453",
    "facilitator": "https://x402.org/facilitator",
    "recipient": "0x...",
    "price_usd": "0.05",
    "all_prices": {
      "POST /v1/render": "0.05",
      "POST /v1/generate": "0.15"
    }
  }
}
```

2. **Agent constructs a payment proof** -- a signed USDC transfer authorization on Base L2.

3. **Agent retries the request with a `PAYMENT-SIGNATURE` header.** DeckForge middleware verifies the payment via the x402 facilitator, settles it on-chain, and processes the request.

The middleware implementation is dual-path:

```python
async def x402_or_apikey_auth(
    request: Request,
    payment_sig: str | None = Security(PAYMENT_SIG_HEADER),
    api_key_header: str | None = Security(API_KEY_HEADER),
) -> AuthContext:
    """Dual auth: x402 payment OR API key.

    Priority:
    1. PAYMENT-SIGNATURE header -> x402 verify/settle
    2. X-API-Key header -> Unkey or DB auth
    3. Neither -> 402 with pricing info
    """
    if payment_sig and settings.X402_ENABLED:
        price = get_x402_price(request.method, request.url.path)
        return await _verify_x402_payment(request, payment_sig, price)

    if api_key_header:
        return await get_api_key(db, api_key_header)

    raise HTTPException(
        status_code=402,
        detail=_build_402_response(request.method, request.url.path),
    )
```

x402-authenticated requests skip rate limiting entirely -- per-call payment is inherently self-throttling. The agent pays $0.05 per render and $0.15 per generate. No subscription, no credit card, no API key signup.

This matters because the direction of AI tooling is toward autonomous agent workflows. An agent that can discover a tool via MCP and pay for it via x402 doesn't need human intervention at any step.

## TypeScript SDK

For human developers who prefer a typed client over raw curl, there's a TypeScript SDK on npm:

```bash
npm install @lukastan/deckforge
```

The SDK uses an immutable builder pattern:

```typescript
import { DeckForge, Presentation, Slides } from "@lukastan/deckforge";

const client = new DeckForge({ apiKey: "dk_test_..." });

const deck = Presentation.create("Q4 Board Update", "corporate-blue")
  .addSlide(
    Slides.titleSlide({
      title: "Q4 2026 Board Update",
      subtitle: "Acme Corp -- Confidential",
    })
  )
  .addSlide(
    Slides.statsCallout({
      title: "Key Metrics",
      metrics: [
        { value: "$4.2M", label: "ARR" },
        { value: "142%", label: "YoY Growth" },
        { value: "94%", label: "Retention" },
      ],
    })
  );

const pptx = await client.render(deck);
// pptx is a Buffer containing the .pptx file
```

The generate endpoint supports SSE streaming so you can show progress:

```typescript
const stream = client.generate({
  prompt: "PE deal memo for a $500M LBO of a healthcare platform",
  theme: "finance-pro",
});

for await (const event of stream) {
  console.log(`${event.stage}: ${event.message}`);
}
// intent: Analyzing prompt...
// outline: Creating 12-slide deal memo...
// expand: Generating slide content...
// refine: Running QA pipeline (5 passes)...
// complete: Deck ready for download
```

Full type coverage for all 32 slide types and 24 chart types. Every `Slides.*` method is typed to its specific element schema, so you get autocomplete and compile-time validation.

## The Finance Angle

The finance vertical is deliberate, not accidental. PE firms, investment banks, and consulting firms generate massive volumes of standardized presentations: IC memos, teasers, CIMs, board decks, quarterly reviews. The formatting is rigid, repetitive, and time-consuming.

The 9 finance slide types encode domain conventions:
- **DCF summary** -- valuation ranges with assumption labels
- **Comp table** -- peer comparison with conditional formatting (green/red for relative positioning)
- **Returns waterfall** -- bridge chart showing entry to exit value creation
- **Deal overview** -- standardized transaction summary layout
- **Capital structure** -- debt/equity stack visualization

These aren't generic templates -- they're structured slide types with typed fields that match how finance professionals think about the data.

## Current State and What's Next

This is v0.1. The API is live at `https://deckforge-api.onrender.com`, 808 tests passing, MIT licensed. Pre-revenue, sole developer.

What works well:
- IR-to-PPTX rendering is solid -- layout engine handles most content gracefully
- Finance slide types produce output that looks close to what you'd see from a real deal team
- MCP integration works with Claude Desktop

What needs work:
- NL-to-IR content generation quality varies by LLM provider
- Google Slides output path is less polished than PPTX
- x402 payment flow is implemented but untested in production with real agent wallets
- Need more themes and better chart styling

If you work on AI agents, MCP tooling, or generate presentations programmatically, I'd appreciate feedback on the API design and output quality.

**Links:**
- GitHub: [github.com/Whatsonyourmind/deckforge](https://github.com/Whatsonyourmind/deckforge)
- API: [deckforge-api.onrender.com](https://deckforge-api.onrender.com)
- npm SDK: [@lukastan/deckforge](https://www.npmjs.com/package/@lukastan/deckforge)
- Landing page: [landing-two-beta-63.vercel.app](https://landing-two-beta-63.vercel.app)
- API docs: [deckforge-api.onrender.com/docs](https://deckforge-api.onrender.com/docs)
