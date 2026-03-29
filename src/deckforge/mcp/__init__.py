"""DeckForge MCP (Model Context Protocol) server.

Exposes DeckForge presentation generation and rendering capabilities as MCP tools,
making DeckForge discoverable by AI agents (Claude, GPT, Copilot, etc.).

Usage:
    # Claude Desktop / stdio transport
    python -m deckforge.mcp.server

    # Production / streamable-http transport
    python -m deckforge.mcp.server --transport streamable-http
"""
