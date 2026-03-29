"""DeckForge tool for CrewAI agents.

Install: pip install crewai crewai-tools httpx
Usage:
    from deckforge_crewai import DeckForgeTool
    presenter = Agent(role="Presenter", tools=[DeckForgeTool()])

This tool wraps the DeckForge REST API for use in CrewAI multi-agent
workflows. A typical pattern pairs a research agent (gathering data) with
a presentation agent (using DeckForgeTool to render the final deck).

API Reference: https://docs.deckforge.io/api
GitHub: https://github.com/Whatsonyourmind/deckforge
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional, Type

import httpx
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_BASE_URL = "https://api.deckforge.io"


# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------

class DeckForgeInput(BaseModel):
    """Input for the DeckForge presentation tool."""

    action: str = Field(
        description=(
            "Action to perform: 'generate' to create a deck from a prompt, "
            "or 'render' to render an existing IR JSON into a deck."
        )
    )
    prompt: Optional[str] = Field(
        default=None,
        description=(
            "Natural language description of the presentation (for 'generate' action). "
            "Be specific: audience, purpose, data points, slide count. "
            "Example: 'PE deal memo for $200M LBO of a specialty chemicals company "
            "with 8x EBITDA entry, 3 value creation levers, and 5-year hold period.'"
        ),
    )
    ir_json: Optional[str] = Field(
        default=None,
        description=(
            "Presentation IR as JSON string (for 'render' action). Must follow "
            "the DeckForge IR schema with schema_version, metadata, theme, slides."
        ),
    )
    slide_count: int = Field(
        default=10,
        description="Number of slides to generate (5-30). Used with 'generate' action.",
    )
    theme: str = Field(
        default="corporate-blue",
        description=(
            "Theme for the presentation. Options: corporate-blue, executive-dark, "
            "startup-vibrant, minimal-light, finance-professional, consulting-clean, "
            "tech-modern, academic-formal, and 7 more."
        ),
    )
    output_format: str = Field(
        default="pptx",
        description="Output format: 'pptx' (PowerPoint) or 'gslides' (Google Slides).",
    )


# ---------------------------------------------------------------------------
# Tool: DeckForgeTool
# ---------------------------------------------------------------------------

class DeckForgeTool(BaseTool):
    """Generate executive-ready presentations from prompts or structured IR.

    DeckForge produces board-ready slide decks with professional layout,
    consistent branding, and verified quality. Supports 32 slide types
    including 9 finance-specific types (comp tables, DCF summaries,
    waterfall charts, deal overviews).

    Two modes:
    - generate: Natural language prompt -> polished deck
    - render: Structured IR JSON -> polished deck

    Returns a download URL, slide count, and quality score.
    """

    name: str = "DeckForge Presentation Generator"
    description: str = (
        "Generate executive-ready presentations from prompts or structured IR. "
        "Supports 32 slide types including finance (comp_table, dcf_summary, "
        "waterfall_chart, deal_overview). 24 chart types. 15 curated themes. "
        "Automatic layout, theming, and 5-pass quality assurance. "
        "Use action='generate' with a prompt, or action='render' with IR JSON."
    )
    args_schema: Type[BaseModel] = DeckForgeInput

    # Constructor params
    api_key: Optional[str] = None
    base_url: Optional[str] = None

    def _get_client(self) -> httpx.Client:
        key = self.api_key or os.environ.get("DECKFORGE_API_KEY", "")
        url = self.base_url or os.environ.get("DECKFORGE_API_URL", DEFAULT_BASE_URL)
        if not key:
            raise ValueError(
                "DeckForge API key required. Set DECKFORGE_API_KEY env var "
                "or pass api_key to DeckForgeTool(api_key='dk_live_xxx')."
            )
        return httpx.Client(
            base_url=url,
            headers={"Authorization": f"Bearer {key}"},
            timeout=120.0,
        )

    def _run(
        self,
        action: str = "generate",
        prompt: str | None = None,
        ir_json: str | None = None,
        slide_count: int = 10,
        theme: str = "corporate-blue",
        output_format: str = "pptx",
    ) -> str:
        """Execute the DeckForge tool."""

        if action == "generate":
            return self._generate(prompt or "", slide_count, theme, output_format)
        elif action == "render":
            return self._render(ir_json or "{}", theme, output_format)
        else:
            return f"Error: Unknown action '{action}'. Use 'generate' or 'render'."

    def _generate(self, prompt: str, slide_count: int, theme: str, output_format: str) -> str:
        """Generate a presentation from a natural language prompt."""
        if not prompt:
            return "Error: 'prompt' is required for the 'generate' action."

        try:
            client = self._get_client()
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
                    f"Quality Score: {result.get('quality_score', 'N/A')}/100\n"
                    f"Theme: {theme}\n"
                    f"Format: {output_format.upper()}"
                )

            return f"Generation completed. Response: {response.text[:500]}"

        except httpx.HTTPStatusError as exc:
            return f"Error: DeckForge API returned {exc.response.status_code} - {exc.response.text}"
        except Exception as exc:
            return f"Error: {type(exc).__name__} - {exc}"

    def _render(self, ir_json: str, theme: str, output_format: str) -> str:
        """Render a structured IR into a presentation."""
        try:
            ir_data = json.loads(ir_json)
        except json.JSONDecodeError as exc:
            return f"Error: Invalid JSON in ir_json - {exc}"

        if theme:
            ir_data["theme"] = {"name": theme}

        try:
            client = self._get_client()
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
            return f"Error: DeckForge API returned {exc.response.status_code} - {exc.response.text}"
        except Exception as exc:
            return f"Error: {type(exc).__name__} - {exc}"


# ---------------------------------------------------------------------------
# CrewAI Agent Example
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Multi-agent workflow: researcher gathers data, presenter creates deck
    #
    # Prerequisites:
    #   pip install crewai crewai-tools httpx
    #   export DECKFORGE_API_KEY=dk_live_xxx
    #   export OPENAI_API_KEY=sk-xxx

    from crewai import Agent, Crew, Task

    # Agent 1: Research analyst who gathers market data
    researcher = Agent(
        role="Research Analyst",
        goal="Gather comprehensive market data and competitive intelligence",
        backstory=(
            "You are a senior research analyst at a top-tier investment bank. "
            "You specialize in technology sector coverage and have deep expertise "
            "in SaaS metrics, competitive dynamics, and market sizing."
        ),
        verbose=True,
    )

    # Agent 2: Presentation designer who uses DeckForge
    presenter = Agent(
        role="Presentation Designer",
        goal="Create executive-ready presentations from research findings",
        backstory=(
            "You are a presentation specialist who transforms complex research "
            "into clear, compelling slide decks for C-suite audiences. You use "
            "DeckForge to produce institutional-quality presentations."
        ),
        tools=[DeckForgeTool()],
        verbose=True,
    )

    # Task 1: Research
    research_task = Task(
        description=(
            "Research the enterprise AI market for a board presentation. "
            "Focus on: market size ($X billion), growth rate, key players, "
            "competitive dynamics, and investment themes for 2026."
        ),
        expected_output=(
            "A structured research brief with market size, growth metrics, "
            "top 10 companies by revenue, and 3 key investment themes."
        ),
        agent=researcher,
    )

    # Task 2: Create presentation
    presentation_task = Task(
        description=(
            "Using the research findings, create a 12-slide board presentation "
            "about the enterprise AI market opportunity. Use DeckForge with "
            "the 'executive-dark' theme. Include market sizing charts, "
            "competitive landscape, and investment recommendations."
        ),
        expected_output=(
            "A download URL for the completed presentation with "
            "a quality score above 80."
        ),
        agent=presenter,
        context=[research_task],
    )

    # Run the crew
    crew = Crew(
        agents=[researcher, presenter],
        tasks=[research_task, presentation_task],
        verbose=True,
    )

    result = crew.kickoff()
    print(f"\nCrew Result:\n{result}")
