"""DeckForge tools for Microsoft AutoGen agents.

Install: pip install autogen-agentchat httpx
Usage:
    from deckforge_autogen import render_presentation, generate_presentation
    assistant.register_for_llm(name="render_presentation")(render_presentation)
    user_proxy.register_for_execution(name="render_presentation")(render_presentation)

AutoGen uses function tools registered on agents. This module provides two
tool functions that wrap the DeckForge REST API for rendering structured IR
and generating presentations from natural language prompts.

API Reference: https://docs.deckforge.io/api
GitHub: https://github.com/Whatsonyourmind/deckforge
"""

from __future__ import annotations

import json
import os
from typing import Annotated, Literal

import httpx


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_BASE_URL = "https://api.deckforge.io"


def _get_headers() -> dict[str, str]:
    """Build authorization headers from environment."""
    key = os.environ.get("DECKFORGE_API_KEY", "")
    if not key:
        raise ValueError(
            "DECKFORGE_API_KEY environment variable is required. "
            "Get your key at https://deckforge.io"
        )
    return {"Authorization": f"Bearer {key}"}


def _get_base_url() -> str:
    return os.environ.get("DECKFORGE_API_URL", DEFAULT_BASE_URL)


# ---------------------------------------------------------------------------
# Tool: render_presentation
# ---------------------------------------------------------------------------

def render_presentation(
    ir_json: Annotated[str, "Presentation IR as JSON string following DeckForge schema"],
    theme: Annotated[str, "Theme name (e.g. corporate-blue, executive-dark, finance-professional)"] = "corporate-blue",
    output_format: Annotated[Literal["pptx", "gslides"], "Output format"] = "pptx",
) -> str:
    """Render a DeckForge IR JSON into a downloadable presentation.

    Use this when you have structured presentation data (IR JSON with
    schema_version, metadata, theme, slides). The DeckForge engine handles
    layout, theming, charts, and quality assurance automatically.

    Supports 32 slide types including finance types: comp_table, dcf_summary,
    waterfall_chart, deal_overview, returns_analysis, capital_structure,
    market_landscape, investment_thesis, risk_matrix.

    Returns download URL, slide count, quality score, and file size.
    """
    try:
        ir_data = json.loads(ir_json)
    except json.JSONDecodeError as exc:
        return f"Error: Invalid JSON — {exc}"

    ir_data["theme"] = {"name": theme}

    try:
        with httpx.Client(
            base_url=_get_base_url(),
            headers=_get_headers(),
            timeout=120.0,
        ) as client:
            response = client.post(
                "/v1/render",
                json=ir_data,
                params={"output_format": output_format},
            )
            response.raise_for_status()
            result = response.json()
            return (
                f"Presentation rendered successfully.\n"
                f"Download URL: {result['download_url']}\n"
                f"Slides: {result['slide_count']}\n"
                f"Quality Score: {result['quality_score']}/100\n"
                f"File Size: {result['file_size_bytes']} bytes"
            )
    except httpx.HTTPStatusError as exc:
        return f"Error: DeckForge API returned {exc.response.status_code} — {exc.response.text}"
    except Exception as exc:
        return f"Error: {type(exc).__name__} — {exc}"


# ---------------------------------------------------------------------------
# Tool: generate_presentation
# ---------------------------------------------------------------------------

def generate_presentation(
    prompt: Annotated[str, "Natural language description of the presentation to create"],
    slide_count: Annotated[int, "Target number of slides (5-30)"] = 10,
    theme: Annotated[str, "Theme name for the generated deck"] = "corporate-blue",
    output_format: Annotated[Literal["pptx", "gslides"], "Output format"] = "pptx",
) -> str:
    """Generate a complete presentation from a natural language prompt.

    Describe the presentation you need — audience, topic, key data points.
    DeckForge will parse intent, create an outline, expand each slide,
    and render the final deck with professional layout and quality checks.

    Examples:
    - "Q4 board update for $50M ARR SaaS with 40% growth"
    - "PE deal memo for $200M LBO of specialty chemicals company"
    - "Startup pitch deck for AI-powered legal tech platform"
    - "McKinsey-style market entry strategy for Southeast Asia fintech"

    Returns download URL, slide count, and quality score.
    """
    if not prompt.strip():
        return "Error: prompt cannot be empty."

    try:
        with httpx.Client(
            base_url=_get_base_url(),
            headers=_get_headers(),
            timeout=120.0,
        ) as client:
            response = client.post(
                "/v1/generate",
                json={
                    "prompt": prompt,
                    "slide_count": slide_count,
                    "theme": theme,
                    "output_format": output_format,
                },
            )
            response.raise_for_status()

            # Parse SSE stream for final result
            lines = response.text.strip().split("\n")
            last_data = None
            for line in lines:
                if line.startswith("data:"):
                    last_data = line[5:].strip()

            if last_data:
                result = json.loads(last_data)
                return (
                    f"Presentation generated successfully.\n"
                    f"Download URL: {result.get('download_url', 'N/A')}\n"
                    f"Slides: {result.get('slide_count', slide_count)}\n"
                    f"Quality Score: {result.get('quality_score', 'N/A')}/100"
                )

            return f"Generation completed. Response: {response.text[:500]}"

    except httpx.HTTPStatusError as exc:
        return f"Error: DeckForge API returned {exc.response.status_code} — {exc.response.text}"
    except Exception as exc:
        return f"Error: {type(exc).__name__} — {exc}"


# ---------------------------------------------------------------------------
# Tool: list_themes
# ---------------------------------------------------------------------------

def list_themes() -> str:
    """List all available DeckForge presentation themes.

    Returns theme names and descriptions. Use a theme name when calling
    render_presentation or generate_presentation.
    """
    try:
        with httpx.Client(
            base_url=_get_base_url(),
            headers=_get_headers(),
            timeout=30.0,
        ) as client:
            response = client.get("/v1/themes")
            response.raise_for_status()
            themes = response.json()
            lines = ["Available DeckForge themes:\n"]
            for t in themes:
                lines.append(f"  - {t['name']}: {t['description']}")
            return "\n".join(lines)
    except Exception as exc:
        return f"Error listing themes: {exc}"


# ---------------------------------------------------------------------------
# Tool: estimate_cost
# ---------------------------------------------------------------------------

def estimate_cost(
    ir_json: Annotated[str, "Presentation IR as JSON string to estimate cost for"],
) -> str:
    """Estimate the credit cost of rendering a presentation.

    Pass the IR JSON and get back the credit cost and USD equivalent
    before committing to a render call.
    """
    try:
        ir_data = json.loads(ir_json)
    except json.JSONDecodeError as exc:
        return f"Error: Invalid JSON — {exc}"

    try:
        with httpx.Client(
            base_url=_get_base_url(),
            headers=_get_headers(),
            timeout=30.0,
        ) as client:
            response = client.post("/v1/estimate", json=ir_data)
            response.raise_for_status()
            result = response.json()
            return (
                f"Cost Estimate:\n"
                f"Credits: {result['credits']}\n"
                f"USD Equivalent: ${result['usd_equivalent']}"
            )
    except Exception as exc:
        return f"Error estimating cost: {exc}"


# ---------------------------------------------------------------------------
# AutoGen Agent Example
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Two-agent collaboration: analyst + designer create a board deck
    #
    # Prerequisites:
    #   pip install autogen-agentchat httpx
    #   export DECKFORGE_API_KEY=dk_live_xxx
    #   export OPENAI_API_KEY=sk-xxx  (or OAI_CONFIG_LIST)

    from autogen import AssistantAgent, ConversableAgent, UserProxyAgent

    # Configuration for the LLM
    llm_config = {
        "config_list": [{"model": "gpt-4o", "api_key": os.environ.get("OPENAI_API_KEY")}],
        "temperature": 0,
    }

    # Agent 1: Investment Analyst (orchestrates the workflow)
    analyst = AssistantAgent(
        name="InvestmentAnalyst",
        system_message=(
            "You are a senior investment analyst. Your job is to:\n"
            "1. Define the presentation structure and content\n"
            "2. Ask the PresentationDesigner to generate the deck using DeckForge\n"
            "3. Review the output quality score\n\n"
            "When creating presentations, be specific about:\n"
            "- Target audience (board, LPs, IC committee)\n"
            "- Key metrics and data points\n"
            "- Slide types needed (comp tables, DCF, waterfall charts)\n"
            "- Visual theme preference"
        ),
        llm_config=llm_config,
    )

    # Agent 2: Presentation Designer (has DeckForge tools)
    designer = AssistantAgent(
        name="PresentationDesigner",
        system_message=(
            "You are a presentation design specialist with access to DeckForge. "
            "Use the generate_presentation function to create decks from prompts, "
            "or render_presentation to render structured IR JSON. "
            "Always aim for quality scores above 80/100."
        ),
        llm_config=llm_config,
    )

    # User proxy for executing tool calls
    user_proxy = UserProxyAgent(
        name="UserProxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=5,
        is_termination_msg=lambda x: "TERMINATE" in (x.get("content", "") or ""),
    )

    # Register DeckForge tools
    for func in [render_presentation, generate_presentation, list_themes, estimate_cost]:
        analyst.register_for_llm(description=func.__doc__)(func)
        designer.register_for_llm(description=func.__doc__)(func)
        user_proxy.register_for_execution()(func)

    # Start the conversation
    user_proxy.initiate_chat(
        analyst,
        message=(
            "Create a 12-slide PE deal memo deck for a $150M acquisition of "
            "a B2B payments company. Include: deal overview, company profile, "
            "comp table with EV/EBITDA and EV/Revenue multiples for 5 comps, "
            "DCF summary with sensitivity analysis, value creation bridges, "
            "and investment thesis. Use the finance-professional theme."
        ),
    )
