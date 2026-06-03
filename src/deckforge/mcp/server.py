"""DeckForge MCP Server.

Exposes DeckForge presentation capabilities as MCP tools for AI agent discovery.
Supports stdio transport (Claude Desktop) and streamable-http (production).

Usage:
    # stdio transport (Claude Desktop, local agents)
    python -m deckforge.mcp.server

    # streamable-http transport (production, remote agents)
    python -m deckforge.mcp.server --transport streamable-http
"""

from __future__ import annotations

import sys

from mcp.server.fastmcp import FastMCP

from deckforge.mcp.tools import (
    estimate_cost,
    generate_presentation,
    get_pricing,
    list_slide_types,
    list_themes,
    render_presentation,
)

# ---------------------------------------------------------------------------
# Create the MCP server instance
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "DeckForge",
    instructions=(
        "DeckForge is an API for generating and rendering executive-ready "
        "presentations. Use these tools to create PowerPoint decks from natural "
        "language prompts or structured IR, explore available themes and slide "
        "types, estimate costs, and check pricing."
    ),
)

# ---------------------------------------------------------------------------
# Register tools with descriptive docstrings for agent discovery
# ---------------------------------------------------------------------------


@mcp.tool()
async def render(
    ir_json: str,
    theme: str = "corporate-blue",
    output_format: str = "pptx",
) -> dict:
    """Render a structured Presentation IR (JSON) into a PowerPoint (.pptx) or Google Slides deck and run the quality pipeline over it. Use when you already have a DeckForge IR object (slides, elements, theme) and want a finished, themed deck plus a quality check. Returns slide_count, quality_score, format, rendered size_bytes, and the number of QA issues found (qa_issues). Args: ir_json (Presentation IR string with metadata, theme, slides), theme (identifier, default 'corporate-blue'; call themes to list), output_format ('pptx' default or 'gslides')."""
    return await render_presentation(ir_json, theme, output_format)


@mcp.tool()
async def generate(
    prompt: str,
    slide_count: int = 10,
    theme: str = "corporate-blue",
) -> dict:
    """Turn a natural-language prompt into a structured Presentation IR (not a rendered file) using the 4-stage content pipeline (intent, outline, expand, refine). Use when you have a topic in plain text and need slide structure and content generated before rendering — chain the returned IR into render to get a .pptx/Google Slides file. Returns title, slide_count, theme, and the full ir object. Args: prompt (what the deck should cover), slide_count (target, default 10), theme (default 'corporate-blue'). Requires at least one LLM provider key (Claude/OpenAI/Gemini/Ollama) configured on the server."""
    return await generate_presentation(prompt, slide_count, theme)


@mcp.tool()
async def themes() -> list[dict]:
    """List the built-in deck themes (currently 15) with their id, name, description, and version. Use when you need a valid theme identifier before calling generate or render, or to show a user the available visual styles. Returns a list of theme records; pass a returned id as the theme argument to render/generate. No arguments, no LLM, no cost."""
    return await list_themes()


@mcp.tool()
async def slide_types(category: str | None = None) -> list[dict]:
    """List the supported slide types (32 total: 23 universal + 9 finance) with each type's id, name, description, category, and required/optional elements. Use when building or validating IR by hand to discover which slide_type values exist and which elements each one needs before calling render. Args: category (optional 'universal' or 'finance'; omit for all). No LLM, no cost."""
    return await list_slide_types(category)


@mcp.tool()
async def cost_estimate(ir_json: str) -> dict:
    """Estimate the credit cost of rendering a given Presentation IR before you spend credits. Use when you want a deterministic, pre-flight cost for a deck — base credits are ceil(slides/10), plus +0.5 per finance slide, +0.2 per chart element, and +2 if NL generation options are present. Returns total_credits, base_credits, a surcharges breakdown, a human-readable breakdown string, and a USD equivalent (x402_usd at $0.05/credit). Args: ir_json (Presentation IR string). No LLM, free."""
    return await estimate_cost(ir_json)


@mcp.tool()
async def pricing() -> dict:
    """Return the current subscription tiers and per-call machine-payment rates. Use when an agent or user needs to know plan limits or pay-per-call pricing before committing to a workload. Returns tiers (name, display_name, credit_limit, price_usd, overage_rate_usd, rate_limit_rpm) and x402 per-call rates (render $0.05, generate $0.15, metadata calls free; protocol x402, USD). No arguments, no LLM, free."""
    return await get_pricing()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    transport: str = "stdio"
    if "--transport" in sys.argv:
        idx = sys.argv.index("--transport")
        if idx + 1 < len(sys.argv):
            transport = sys.argv[idx + 1]

    mcp.run(transport=transport)  # type: ignore[arg-type]
