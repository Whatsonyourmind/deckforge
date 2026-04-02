# Product Hunt Launch Brief -- DeckForge

## Tagline (60 chars max)

```
API-first slide generation for developers and AI agents
```
(56 chars)

## Description (260 chars max)

```
Generate executive-ready PowerPoint decks from JSON or natural language. 32 slide types, 24 charts, 15 themes, finance vertical (DCF, comp tables, waterfalls). MCP server for AI agents. TypeScript SDK. x402 USDC micropayments for autonomous machines. MIT licensed.
```
(265 chars -- trim to 260:)

```
Generate executive-ready PowerPoint from JSON or natural language. 32 slide types, 24 charts, 15 themes, finance vertical (DCF, comp tables, waterfalls). MCP server for AI agents. TypeScript SDK. x402 USDC micropayments for machines. MIT licensed.
```
(247 chars)

## 3 Key Features

### 1. 32 Slide Types with Finance Vertical
23 universal slide types (title, bullets, chart, comparison, timeline, funnel, matrix, org chart) plus 9 finance-specific types built for PE/IB workflows: DCF summary, comp table, returns waterfall, deal overview, capital structure. Constraint-based layout engine handles content overflow automatically.

### 2. MCP Server for AI Agents
6 MCP tools let Claude, GPT, and other agents generate real PPTX files -- not code snippets. Agents discover available themes and slide types, generate from natural language, render from structured IR, and estimate costs. One-line setup for Claude Desktop.

### 3. x402 Machine Payments
Autonomous AI agents pay per-call with USDC on Base L2 via the x402 protocol. No API key signup, no credit card, no human in the loop. $0.05/render, $0.15/generate. The API returns a 402 with pricing info, the agent signs a payment proof, and the request proceeds.

## Maker Comment Draft

```
Hi Product Hunt -- I'm Luka, and I built DeckForge because there's nothing between python-pptx (manual shape positioning, 530 open issues) and GUI tools like Gamma (no API).

The core idea: send structured JSON or a natural language prompt to an API, get back a polished .pptx file. No manual formatting, no code generation -- just data in, deck out.

I'm betting on the finance vertical as the wedge. PE firms and investment banks produce hundreds of standardized decks per deal (IC memos, teasers, CIMs). The 9 finance slide types encode the formatting conventions these teams expect -- comp tables with conditional formatting, waterfall charts with bridge logic, DCF layouts with assumption labels.

The MCP + x402 angle is forward-looking: AI agents can discover DeckForge's tools via MCP, generate a presentation, and pay for it with USDC -- no human intervention needed at any step. That's the direction I think developer tooling is headed.

This is v0.1, pre-revenue, sole developer, 808 tests. I'd love feedback on:
- Output quality -- do the generated decks look professional enough?
- API design -- is the IR schema intuitive?
- What slide types or chart types should I prioritize next?

GitHub: https://github.com/Whatsonyourmind/deckforge
API docs: https://deckforge-api.onrender.com/docs
```

## Launch Assets Needed

- [ ] Logo (240x240 PNG, no text, simple icon)
- [ ] Gallery images (1270x760 each, up to 8):
  - Screenshot: Landing page hero
  - Screenshot: Generated PPTX deck (McKinsey strategy demo)
  - Screenshot: Generated PPTX deck (PE deal memo demo)
  - Screenshot: API docs page (/docs)
  - Screenshot: MCP tools in Claude Desktop
  - Diagram: Architecture overview
- [ ] Thumbnail (240x240)
- [ ] Video/GIF (optional): curl command -> PPTX file opening in PowerPoint

## Suggested Launch Day

- **Day:** Tuesday or Wednesday (highest PH traffic)
- **Time:** 12:01 AM PST (standard PH launch time)
- **Prep:** Share with supporters 24h before for early upvotes

## Topics to Select

- Developer Tools
- Artificial Intelligence
- Productivity
- SaaS
- APIs

## Cross-Promotion Plan

- Post link on Hacker News (Show HN) same day
- Share on r/ClaudeAI, r/SideProject, r/SaaS
- Tweet thread with demo GIF
- Dev.to article published day before for SEO
