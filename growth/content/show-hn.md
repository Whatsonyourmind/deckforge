# Show HN: DeckForge -- An API that generates executive-ready slides for AI agents

## Submission Details

- **Title:** Show HN: DeckForge -- An API that generates executive-ready slides for AI agents
- **URL:** https://github.com/Whatsonyourmind/deckforge
- **Text field (optional, leave blank if submitting URL):** Leave blank -- link directly to GitHub

---

## First Comment (Maker Comment -- post immediately after submission)

Hi HN, I built DeckForge because I spent years in finance watching analysts burn 3-5 hours formatting a single investment committee deck. The content was ready in 30 minutes -- the other 4 hours were spent fighting PowerPoint: aligning boxes, fixing text overflow, making charts look consistent, applying brand guidelines. Every. Single. Time.

When AI agents (Claude, GPT, Copilot) started generating content, I thought the problem was solved. It wasn't. LLMs produce great text and structured data, but they cannot produce visual documents. The output is either markdown (useless for boardroom presentations), screenshots (not editable), or raw python-pptx code (fragile, inconsistent, ugly).

DeckForge solves this. You send structured JSON (we call it an Intermediate Representation), and you get back a professionally laid-out PowerPoint file. One API call. No templates to manage. No pixel-pushing.

**What makes it technically interesting:**

- **Constraint-based layout engine.** Instead of hard-coded coordinates, every slide runs through kiwisolver (the same constraint solver Cassowary uses). Content volume determines font size, spacing, and element positions. A 3-bullet slide and a 12-bullet slide both look correct -- automatically.

- **6-layer pipeline.** IR schema validation -> layout solver -> theme resolution -> element rendering -> content pipeline -> 5-pass QA. Each layer is independent and testable.

- **5-pass QA pipeline.** Structural checks, text overflow detection (with auto-fix cascade: reduce font -> reflow -> split slide), WCAG AA contrast validation, data integrity verification (do your chart values sum correctly?), and brand compliance. Every deck gets a score 0-100.

- **32 slide types, 24 chart types.** Including 9 finance-specific types: comp tables with median highlights and conditional formatting, DCF summaries with sensitivity matrices, waterfall charts, deal overviews. Built for institutional investors who expect Goldman-quality output.

- **MCP server.** 6 tools for AI agent discovery via the Model Context Protocol. Claude Desktop, Cursor, and any MCP client can discover and use DeckForge without custom integration.

**Stack:** Python FastAPI, python-pptx, kiwisolver, Plotly (for static chart rendering), TypeScript SDK (@deckforge/sdk on npm), FastMCP.

**What it doesn't do (yet):**
- No animation or video support
- Google Slides output is functional but less polished than PPTX
- The NL-to-slides generation requires your own LLM API key (Claude, OpenAI, Gemini, or Ollama)
- No real-time collaboration (it produces files, not a SaaS editor)

**Try it:**
```bash
pip install deckforge
```

**Links:**
- GitHub: https://github.com/Whatsonyourmind/deckforge
- Landing page: https://deckforge.dev
- npm SDK: https://www.npmjs.com/package/@deckforge/sdk
- Demo decks (IR examples): https://github.com/Whatsonyourmind/deckforge/tree/master/demos

Happy to answer any questions about the architecture, the constraint solver, or the finance vertical. The codebase is fully open source.
