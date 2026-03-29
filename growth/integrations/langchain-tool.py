"""DeckForge tools for LangChain agents.

Install: pip install langchain-core httpx pydantic
Usage:
    from deckforge_langchain import DeckForgeRenderTool, DeckForgeGenerateTool
    tools = [DeckForgeRenderTool(), DeckForgeGenerateTool()]
    agent = create_react_agent(llm, tools)

These tools wrap the DeckForge REST API for use within LangChain agent
workflows. Any LangChain-compatible LLM can use them to render structured
IR into PPTX/Google Slides or generate presentations from natural language.

API Reference: https://docs.deckforge.io/api
GitHub: https://github.com/Whatsonyourmind/deckforge
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional, Type

import httpx
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_BASE_URL = "https://api.deckforge.io"


def _get_client(api_key: str | None, base_url: str | None) -> httpx.Client:
    """Create an httpx client with DeckForge auth headers."""
    key = api_key or os.environ.get("DECKFORGE_API_KEY", "")
    url = base_url or os.environ.get("DECKFORGE_API_URL", DEFAULT_BASE_URL)
    if not key:
        raise ValueError(
            "DeckForge API key required. Set DECKFORGE_API_KEY env var "
            "or pass api_key to the tool constructor."
        )
    return httpx.Client(
        base_url=url,
        headers={"Authorization": f"Bearer {key}"},
        timeout=120.0,
    )


# ---------------------------------------------------------------------------
# Input schemas (Pydantic v2 — LangChain reads these for tool descriptions)
# ---------------------------------------------------------------------------

class RenderInput(BaseModel):
    """Input schema for rendering a DeckForge presentation from IR JSON."""

    ir_json: str = Field(
        description=(
            "Presentation IR as a JSON string. Must follow the DeckForge IR schema "
            "with keys: schema_version, metadata, theme, slides. Each slide has "
            "slide_type, title, and elements. See https://docs.deckforge.io/ir"
        )
    )
    output_format: str = Field(
        default="pptx",
        description="Output format: 'pptx' for PowerPoint or 'gslides' for Google Slides.",
    )
    theme: Optional[str] = Field(
        default=None,
        description=(
            "Theme override. Available themes include: corporate-blue, executive-dark, "
            "startup-vibrant, minimal-light, finance-professional, consulting-clean, "
            "tech-modern, academic-formal. If omitted, uses theme specified in the IR."
        ),
    )


class GenerateInput(BaseModel):
    """Input schema for generating a DeckForge presentation from a prompt."""

    prompt: str = Field(
        description=(
            "Natural language description of the presentation to generate. "
            "Be specific about audience, purpose, and key data points. "
            "Example: 'Q4 2025 board update for a $50M ARR B2B SaaS company "
            "showing revenue growth, churn reduction, and 2026 expansion plan.'"
        )
    )
    slide_count: int = Field(
        default=10,
        description="Target number of slides (5-30). Default 10.",
    )
    theme: str = Field(
        default="corporate-blue",
        description="Theme name for the generated deck.",
    )
    output_format: str = Field(
        default="pptx",
        description="Output format: 'pptx' or 'gslides'.",
    )


# ---------------------------------------------------------------------------
# Tool: DeckForgeRenderTool
# ---------------------------------------------------------------------------

class DeckForgeRenderTool(BaseTool):
    """Render a structured DeckForge IR into a downloadable PPTX or Google Slides deck.

    Use this tool when you have structured presentation data (IR JSON) and need
    to produce a finished slide deck. The IR defines slides, elements, charts,
    tables, and layout — the DeckForge engine handles positioning, theming,
    and quality assurance automatically.

    Returns: download URL, slide count, quality score (0-100), and file size.
    """

    name: str = "deckforge_render"
    description: str = (
        "Render a DeckForge Intermediate Representation (IR) JSON into a "
        "downloadable PPTX or Google Slides presentation. The IR defines "
        "slides with types like title, bullets, chart, table, comp_table, "
        "dcf_summary, waterfall_chart, etc. Returns a download URL and "
        "quality score. Use for structured data you already have."
    )
    args_schema: Type[BaseModel] = RenderInput

    # Constructor params (not exposed to LLM)
    api_key: Optional[str] = None
    base_url: Optional[str] = None

    def _run(self, ir_json: str, output_format: str = "pptx", theme: str | None = None) -> str:
        """Execute the render tool."""
        try:
            ir_data = json.loads(ir_json)
        except json.JSONDecodeError as exc:
            return f"Error: Invalid JSON in ir_json — {exc}"

        if theme:
            ir_data["theme"] = {"name": theme}

        try:
            client = _get_client(self.api_key, self.base_url)
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

    async def _arun(self, ir_json: str, output_format: str = "pptx", theme: str | None = None) -> str:
        """Async variant of the render tool."""
        try:
            ir_data = json.loads(ir_json)
        except json.JSONDecodeError as exc:
            return f"Error: Invalid JSON in ir_json — {exc}"

        if theme:
            ir_data["theme"] = {"name": theme}

        key = self.api_key or os.environ.get("DECKFORGE_API_KEY", "")
        url = self.base_url or os.environ.get("DECKFORGE_API_URL", DEFAULT_BASE_URL)
        try:
            async with httpx.AsyncClient(
                base_url=url,
                headers={"Authorization": f"Bearer {key}"},
                timeout=120.0,
            ) as client:
                response = await client.post(
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
# Tool: DeckForgeGenerateTool
# ---------------------------------------------------------------------------

class DeckForgeGenerateTool(BaseTool):
    """Generate a complete presentation from a natural language prompt.

    Use this tool when you need to create a presentation from scratch based on
    a description. DeckForge will parse intent, generate an outline, expand
    slides, and render the final deck — all in one call.

    Returns: download URL, slide count, and quality score.
    """

    name: str = "deckforge_generate"
    description: str = (
        "Generate a complete presentation from a natural language prompt. "
        "Describe the presentation topic, audience, and key points. "
        "DeckForge will create the outline, select appropriate slide types "
        "(including finance types like comp_table, DCF, waterfall), "
        "and render a polished deck. Returns a download URL."
    )
    args_schema: Type[BaseModel] = GenerateInput

    # Constructor params
    api_key: Optional[str] = None
    base_url: Optional[str] = None

    def _run(
        self,
        prompt: str,
        slide_count: int = 10,
        theme: str = "corporate-blue",
        output_format: str = "pptx",
    ) -> str:
        """Execute the generate tool."""
        try:
            client = _get_client(self.api_key, self.base_url)
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

            # /v1/generate returns SSE stream; for sync usage, read final event
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
                    f"Slides: {result.get('slide_count', 'N/A')}\n"
                    f"Quality Score: {result.get('quality_score', 'N/A')}/100"
                )

            return f"Generation completed. Raw response: {response.text[:500]}"

        except httpx.HTTPStatusError as exc:
            return f"Error: DeckForge API returned {exc.response.status_code} — {exc.response.text}"
        except Exception as exc:
            return f"Error: {type(exc).__name__} — {exc}"

    async def _arun(
        self,
        prompt: str,
        slide_count: int = 10,
        theme: str = "corporate-blue",
        output_format: str = "pptx",
    ) -> str:
        """Async variant of the generate tool."""
        key = self.api_key or os.environ.get("DECKFORGE_API_KEY", "")
        url = self.base_url or os.environ.get("DECKFORGE_API_URL", DEFAULT_BASE_URL)
        try:
            async with httpx.AsyncClient(
                base_url=url,
                headers={"Authorization": f"Bearer {key}"},
                timeout=120.0,
            ) as client:
                response = await client.post(
                    "/v1/generate",
                    json={
                        "prompt": prompt,
                        "slide_count": slide_count,
                        "theme": theme,
                        "output_format": output_format,
                    },
                )
                response.raise_for_status()

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
                        f"Slides: {result.get('slide_count', 'N/A')}\n"
                        f"Quality Score: {result.get('quality_score', 'N/A')}/100"
                    )

                return f"Generation completed. Raw response: {response.text[:500]}"

        except httpx.HTTPStatusError as exc:
            return f"Error: DeckForge API returned {exc.response.status_code} — {exc.response.text}"
        except Exception as exc:
            return f"Error: {type(exc).__name__} — {exc}"


# ---------------------------------------------------------------------------
# Usage Example
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Quick example: generate a presentation using a LangChain ReAct agent
    #
    # Prerequisites:
    #   pip install langchain langchain-openai httpx
    #   export DECKFORGE_API_KEY=dk_live_xxx
    #   export OPENAI_API_KEY=sk-xxx

    from langchain.agents import AgentExecutor, create_react_agent
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    tools = [DeckForgeRenderTool(), DeckForgeGenerateTool()]

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a presentation assistant. Use the DeckForge tools to "
            "create professional slide decks. Available tools:\n"
            "- deckforge_generate: Create a deck from a text prompt\n"
            "- deckforge_render: Render structured IR JSON into a deck\n\n"
            "{tools}\n\n{tool_names}\n\n{agent_scratchpad}"
        )),
        ("human", "{input}"),
    ])

    agent = create_react_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    result = executor.invoke({
        "input": (
            "Create a 10-slide board update deck for a $50M ARR SaaS company "
            "showing 40% YoY growth, 95% NRR, and expansion into EMEA."
        )
    })
    print(result["output"])
