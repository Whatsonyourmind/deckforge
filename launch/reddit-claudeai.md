# r/ClaudeAI Post

**Title:** I built an MCP server that lets Claude generate real PPTX presentations — 32 slide types, charts, finance templates

**Body:**

I've been frustrated that Claude can reason about what should be in a presentation but can't actually create one. So I built DeckForge — an MCP server with 6 tools that give Claude real slide generation capabilities.

**MCP Setup:**
```json
{
  "mcpServers": {
    "deckforge": {
      "command": "npx",
      "args": ["@deckforge/mcp-server"]
    }
  }
}
```

**What Claude can do with it:**
- `generate_deck` — "Create a 10-slide pitch deck for a fintech startup" → downloads a real PPTX
- `add_slide` — Add specific slide types (title, bullets, chart, table, timeline, comparison, etc.)
- `apply_theme` — Switch between 15 curated themes
- `render_chart` — 24 chart types (bar, line, waterfall, funnel, scatter, etc.)
- `export_deck` — Output as PPTX or Google Slides
- `qa_check` — Score the deck quality (0-100) and auto-fix issues

**Why not just ask Claude to write python-pptx code?**
- python-pptx requires manual positioning of every shape (x, y, width, height in EMUs)
- No layout engine — content overflow breaks everything
- No themes, no chart rendering, no QA
- DeckForge has a constraint-based layout engine that handles dynamic content automatically

**Finance vertical:** If you work in PE/IB, there are 9 specialized slide types — DCF summary, comp tables, returns waterfall, deal structure, etc. The kind of slides that take analysts hours to format manually.

32 slide types, 24 charts, 15 themes, 808 tests. Free tier included.

GitHub: https://github.com/Whatsonyourmind/deckforge

What slide types would be most useful for your Claude workflows?
