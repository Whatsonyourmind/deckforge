# DeckForge X/Twitter Threads

---

## Thread 1: Technical Build Story

**Tweet 1/6:**
I built a presentation API because every existing option is broken.

python-pptx: 530 open issues, manual pixel positioning
Gamma/Tome: beautiful output, zero API access
LLM-generated code: overflows guaranteed, one abstraction too many

So I built DeckForge -- send JSON, get a polished .pptx.

**Tweet 2/6:**
The core insight: slide layout is a constraint satisfaction problem, not a coordinate problem.

Instead of hardcoding x/y positions, each slide type defines constraints. A kiwisolver engine resolves them at render time.

Result: content overflow is handled automatically. No more clipped text or broken layouts.

**Tweet 3/6:**
32 slide types. 23 universal (title, bullets, chart, table, comparison, timeline, funnel, matrix, org chart). 9 finance-specific (DCF summary, comp table, returns waterfall, deal overview, capital structure).

Each type has a typed Pydantic schema. No guessing what fields go where.

**Tweet 4/6:**
The QA pipeline runs 5 passes before any deck ships:

1. Contrast validation (WCAG AA)
2. Overflow detection
3. Alignment consistency
4. Color scheme coherence
5. Readability scoring

Average quality score: 97%.

**Tweet 5/6:**
Why finance? Because PE firms and banks generate massive volumes of standardized decks per deal.

IC memos, teasers, CIMs, board updates. The format is rigid and repetitive. Perfect for automation.

The 9 finance slide types encode the domain conventions analysts actually use.

**Tweet 6/6:**
Open source. 808 tests. FastAPI backend. TypeScript SDK on npm.

Also has an MCP server so AI agents can generate presentations natively, and x402 micropayments so agents can pay per-call in USDC.

GitHub: github.com/Whatsonyourmind/deckforge
Service: sales-gray-eight.vercel.app

---

## Thread 2: Market Analysis

**Tweet 1/7:**
The presentation automation market is broken. Here is why.

There are 30+ million PowerPoint presentations created every day. The tooling for generating them programmatically has barely improved in a decade.

**Tweet 2/7:**
Option A: python-pptx.

Last meaningful update: years ago. 530 open issues. You manually specify x/y coordinates in EMUs (English Metric Units). No layout engine. No theme system. No chart rendering.

If your text is longer than expected, it overflows. Silently.

**Tweet 3/7:**
Option B: GUI tools (Gamma, Tome, Beautiful.ai).

Good output quality. But zero API access. You cannot call them from code, a workflow, or an agent. They are design tools, not infrastructure.

**Tweet 4/7:**
Option C: Ask an LLM to write python-pptx code.

This is generating code that generates slides -- one abstraction too many. The LLM does not know rendered text dimensions. Overflow is guaranteed. And you get inconsistent layouts every time.

**Tweet 5/7:**
The gap: an API that accepts structured data and returns a polished deck.

No GUI. No code generation. No manual positioning.

Send content in, get a rendered .pptx out.

**Tweet 6/7:**
This gap matters most in finance.

PE and IB teams generate hundreds of standardized presentations per year. IC memos, quarterly updates, deal teasers. The content changes; the structure does not.

Firms spend $500-2K per IC memo in implicit analyst time on formatting alone.

**Tweet 7/7:**
I built DeckForge to fill this gap.

32 slide types. Constraint-based layout. 5-pass QA. Finance-specific slides for DCF, comps, waterfalls.

Available as a managed service or an API.

Service: sales-gray-eight.vercel.app
GitHub: github.com/Whatsonyourmind/deckforge

---

## Thread 3: x402 and Autonomous Agent Payments

**Tweet 1/6:**
HTTP status code 402: Payment Required.

It has existed since 1997. It was "reserved for future use."

29 years later, x402 finally makes it real. And it changes how AI agents consume paid APIs.

**Tweet 2/6:**
The current model for API billing:

1. Human visits a website
2. Enters a credit card
3. Gets an API key
4. Configures the key in their agent

This breaks when the agent is autonomous. Agents do not have credit cards. They have wallets.

**Tweet 3/6:**
x402 flow:

1. Agent hits endpoint without credentials
2. Server returns 402 with a USDC price
3. Agent signs a payment authorization on Base L2
4. Agent retries with a PAYMENT-SIGNATURE header
5. Server verifies, settles on-chain, processes request

No signup. No API key. No human in the loop.

**Tweet 4/6:**
I integrated x402 into DeckForge -- my presentation generation API.

Render a deck: $0.05
Generate from prompt: $0.15

An agent that discovers DeckForge via MCP can pay per-call in USDC without ever creating an account.

**Tweet 5/6:**
This is dual-path auth:

- Human developers: Unkey API keys, Stripe subscriptions ($79/mo)
- AI agents: x402 per-call payments, no signup required

Both paths hit the same render pipeline. x402 requests skip rate limiting -- per-call payment is inherently self-throttling.

**Tweet 6/6:**
The direction is clear: agents that discover tools (MCP) and pay for them (x402) without human intervention.

DeckForge is one implementation. The pattern applies to any API.

Full technical writeup:
dev.to/whatsonyourmind/how-i-built-an-x402-monetized-mcp-server-for-ai-presentation-generation-4a6i
