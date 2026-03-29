# Reddit Launch Posts

**Strategy:** Post to 4 subreddits with tailored content. Each post respects subreddit culture, self-promotion rules, and community norms. Post on different days to avoid appearing spammy.

---

## Post 1: r/programming

**When to post:** Tuesday 10 AM EST (high traffic, weekday)
**Flair:** Show /r/programming
**Self-promotion note:** r/programming allows project sharing. Focus on technical depth, not marketing. Link to GitHub (not landing page).

### Title

I built a constraint-based layout engine for AI-generated presentations (open source)

### Body

I've been working on DeckForge, an API that generates PowerPoint files from structured JSON input. The interesting technical problem was layout -- not just "put text in boxes" but adapting layout to content volume dynamically.

**The layout problem**

Most slide generators use templates with fixed coordinates. A "bullets template" allocates the same bounding box whether you have 3 bullets or 15. The result: either wasted space (3 bullets floating in a huge box) or text overflow (15 bullets clipped at the bottom).

I wanted content-adaptive layout, so I used kiwisolver (Python binding for the Cassowary constraint-solving algorithm -- same algorithm behind macOS Auto Layout and CSS Flexbox).

Instead of fixed positions, I define relationships:

```python
solver.addConstraint(title.bottom + spacing <= body.top)
solver.addConstraint(body.bottom <= slide.height - margin)
solver.addConstraint(body.height >= measured_title_height)
```

The solver finds positions satisfying all constraints simultaneously. Short content gets bigger fonts and more whitespace. Long content gets tighter layout.

When constraints are unsatisfiable (content genuinely won't fit), an overflow cascade runs automatically:
1. Reduce font size (2pt steps, minimum 10pt body / 14pt title)
2. Reflow content (redistribute across available space)
3. Split slide (duplicate slide, divide content)

**Architecture**

6-layer pipeline, each layer independent:

```
JSON IR -> Validation -> Layout (kiwisolver) -> Theme -> Rendering (python-pptx) -> QA
```

The IR (Intermediate Representation) defines 32 slide types. Think of it as HTML for slides -- you declare what you want, the engine determines how to render it. Pydantic v2 discriminated unions handle schema validation.

The QA pipeline runs 5 automated checks: structural integrity, text overflow detection, WCAG AA contrast validation (4.5:1 ratio), data integrity (do chart values sum correctly?), and brand compliance. An auto-fix engine handles what it can -- contrast failures get linear-interpolated toward black/white until they pass.

**Charts**

24 chart types. 9 render as native editable PowerPoint charts (bar, line, pie, etc.). 15 render as high-resolution static PNGs via Plotly (waterfall, Sankey, heatmap, Gantt, etc.). python-pptx doesn't support combo charts natively, so I inject raw Open XML (lineChart element into plotArea via lxml).

**Finance vertical**

9 finance-specific slide types: comp tables with median highlights and conditional formatting (EV/EBITDA, P/E), DCF summaries with sensitivity matrices, waterfall charts, deal overviews. Column format is auto-inferred from header keywords ("Market Cap" -> currency, "Growth" -> percentage).

**Stack:** Python FastAPI, python-pptx, kiwisolver, Plotly, Pydantic v2. TypeScript SDK on npm. MCP server for AI agent integration.

GitHub: https://github.com/Whatsonyourmind/deckforge

Happy to discuss the constraint solver implementation, the overflow cascade, or the chart XML injection. All code is MIT licensed.

---

## Post 2: r/SaaS

**When to post:** Tuesday (self-promotion allowed on Tuesdays per subreddit rules)
**Flair:** Show and Tell Tuesday

### Title

Launched DeckForge: API-first AI slide generation. Here's my zero-budget growth strategy.

### Body

I just launched DeckForge -- an API that generates executive-ready PowerPoint presentations for developers and AI agents. 32 slide types, 15 themes, 24 chart types, finance vertical.

I'm sharing my zero-budget growth strategy because this community has taught me a lot, and I think the approach is interesting for other dev-tool SaaS founders.

**The product**

DeckForge takes structured JSON and produces professional PowerPoint files. One API call. No templates. Constraint-based layout engine adapts to content volume. TypeScript SDK, MCP server for AI agents.

Pricing: Free tier (50 credits), Pro ($79/mo, 500 credits), Enterprise (custom). Plus x402 machine payments where AI agents pay per-call in USDC ($0.05/render).

**Zero-budget growth channels (ranked by expected impact)**

1. **MCP directory listings** -- DeckForge has an MCP server. Getting listed on Smithery, Glama, mcpservers.org, OpenTools, and Cursor Directory means AI agents can discover and use DeckForge automatically. This is the agent-era equivalent of SEO. Zero cost, compounding returns.

2. **GitHub SEO** -- Optimized repository with 12+ topic tags (mcp-server, presentations, pptx, ai-agents, finance, slides), descriptive README with install snippet in first 10 lines, social preview image (1280x640). Goal: appear in GitHub search for "mcp presentation" and "ai slide generation."

3. **npm keyword optimization** -- 19 search-relevant keywords on the npm package. When a developer searches "powerpoint api" or "mcp slides" on npm, DeckForge shows up.

4. **Hacker News** -- Show HN post focusing on the constraint-based layout engine (technically interesting). HN drives developer signups better than any other channel for dev tools.

5. **Dev.to articles** -- Two technical articles: architecture deep-dive and thought leadership on AI agent APIs. Dev.to has strong SEO, articles rank for long-tail searches for years.

6. **Reddit** (you're reading one of them) -- Tailored posts per subreddit: r/programming (technical), r/SaaS (business), r/artificial (AI), r/fintech (finance).

7. **Product Hunt** -- Launching Tuesday. Tagline: "Executive-ready slides via API. For AI agents & devs." First comment prepared with personal story.

8. **Agent framework integrations** -- Building tool wrappers for LangChain, CrewAI, AutoGen. When developers build agents, DeckForge is a pip install away.

9. **Finance community** -- Finance professionals are the highest-value customers. Targeting LinkedIn finance groups, Wall Street Oasis, r/fintech with comp table and DCF demos.

**Metrics so far**

Just launched, so metrics are pre-revenue. But the strategy is designed so that every channel compounds: MCP listings drive agent adoption, which drives GitHub stars, which drives npm installs, which drives pricing page visits.

The key insight: in 2026, distribution through AI agent directories (MCP, tool registries) is as important as traditional SEO. Build for agents first, humans second.

**What I would do differently**

I should have built the MCP server earlier. It's the highest-leverage distribution channel for developer tools in 2026 and I left it to Phase 9 of 10.

GitHub: https://github.com/Whatsonyourmind/deckforge

Would love feedback on the growth strategy. What am I missing?

---

## Post 3: r/artificial

**When to post:** Wednesday 10 AM EST
**Flair:** Project / Tool

### Title

Built an MCP server that lets AI agents generate executive-ready presentations

### Body

I built DeckForge, an MCP server that gives AI agents the ability to generate professional PowerPoint presentations. The idea: agents are great at generating structured content, but they cannot produce visual documents. DeckForge bridges that gap.

**How it works**

The MCP server exposes 6 tools:
- `render` -- takes a JSON Intermediate Representation, returns a PPTX file
- `generate` -- takes a natural language prompt, returns a presentation
- `themes` -- lists 15 available themes
- `slide_types` -- lists 32 slide types with schemas
- `estimate` -- estimates credit cost before rendering
- `pricing` -- returns per-call pricing

Any MCP client (Claude Desktop, Cursor, Windsurf, custom agents) can discover and use these tools. The agent doesn't need to know DeckForge exists in advance -- it discovers the tools through MCP's standard protocol.

**Example conversation in Claude Desktop:**

User: "Create a board presentation with our Q4 results: ARR $50M, growth 34%, NRR 124%, margin 81%."

Claude discovers DeckForge's `generate` tool via MCP, calls it with the prompt, receives a download URL for the rendered PPTX. The deck has 10 slides with charts, tables, and speaker notes.

**x402 machine payments**

The interesting economic question: how do autonomous agents pay for API calls? DeckForge supports x402, an HTTP-native payment protocol. Agents pay per-call in USDC on Base. No API key. No subscription. No human approval.

- Render a presentation: $0.05
- Generate from prompt: $0.15
- Discovery tools: Free

This enables fully autonomous agent pipelines. An agent monitoring a data warehouse can detect a quarterly close, generate a board update, render it to PPTX, email it to the CFO, and pay for the rendering -- all without human involvement.

**What makes the output good**

The reason agent-generated slides usually look terrible is that LLMs cannot reason about visual layout. DeckForge handles this with:

1. Constraint-based layout engine (kiwisolver) that adapts to content volume
2. 15 professionally designed themes with WCAG AA contrast compliance
3. 5-pass QA pipeline that catches text overflow, contrast violations, and data errors
4. Auto-fix engine that resolves issues before delivery

Every deck gets a quality score 0-100. The agent doesn't need to visually inspect the output -- the QA pipeline guarantees board-readiness.

**32 slide types** including 9 finance-specific (comp tables, DCF summaries, deal memos). **24 chart types** including waterfall, Sankey, Gantt, heatmap.

GitHub: https://github.com/Whatsonyourmind/deckforge

Add to your MCP config:
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

Curious to hear from people building agent pipelines -- what other output modalities do agents struggle with?

---

## Post 4: r/fintech

**When to post:** Thursday 10 AM EST
**Flair:** Open Source

### Title

Open-source API for generating IC decks, comp tables, and deal memos automatically

### Body

I built DeckForge because I watched IB and PE analysts spend 3-5 hours formatting investment committee decks that should take 30 minutes. The content was always ready fast. The formatting was the bottleneck.

DeckForge is an API that takes structured data and produces institutional-grade PowerPoint presentations. One API call. The finance vertical has 9 specialized slide types built specifically for the output that IB/PE/ER professionals need.

**Finance-specific slide types:**

1. **comp_table** -- Comparable company analysis with EV/EBITDA, P/E, revenue multiples. Median row auto-highlighted. Conditional formatting (green/red) for above/below median. Number formatting: 1.0x for multiples, $1.2B for currency, 23.4% for percentages.

2. **dcf_summary** -- DCF valuation with assumption table + sensitivity matrix. WACC vs exit multiple grid with highlighted base case cell. Implied EV range calculation.

3. **waterfall_chart** -- Revenue bridge, EBITDA bridge, or any add/subtract flow. Positive bars in green, negative in red, totals in blue. Running subtotals computed automatically.

4. **deal_overview** -- One-page deal summary: target name, sector, LTM/NTM metrics, enterprise value, multiples, source, expected close. The "front page" of every IC memo.

5. **returns_analysis** -- IRR/MOIC scenario table. Bear/base/bull cases with equity value, exit EV, and returns. Configurable hold period and leverage assumptions.

6. **capital_structure** -- Sources & uses table with debt tranches, rates, leverage multiples, and total sources.

7. **risk_matrix** -- Probability/impact grid with risk factors, scores, and mitigations.

8. **market_landscape** -- Industry overview with competitive positioning, market sizing, and secular trends.

9. **investment_thesis** -- Structured thesis with market, moat, expansion, margin, and exit pillars.

**Example: PE deal memo**

I included a demo IR for a PE IC memo (a $200M ARR healthcare SaaS acquisition). 10 slides: deal overview, investment thesis, comp table (5 comps), DCF with sensitivity, returns analysis (bear/base/bull/home run), capital structure, risk matrix, market landscape, and closing with IC recommendation.

The data is realistic -- real multiples, real capital structures, real IRR calculations. You can swap in your own deal data and have a formatted IC deck in seconds instead of hours.

**How it saves time**

An analyst workflow today:
1. Build model in Excel (30 min)
2. Copy data into PowerPoint (15 min)
3. Format tables, align boxes, fix fonts (2-3 hours)
4. Apply brand template (30 min)
5. QA pass -- find overflow, fix contrast, recheck numbers (30 min)

With DeckForge:
1. Build model in Excel (30 min)
2. Export data as JSON, call DeckForge API (30 seconds)
3. Auto-formatted, auto-QA'd, brand-compliant deck delivered

Steps 2-5 collapse from 3-4 hours to 30 seconds. For a team of 20 analysts producing 5 decks per week each, that is 300-400 hours saved per week.

**Open source:** Everything is MIT licensed. You can self-host the entire stack.

GitHub: https://github.com/Whatsonyourmind/deckforge
PE deal memo demo: https://github.com/Whatsonyourmind/deckforge/tree/master/demos/pe-deal-memo

If you're in IB/PE and want to try it with your own deal data, I'm happy to help set it up. DM me or comment below.
