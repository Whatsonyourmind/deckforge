# OpenTools Listing -- DeckForge MCP Server

## Submission URL

https://opentools.com (May require contacting the team directly)

## Server Metadata

- **Server Name:** DeckForge
- **Description:** Generate executive-ready presentations via API. 32 slide types, 15 themes, native charts, finance vertical. For AI agents and developers.
- **GitHub URL:** https://github.com/Whatsonyourmind/deckforge
- **Category:** Productivity / Developer Tools
- **License:** MIT

## OpenTools Integration Notes

OpenTools provides a unified API layer over MCP tools, meaning:
- Users can call DeckForge tools through the OpenTools unified API
- No separate MCP client setup required for OpenTools users
- Discovery is centralized -- agents find DeckForge through OpenTools search

## Tools for OpenTools Registry

| Tool Name | Input | Output | Description |
|-----------|-------|--------|-------------|
| `deckforge.render` | IR JSON, theme, format | PPTX file + metadata | Render presentation IR into PowerPoint |
| `deckforge.generate` | prompt, slide_count, theme | Job ID + progress | Generate presentation from NL prompt |
| `deckforge.themes` | (none) | Theme list | List 15 available themes |
| `deckforge.slide_types` | category (optional) | Slide type list | List 32 slide types |
| `deckforge.cost_estimate` | IR JSON | Cost breakdown | Estimate rendering credits |
| `deckforge.pricing` | (none) | Pricing tiers | Get subscription and x402 rates |

## Submission Steps

1. Visit https://opentools.com
2. Look for "Add Tool" or "Submit" option
3. If no self-serve submission, contact team via:
   - Twitter/X: @opentools
   - Email: Check website for contact
   - GitHub: Check for issues/discussions
4. Provide GitHub URL and tool descriptions
5. Follow up within 1 week if no response

## Value Proposition for OpenTools

- High-value enterprise use case (presentations)
- Finance vertical differentiates from generic tools
- x402 machine payments align with OpenTools agent-first ethos
- TypeScript SDK makes integration easy for their users
