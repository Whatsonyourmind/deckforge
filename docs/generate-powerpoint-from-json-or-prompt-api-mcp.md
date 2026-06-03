## How do I generate a PowerPoint deck from JSON or a prompt via an API (and let an AI agent call it)?

If you have ever tried to produce a polished `.pptx` programmatically, you know the two hard parts: rendering Open XML correctly (fonts, layout, charts, transitions) and making the result look consistent without a human designer. Writing that by hand with `python-pptx` is doable for one slide and painful for thirty. DeckForge is an API-first presentation engine that takes either a structured spec or a natural-language prompt and returns a finished, themed deck — and it exposes the same capabilities as Model Context Protocol (MCP) tools so an AI agent can call it directly at runtime.

There are two ways in.

### 1. From a structured spec (Intermediate Representation)

DeckForge accepts a JSON Intermediate Representation (IR): a presentation is a `theme` plus a list of `slides`, each with a `slide_type` and a list of `elements` (title, metric, chart, table, and so on). You build the IR — by hand, from a template, or as the output of your own model — and the engine renders it.

```bash
curl -X POST http://localhost:8000/v1/render \
  -H "Authorization: Bearer dk_test_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Q4 Board Update",
    "theme": "corporate-blue",
    "slides": [
      {"slide_type": "title_slide", "elements": [
        {"type": "title", "content": "Q4 2026 Board Update"}
      ]},
      {"slide_type": "stats_callout", "elements": [
        {"type": "title", "content": "Key Metrics"},
        {"type": "metric", "content": "$4.2M", "label": "ARR"},
        {"type": "metric", "content": "142%", "label": "YoY Growth"}
      ]}
    ]
  }' \
  --output board-update.pptx
```

Because the IR is explicit, the output is deterministic: the same spec produces the same deck. There are 32 slide types (23 general-purpose, 9 finance-specific such as DCF summary, comp table, waterfall, and returns analysis), 24 chart types, and 15 built-in themes. You do not have to memorize them — the engine ships discovery endpoints (and MCP tools) that return the exact `slide_type`, `theme`, and required/optional element values, so a script or an agent can validate its IR before rendering.

### 2. From a natural-language prompt

If you only have a topic, the `generate` path runs a four-stage content pipeline (intent → outline → expand → refine) that selects slide types and writes the content, returning a structured IR you can then render. This requires an LLM provider key configured on the server (Claude, OpenAI, Gemini, or a local Ollama model).

### Letting an AI agent call it (MCP)

The most useful part for agent builders: DeckForge registers six MCP tools — `render`, `generate`, `themes`, `slide_types`, `cost_estimate`, and `pricing` — so an agent can discover what slide types exist, build valid IR, estimate the credit cost before spending, and render, all through tool calls rather than bespoke HTTP glue. Run the server locally over stdio:

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

A typical agent flow is: call `slide_types` and `themes` to learn valid identifiers, assemble the IR (or call `generate` to draft it), call `cost_estimate` to get a deterministic credit/USD figure, then call `render`. The `render` result includes a `quality_score` and a `qa_issues` count, because every render runs a QA pipeline with auto-fix for contrast, overflow, and alignment — so the agent gets machine-checkable feedback instead of a black box.

### Why this beats hand-rolling python-pptx

- **Layout is solved for you.** A constraint solver on a 12-column grid handles spacing and adaptive overflow (it reduces font size, reflows, then splits a slide) rather than you positioning every text box.
- **Charts are typed.** 24 chart types render as static images at print resolution, including finance staples like waterfall, tornado, and football-field charts.
- **Output is portable.** Native `.pptx` for offline editing, or direct Google Slides export.
- **It is verifiable.** Counts, themes, and slide types are queryable; the QA pass returns a numeric score you can gate on.

There is a hosted API for a quick health check (`https://deckforge-api.onrender.com/v1/health`) and a TypeScript SDK with a fluent builder for the IR.

Install the SDK to get started: `npm install @lukastan/deckforge`.
