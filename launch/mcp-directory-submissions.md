# MCP Directory Submissions -- DeckForge

Submission templates for all major MCP directories. Copy-paste ready.

---

## 1. PulseMCP

**Submission URL:** https://www.pulsemcp.com/submit

- **Server Name:** DeckForge
- **Short Description:** API-first presentation generation -- 32 slide types, 24 charts, 15 themes, finance vertical with DCF/comp tables/waterfalls.
- **Long Description:** DeckForge is an MCP server that gives AI agents the ability to generate and render executive-ready PowerPoint presentations. Agents can create decks from natural language prompts or structured JSON IR, choose from 32 slide types (including 9 finance-specific: DCF summary, comp table, returns waterfall, deal overview, capital structure, market landscape, risk matrix, investment thesis), render 24 chart types, apply 15 curated themes, estimate costs, and check pricing. Output is native PPTX or Google Slides. Supports x402 USDC micropayments for autonomous agent billing.
- **Category:** Developer Tools / Productivity
- **GitHub URL:** https://github.com/Whatsonyourmind/deckforge
- **License:** MIT
- **Transport:** stdio (Claude Desktop), streamable-http (production)
- **Install Command:**
  ```bash
  pip install deckforge
  ```
- **MCP Config:**
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
- **Tools (6):**
  | Tool | Description |
  |------|-------------|
  | `render` | Render Presentation IR into PPTX. Accepts JSON IR with theme selection. Returns slide count, quality score, file size. |
  | `generate` | Generate complete presentation from natural language prompt. AI selects slide types, writes content, organizes narrative. |
  | `themes` | List all 15 built-in themes with names, descriptions, color info. |
  | `slide_types` | List 32 slide types. Filter by category: universal (23) or finance (9). |
  | `cost_estimate` | Estimate credit cost for a given IR. Returns credits and USD equivalent with surcharge breakdown. |
  | `pricing` | Get subscription tiers (Free/Pro $79/Enterprise) and x402 per-call USDC rates. |
- **Pricing:** Free tier (50 credits/mo), Pro $79/mo (500 credits), Enterprise custom. x402 per-call: $0.05/render, $0.15/generate.
- **Tags:** presentations, slides, pptx, powerpoint, finance, charts, ai-agents, typescript-sdk

---

## 2. Glama

**Submission URL:** https://glama.ai/mcp/servers (Click "Add Server")

- **Server Name:** DeckForge
- **Description:** Generate executive-ready presentations via API. 32 slide types, 15 themes, native charts, finance vertical. For AI agents and developers.
- **GitHub URL:** https://github.com/Whatsonyourmind/deckforge
- **Categories:** Developer Tools, Finance
- **License:** MIT
- **Transport:** stdio, streamable-http
- **Install:** `pip install deckforge && python -m deckforge.mcp.server`
- **Tools:** render, generate, themes, slide_types, cost_estimate, pricing
- **Tags:** presentations, slides, pptx, finance, ai-agents, api, powerpoint, charts

**Submission steps:**
1. Go to https://glama.ai/mcp/servers
2. Click "Add Server"
3. Paste GitHub URL
4. Select categories: Developer Tools, Finance
5. Submit (Glama auto-grades on security, quality, license, docs)

---

## 3. MCP.so

**Submission URL:** https://mcp.so/submit (or email)

- **Server Name:** DeckForge
- **One-liner:** API-first AI presentation generation with 32 slide types, finance vertical, and x402 machine payments.
- **Description:** MCP server for generating and rendering PowerPoint presentations. 32 slide types (23 universal + 9 finance-specific including DCF, comp tables, waterfalls), 24 chart types, 15 themes. Supports natural language to slides, structured IR rendering, and autonomous agent billing via x402 USDC on Base L2. TypeScript SDK available on npm.
- **GitHub:** https://github.com/Whatsonyourmind/deckforge
- **Category:** Productivity / Developer Tools
- **License:** MIT
- **Install:**
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
- **Tool Count:** 6
- **Pricing:** Free tier available. Pro $79/mo. x402 per-call for agents.

---

## 4. mcpserverfinder (mcpserverfinder.com)

**Submission URL:** https://mcpserverfinder.com/submit

- **Server Name:** DeckForge
- **Tagline:** Generate executive-ready PPTX presentations from AI agents
- **Description:** DeckForge MCP server exposes 6 tools for AI-driven presentation generation. Create slides from natural language or structured JSON, with 32 slide types, 24 chart types, and 15 built-in themes. Includes a finance vertical with 9 specialized slide types for PE/IB workflows (DCF summary, comp table, waterfall chart, deal overview). Supports x402 USDC micropayments for autonomous agents.
- **GitHub:** https://github.com/Whatsonyourmind/deckforge
- **npm SDK:** @lukastan/deckforge
- **Category:** Productivity, Finance, Developer Tools
- **License:** MIT
- **Tools:** render, generate, themes, slide_types, cost_estimate, pricing
- **Install:** `pip install deckforge`
- **Config:**
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

---

## 5. AIAgentsList (aiagentslist.com)

**Submission URL:** https://aiagentslist.com/submit

- **Name:** DeckForge MCP Server
- **Type:** MCP Server / Tool
- **Short Description:** Presentation generation MCP server -- 32 slide types, 24 charts, finance vertical, x402 payments.
- **Long Description:** DeckForge provides AI agents with the ability to create professional PowerPoint presentations. The MCP server exposes 6 tools: generate presentations from natural language, render from structured IR, browse themes and slide types, estimate costs, and check pricing. Purpose-built for finance workflows with 9 specialized slide types (DCF, comp table, waterfall, deal overview, capital structure). Autonomous agents can pay per-call via x402 USDC on Base L2 without needing an API key.
- **GitHub:** https://github.com/Whatsonyourmind/deckforge
- **Pricing Model:** Freemium (Free tier: 50 credits/mo, Pro: $79/mo, x402 per-call)
- **Category:** Developer Tools, Finance, Productivity
- **Tags:** mcp, presentations, pptx, finance, ai-agents, x402

---

## 6. MCP Market (mcpmarket.com)

**Submission URL:** https://mcpmarket.com/submit

- **Server Name:** DeckForge
- **Publisher:** Luka Stanisljevic (@Whatsonyourmind)
- **Description:** Generate and render executive-ready PowerPoint decks via MCP tools. 32 slide types, 24 chart types, 15 themes, finance vertical with DCF/comp/waterfall slides. Supports x402 USDC micropayments for autonomous agent billing.
- **GitHub:** https://github.com/Whatsonyourmind/deckforge
- **License:** MIT
- **Category:** Productivity
- **Transport:** stdio, streamable-http
- **Install:**
  ```bash
  pip install deckforge
  python -m deckforge.mcp.server
  ```
- **Tools (6):** render, generate, themes, slide_types, cost_estimate, pricing
- **Pricing:** Free tier, Pro $79/mo, Enterprise custom, x402 per-call ($0.05 render, $0.15 generate)

---

## 7. GitHub modelcontextprotocol/servers

**Submission URL:** PR to https://github.com/modelcontextprotocol/servers

**PR Title:** Add DeckForge -- presentation generation server

**Entry for README.md (Community Servers section):**

```markdown
- **[DeckForge](https://github.com/Whatsonyourmind/deckforge)** - Generate and render executive-ready PowerPoint presentations. 32 slide types (including finance: DCF, comp table, waterfall), 24 chart types, 15 themes, natural language to slides, x402 machine payments.
```

**Server details for PR description:**

```
Server name: DeckForge
Repository: https://github.com/Whatsonyourmind/deckforge
Description: API-first presentation generation with 32 slide types, 24 chart types,
  15 themes, and a finance vertical. Renders PPTX from structured IR or natural
  language. Includes x402 USDC micropayments for autonomous agents.
Transport: stdio (default), streamable-http (production)
Language: Python 3.12
License: MIT
Tools: render, generate, themes, slide_types, cost_estimate, pricing
```

**PR body template:**

```markdown
## New Server: DeckForge

DeckForge is a presentation generation MCP server that creates executive-ready
PowerPoint files from natural language prompts or structured JSON.

### Tools (6)
- `render` -- Render Presentation IR to PPTX with theme selection and quality scoring
- `generate` -- Generate full presentation from a text prompt (AI slide type selection)
- `themes` -- List 15 built-in themes
- `slide_types` -- List 32 slide types (23 universal + 9 finance)
- `cost_estimate` -- Estimate credit cost for a given presentation
- `pricing` -- Get subscription tiers and x402 per-call rates

### Install
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

### Highlights
- 32 slide types including 9 finance-specific (DCF, comp table, waterfall, deal overview)
- 24 chart types via Plotly static rendering
- 15 curated themes with WCAG AA contrast validation
- 5-pass QA pipeline with auto-fix
- x402 USDC micropayments on Base L2 for autonomous agents
- TypeScript SDK on npm: @lukastan/deckforge

Repository: https://github.com/Whatsonyourmind/deckforge
License: MIT
```

---

## Submission Checklist

- [ ] PulseMCP
- [ ] Glama
- [ ] MCP.so
- [ ] mcpserverfinder
- [ ] AIAgentsList
- [ ] MCP Market
- [ ] modelcontextprotocol/servers PR
