# Smithery.ai Listing -- DeckForge MCP Server

## Submission URL

https://smithery.ai (Submit via GitHub repo connection)

## Server Metadata

- **Server Name:** DeckForge
- **Description (160 chars):** Generate executive-ready presentations via API. 32 slide types, 15 themes, native charts, finance vertical. For AI agents and developers.
- **GitHub URL:** https://github.com/Whatsonyourmind/deckforge
- **License:** MIT
- **Transport:** stdio (default), streamable-http (production)
- **Install Command:** `pip install deckforge && python -m deckforge.mcp.server`

## Tags

presentations, slides, pptx, finance, ai-agents, api

## Tools

| Tool | Description |
|------|-------------|
| `render` | Render a DeckForge Presentation IR into a PowerPoint file. Takes JSON IR, returns PPTX with slide count, quality score, and file size. |
| `generate` | Generate a complete presentation from a natural language prompt. Transforms text into structured slides with professional layouts, content, and charts. |
| `themes` | List all 15 available DeckForge themes with names, descriptions, and version info. |
| `slide_types` | List available slide types. 32 types across universal (23) and finance (9) categories. |
| `cost_estimate` | Estimate credit cost for rendering a presentation. Base credits from slide count plus surcharges. |
| `pricing` | Get DeckForge pricing tiers (Starter free, Pro $79/mo, Enterprise custom) and x402 per-call rates. |

## Claude Desktop Config (for listing)

```json
{
  "mcpServers": {
    "deckforge": {
      "command": "python",
      "args": ["-m", "deckforge.mcp.server"],
      "env": {
        "DECKFORGE_API_KEY": "dk_live_your_key_here"
      }
    }
  }
}
```

## Submission Notes

- Smithery auto-discovers from GitHub repo -- ensure repo has MCP server metadata
- Server supports both stdio (local) and streamable-http (remote) transports
- x402 machine payments supported for per-call USDC billing
