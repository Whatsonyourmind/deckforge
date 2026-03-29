# Glama.ai Listing -- DeckForge MCP Server

## Submission URL

https://glama.ai/mcp/servers (Click "Add Server" button)

## Server Metadata

- **Server Name:** DeckForge
- **Description:** Generate executive-ready presentations via API. 32 slide types, 15 themes, native charts, finance vertical. For AI agents and developers.
- **GitHub URL:** https://github.com/Whatsonyourmind/deckforge
- **Category:** Developer Tools, Finance
- **License:** MIT
- **Transport:** stdio (default), streamable-http (production)
- **Install Command:** `pip install deckforge && python -m deckforge.mcp.server`

## Tags

presentations, slides, pptx, finance, ai-agents, api, powerpoint, charts, typescript-sdk

## Tools

| Tool | Description |
|------|-------------|
| `render` | Render Presentation IR into PowerPoint. Returns PPTX with quality score. |
| `generate` | Generate presentation from natural language prompt with AI slide selection. |
| `themes` | List 15 built-in themes (corporate, finance, minimal, etc.). |
| `slide_types` | List 32 slide types across universal and finance categories. |
| `cost_estimate` | Estimate credit cost for rendering with surcharge breakdown. |
| `pricing` | Get subscription tiers and x402 per-call machine payment rates. |

## Glama Auto-Grading Notes

Glama automatically grades servers on:
- **Security:** MIT license, no credential storage, API key via env var
- **Quality:** 6 tools with typed parameters and detailed descriptions
- **License:** MIT (open source)
- **Documentation:** Full README with usage examples, API docs, SDK reference

Ensure GitHub repo has:
- Clear README with installation instructions
- LICENSE file (MIT)
- Well-documented tool descriptions in server.py
- Example usage in SDK README

## Submission Steps

1. Go to https://glama.ai/mcp/servers
2. Click "Add Server"
3. Paste GitHub URL: https://github.com/Whatsonyourmind/deckforge
4. Fill in categories: Developer Tools, Finance
5. Submit for review
