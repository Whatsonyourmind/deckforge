# Show HN: DeckForge — API-first AI presentation generation (32 slide types, MCP server)

**URL:** https://github.com/Whatsonyourmind/deckforge

**Text:**

DeckForge is an API that generates PPTX presentations from structured JSON or natural language. It's built for developers and AI agents who need to produce slides programmatically.

The motivation: python-pptx is the standard for programmatic slide generation, but it's low-level (you position every shape manually) and effectively in maintenance mode (530 open issues). AI tools like Gamma and Tome are GUI-only with no API. There's nothing in between for developers who want "send JSON, get polished deck."

What it does:
- 32 slide types (23 universal + 9 finance-specific like DCF, comp tables, waterfalls)
- Constraint-based layout engine (kiwisolver) that handles dynamic content
- 15 curated themes with WCAG AA contrast validation
- 24 chart types via Plotly static rendering
- 5-pass QA pipeline that scores and auto-fixes output quality
- Multi-LLM content generation (Claude/GPT/Gemini/Ollama — BYO key)
- MCP server with 6 tools for AI agent integration
- TypeScript SDK with fluent builder
- PPTX + Google Slides output

Technical details:
- Python 3.12 / FastAPI / python-pptx / kiwisolver / Plotly+Kaleido
- 808 tests passing
- Dual auth: Unkey API keys + DB fallback
- Stripe billing + x402 USDC machine payments

Quick test (no auth, generates a 10-slide pitch deck):
```bash
curl -X POST https://api.deckforge.dev/v1/generate \
  -H 'Content-Type: application/json' \
  -d '{"prompt": "Create a pitch deck for an AI-powered logistics startup", "theme": "midnight", "slides": 10}' \
  --output pitch.pptx
```

The finance vertical is the wedge — PE firms and investment banks generate hundreds of standardized decks per deal. But the universal slide types work for any use case.

Demo decks (generated from the API, no manual editing): [link to demo output]

Looking for feedback on: (1) API design — is the IR schema intuitive? (2) output quality — do the generated PPTX files look professional? (3) what slide types or chart types should I add?

GitHub: https://github.com/Whatsonyourmind/deckforge
