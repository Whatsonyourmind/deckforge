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
    """Render a DeckForge Presentation IR into a PowerPoint file.

    Takes a JSON string conforming to the DeckForge Presentation IR schema
    and produces a rendered PPTX file. Returns slide count, quality score,
    and file size.

    Args:
        ir_json: JSON string of the Presentation IR. Must include schema_version,
            metadata, theme, and slides array.
        theme: Theme identifier. Available themes include corporate-blue,
            executive-dark, finance-pro, minimal-light, modern-gradient, etc.
            Use list_themes() to see all options.
        output_format: 'pptx' (default) or 'gslides' for Google Slides.
    """
    return await render_presentation(ir_json, theme, output_format)


@mcp.tool()
async def generate(
    prompt: str,
    slide_count: int = 10,
    theme: str = "corporate-blue",
) -> dict:
    """Generate a complete presentation from a natural language prompt.

    Transforms a text description into a fully structured presentation with
    professional slide layouts, content, and charts. Uses AI to select
    appropriate slide types, write content, and organize the narrative.

    Args:
        prompt: Natural language description of the presentation you want.
            Example: 'Create a Q4 earnings deck for the board with revenue
            trends, key metrics, and strategic outlook'.
        slide_count: Target number of slides (3-50, default: 10).
        theme: Theme identifier (default: 'corporate-blue').
    """
    return await generate_presentation(prompt, slide_count, theme)


@mcp.tool()
async def themes() -> list[dict]:
    """List all available DeckForge themes.

    Returns the catalog of 15 built-in themes with names, descriptions,
    and version info. Themes control colors, typography, spacing, and
    slide master layouts.
    """
    return await list_themes()


@mcp.tool()
async def slide_types(category: str | None = None) -> list[dict]:
    """List available slide types in DeckForge.

    DeckForge supports 32 slide types across 2 categories:
    - universal (23): title, bullets, chart, table, comparison, timeline, etc.
    - finance (9): DCF summary, comp table, waterfall, deal overview, etc.

    Args:
        category: Optional filter -- 'universal' or 'finance'. Returns all if omitted.
    """
    return await list_slide_types(category)


@mcp.tool()
async def cost_estimate(ir_json: str) -> dict:
    """Estimate the credit cost for rendering a presentation.

    Analyzes the IR to calculate costs. Pricing: base credits from slide count,
    plus surcharges for finance slides (+0.5 each), charts (+0.2 each),
    and NL generation (+2). Returns credits and USD equivalent.

    Args:
        ir_json: JSON string of the Presentation IR to estimate.
    """
    return await estimate_cost(ir_json)


@mcp.tool()
async def pricing() -> dict:
    """Get DeckForge pricing tiers and per-call rates.

    Returns subscription tiers (Starter free, Pro $79/mo, Enterprise custom)
    with credit limits and rate limits, plus x402 machine payment rates
    for per-call usage.
    """
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
