"""Example: Claude agent using DeckForge MCP server.

This demonstrates how Claude Desktop or any MCP client discovers and uses
DeckForge tools for presentation generation. DeckForge exposes 6 MCP tools
that Claude can call directly.

Prerequisites:
1. Install DeckForge: pip install deckforge
2. Add to claude_desktop_config.json (see below)
3. Set DECKFORGE_API_KEY environment variable
4. Claude will auto-discover 6 DeckForge tools

API Reference: https://docs.deckforge.io/api
GitHub: https://github.com/Whatsonyourmind/deckforge
MCP Spec: https://modelcontextprotocol.io
"""

# ============================================================================
# PART 1: Claude Desktop Configuration
# ============================================================================
#
# Add this to your claude_desktop_config.json:
#
# macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
# Windows: %APPDATA%/Claude/claude_desktop_config.json
# Linux: ~/.config/Claude/claude_desktop_config.json
#
# {
#   "mcpServers": {
#     "deckforge": {
#       "command": "python",
#       "args": ["-m", "deckforge.mcp.server"],
#       "env": {
#         "DECKFORGE_API_KEY": "dk_live_your_key_here",
#         "DECKFORGE_API_URL": "https://api.deckforge.io"
#       }
#     }
#   }
# }
#
# Alternative: using uvx (no install needed):
#
# {
#   "mcpServers": {
#     "deckforge": {
#       "command": "uvx",
#       "args": ["deckforge-mcp"],
#       "env": {
#         "DECKFORGE_API_KEY": "dk_live_your_key_here"
#       }
#     }
#   }
# }
#


# ============================================================================
# PART 2: Available MCP Tools
# ============================================================================
#
# Once configured, Claude Desktop discovers these 6 tools automatically:
#
# 1. render(ir_json, output_format, theme)
#    Render structured IR into PPTX or Google Slides.
#    Input: IR JSON with slides, elements, charts.
#    Output: Download URL + quality score.
#
# 2. generate(prompt, slide_count, theme, output_format)
#    Generate a complete presentation from natural language.
#    Input: Text prompt describing the deck.
#    Output: Download URL + quality score.
#
# 3. themes()
#    List all 15 available presentation themes.
#    Output: Theme names and descriptions.
#
# 4. slide_types(category)
#    List available slide types.
#    Input: category="universal" (23 types) or "finance" (9 types)
#    Output: Slide type names, descriptions, element types.
#
# 5. cost_estimate(ir_json)
#    Estimate credit cost before rendering.
#    Input: IR JSON.
#    Output: Credits and USD equivalent.
#
# 6. capabilities()
#    Full API capability discovery.
#    Output: All slide types, themes, chart types, output formats.
#


# ============================================================================
# PART 3: Example Conversation Flow
# ============================================================================
#
# This shows what happens when a user asks Claude to create a presentation:
#
# USER: "Create a Q4 board update for our $50M ARR SaaS company"
#
# CLAUDE (thinking): I should use DeckForge to create this. Let me first
# check what finance slide types are available.
#
# CLAUDE calls: themes()
# RESPONSE: [
#   {"name": "corporate-blue", "description": "Professional blue palette"},
#   {"name": "executive-dark", "description": "Dark theme for executive presentations"},
#   {"name": "finance-professional", "description": "Finance-optimized with data focus"},
#   ... 12 more
# ]
#
# CLAUDE calls: slide_types(category="finance")
# RESPONSE: [
#   {"name": "comp_table", "description": "Comparable companies analysis table"},
#   {"name": "dcf_summary", "description": "DCF valuation with sensitivity matrix"},
#   {"name": "waterfall_chart", "description": "Revenue bridge or value creation waterfall"},
#   {"name": "deal_overview", "description": "One-page deal summary"},
#   {"name": "returns_analysis", "description": "IRR/MOIC returns waterfall"},
#   {"name": "capital_structure", "description": "Debt/equity stack visualization"},
#   {"name": "market_landscape", "description": "Market sizing TAM/SAM/SOM"},
#   {"name": "investment_thesis", "description": "Thesis with supporting pillars"},
#   {"name": "risk_matrix", "description": "Risk assessment heat map"}
# ]
#
# CLAUDE calls: generate(
#     prompt="Q4 2025 board update for a $50M ARR B2B SaaS company showing "
#            "revenue growth from $38M to $50M, NRR of 118%, churn reduction "
#            "from 4.2% to 2.8%, EMEA expansion launch, and 2026 targets of "
#            "$72M ARR with 3 new product lines",
#     slide_count=12,
#     theme="executive-dark"
# )
# RESPONSE: {
#   "download_url": "https://api.deckforge.io/dl/abc123",
#   "slide_count": 12,
#   "quality_score": 91
# }
#
# CLAUDE calls: cost_estimate(ir_json=...)
# RESPONSE: {"credits": 8, "usd_equivalent": "0.40"}
#
# CLAUDE: "I've created your Q4 board update deck. Here's the download link:
# https://api.deckforge.io/dl/abc123
#
# The 12-slide deck includes:
# - Title slide with company branding
# - Executive summary with key metrics
# - Revenue waterfall: $38M -> $50M ARR growth
# - NRR trend: 118% with cohort analysis
# - Churn reduction: 4.2% -> 2.8%
# - EMEA expansion timeline
# - Product roadmap for 3 new lines
# - Financial projections to $72M ARR
# - Team and hiring plan
# - Risk matrix
# - Key asks and next steps
#
# Quality score: 91/100. Cost: 8 credits ($0.40)."
#


# ============================================================================
# PART 4: Programmatic Usage with Anthropic SDK + MCP Client
# ============================================================================

from __future__ import annotations

import asyncio
import json
import os
from typing import Any


async def run_claude_with_deckforge():
    """Programmatic example using Anthropic SDK with MCP tool use.

    This shows how to build a Claude-powered application that uses
    DeckForge MCP tools programmatically (not through Claude Desktop).

    Prerequisites:
        pip install anthropic httpx
        export ANTHROPIC_API_KEY=sk-ant-xxx
        export DECKFORGE_API_KEY=dk_live_xxx
    """
    try:
        import anthropic
    except ImportError:
        print("Install anthropic SDK: pip install anthropic")
        return

    client = anthropic.Anthropic()

    # Define DeckForge tools as Claude tool_use format
    tools = [
        {
            "name": "deckforge_generate",
            "description": (
                "Generate a complete presentation from a natural language prompt. "
                "DeckForge supports 32 slide types including finance-specific types "
                "(comp_table, dcf_summary, waterfall_chart). Returns a download URL."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Natural language description of the presentation",
                    },
                    "slide_count": {
                        "type": "integer",
                        "description": "Number of slides (5-30)",
                        "default": 10,
                    },
                    "theme": {
                        "type": "string",
                        "description": "Theme name (e.g., executive-dark, finance-professional)",
                        "default": "corporate-blue",
                    },
                },
                "required": ["prompt"],
            },
        },
        {
            "name": "deckforge_render",
            "description": (
                "Render a structured DeckForge IR JSON into a PPTX or Google Slides "
                "presentation. Use when you have the exact slide structure defined."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "ir_json": {
                        "type": "string",
                        "description": "Presentation IR as JSON string",
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["pptx", "gslides"],
                        "default": "pptx",
                    },
                },
                "required": ["ir_json"],
            },
        },
        {
            "name": "deckforge_themes",
            "description": "List all available DeckForge presentation themes",
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        },
    ]

    # Step 1: Ask Claude to create a presentation
    print("Asking Claude to create a PE deal memo...\n")

    messages = [
        {
            "role": "user",
            "content": (
                "Create a PE deal memo presentation for a $200M acquisition of "
                "CloudPay Systems, a B2B payments processor with $45M revenue, "
                "35% EBITDA margins, and 120% NRR. Use the finance-professional theme."
            ),
        }
    ]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        tools=tools,
        messages=messages,
    )

    # Step 2: Handle tool calls
    while response.stop_reason == "tool_use":
        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

        tool_results = []
        for tool_use in tool_use_blocks:
            print(f"Claude called: {tool_use.name}({json.dumps(tool_use.input, indent=2)})")

            # Execute the DeckForge API call
            result = await _execute_deckforge_tool(tool_use.name, tool_use.input)
            print(f"Result: {result}\n")

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": result,
            })

        # Continue conversation with tool results
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            tools=tools,
            messages=messages,
        )

    # Step 3: Print final response
    final_text = "".join(b.text for b in response.content if hasattr(b, "text"))
    print(f"Claude's response:\n{final_text}")


async def _execute_deckforge_tool(name: str, inputs: dict[str, Any]) -> str:
    """Execute a DeckForge API call based on tool name and inputs."""
    import httpx

    base_url = os.environ.get("DECKFORGE_API_URL", "https://api.deckforge.io")
    api_key = os.environ.get("DECKFORGE_API_KEY", "")

    headers = {"Authorization": f"Bearer {api_key}"}

    async with httpx.AsyncClient(base_url=base_url, headers=headers, timeout=120.0) as client:
        if name == "deckforge_generate":
            response = await client.post(
                "/v1/generate",
                json={
                    "prompt": inputs["prompt"],
                    "slide_count": inputs.get("slide_count", 10),
                    "theme": inputs.get("theme", "corporate-blue"),
                },
            )
            response.raise_for_status()
            # Parse SSE stream
            lines = response.text.strip().split("\n")
            for line in reversed(lines):
                if line.startswith("data:"):
                    data = json.loads(line[5:].strip())
                    return json.dumps(data)
            return response.text[:500]

        elif name == "deckforge_render":
            ir_data = json.loads(inputs["ir_json"])
            response = await client.post(
                "/v1/render",
                json=ir_data,
                params={"output_format": inputs.get("output_format", "pptx")},
            )
            response.raise_for_status()
            return json.dumps(response.json())

        elif name == "deckforge_themes":
            response = await client.get("/v1/themes")
            response.raise_for_status()
            return json.dumps(response.json())

        else:
            return f"Unknown tool: {name}"


# ============================================================================
# PART 5: MCP Client Library Example (for custom MCP hosts)
# ============================================================================

async def run_mcp_client_example():
    """Example using the MCP client library to connect to DeckForge MCP server.

    This is for developers building custom MCP hosts (not Claude Desktop).

    Prerequisites:
        pip install mcp deckforge
        export DECKFORGE_API_KEY=dk_live_xxx
    """
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError:
        print("Install MCP client: pip install mcp")
        return

    # Connect to DeckForge MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "deckforge.mcp.server"],
        env={
            "DECKFORGE_API_KEY": os.environ.get("DECKFORGE_API_KEY", ""),
            "DECKFORGE_API_URL": os.environ.get("DECKFORGE_API_URL", "https://api.deckforge.io"),
        },
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Discover available tools
            tools_list = await session.list_tools()
            print("Available DeckForge MCP tools:")
            for tool in tools_list.tools:
                print(f"  - {tool.name}: {tool.description}")

            # Call the themes tool
            themes_result = await session.call_tool("themes", {})
            print(f"\nThemes: {themes_result.content}")

            # Call the generate tool
            gen_result = await session.call_tool("generate", {
                "prompt": (
                    "Startup pitch deck for an AI-powered legal document review "
                    "platform targeting Am Law 200 firms. $2M ARR, 300% growth, "
                    "Series A fundraise of $15M."
                ),
                "slide_count": 12,
                "theme": "startup-vibrant",
            })
            print(f"\nGenerated deck: {gen_result.content}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("DeckForge + Claude Agent Example")
    print("=" * 60)
    print()
    print("This example demonstrates two integration patterns:")
    print()
    print("1. Anthropic SDK + tool_use (run_claude_with_deckforge)")
    print("   Claude calls DeckForge API via tool_use protocol.")
    print()
    print("2. MCP Client Library (run_mcp_client_example)")
    print("   Custom MCP host connects to DeckForge MCP server.")
    print()
    print("For Claude Desktop: just add the config snippet above")
    print("to your claude_desktop_config.json and Claude will")
    print("auto-discover all 6 DeckForge tools.")
    print()

    # Uncomment to run:
    # asyncio.run(run_claude_with_deckforge())
    # asyncio.run(run_mcp_client_example())
