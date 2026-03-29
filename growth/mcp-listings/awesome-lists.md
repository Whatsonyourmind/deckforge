# Awesome List Submissions -- DeckForge MCP Server

## Target Lists

### 1. wong2/awesome-mcp-servers

- **URL:** https://github.com/wong2/awesome-mcp-servers
- **Accepts PRs:** NO -- auto-synced from mcpservers.org
- **Action:** Submit via mcpservers.org (covered in mcpservers.md)
- **Status:** Will be covered by mcpservers.org submission

### 2. punkpeye/awesome-mcp-servers

- **URL:** https://github.com/punkpeye/awesome-mcp-servers
- **Accepts PRs:** Yes
- **Category:** Productivity / Data & File Systems

**Prepared PR Entry:**

```markdown
- [DeckForge](https://github.com/Whatsonyourmind/deckforge) - Generate executive-ready presentations via API. 32 slide types, 15 themes, native charts, finance vertical. For AI agents and developers.
```

**PR Steps:**
1. Fork punkpeye/awesome-mcp-servers
2. Add entry under appropriate category (Productivity or Data & File Systems)
3. Follow contribution guidelines (alphabetical order, format matching)
4. Submit PR with title: "Add DeckForge - Presentation generation MCP server"
5. PR description: Brief summary + link to repo

### 3. awesome-mcp (general)

- **URL:** Search GitHub for "awesome-mcp" repos with 100+ stars
- **Potential targets:**
  - https://github.com/appcypher/awesome-mcp-servers (if exists and active)
  - Any new curated lists in the MCP ecosystem

**Prepared Entry (generic format):**

```markdown
- [DeckForge](https://github.com/Whatsonyourmind/deckforge) - MCP server for generating executive-ready presentations. 32 slide types, 15 themes, 24 chart types, finance vertical. TypeScript SDK and x402 machine payments.
```

### 4. awesome-ai-tools

- **URL:** Search GitHub for "awesome-ai-tools" with 1000+ stars
- **Category:** Productivity / Content Generation

**Prepared Entry:**

```markdown
- [DeckForge](https://github.com/Whatsonyourmind/deckforge) - API-first presentation generation platform. 32 slide types, native charts, finance vertical. MCP server for AI agent integration, TypeScript SDK, x402 machine payments.
```

### 5. Cursor Directory

- **URL:** https://cursor.directory
- **Type:** MCP server directory specific to Cursor IDE
- **Action:** Check submission process, may auto-discover from npm/GitHub

**Prepared Entry:**

```json
{
  "name": "DeckForge",
  "description": "Generate executive-ready presentations via API. 32 slide types, 15 themes, finance vertical.",
  "github": "https://github.com/Whatsonyourmind/deckforge",
  "install": "pip install deckforge && python -m deckforge.mcp.server",
  "config": {
    "command": "python",
    "args": ["-m", "deckforge.mcp.server"],
    "env": {
      "DECKFORGE_API_KEY": "dk_live_your_key_here"
    }
  }
}
```

## Submission Priority Order

1. **mcpservers.org** -- Covers both mcpservers.org AND wong2/awesome-mcp-servers
2. **Smithery.ai** -- Largest MCP directory, auto-discovers from GitHub
3. **Glama.ai** -- Quality-graded, good for credibility
4. **punkpeye/awesome-mcp-servers** -- Direct PR, quick turnaround
5. **Cursor Directory** -- Growing IDE-specific audience
6. **OpenTools** -- Unified API layer, broader reach
7. **awesome-ai-tools** -- General AI audience
