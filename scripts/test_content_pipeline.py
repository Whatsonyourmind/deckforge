#!/usr/bin/env python3
"""Test the content generation pipeline locally.

Runs the 4-stage content pipeline (intent -> outline -> expand -> refine)
and outputs the generated Presentation IR.

- If ANTHROPIC_API_KEY / DECKFORGE_ANTHROPIC_API_KEY is set, runs against
  the real Claude API.
- Otherwise, runs a mock test that validates the full pipeline structure
  works end-to-end without actual LLM calls.

Usage:
    cd SlideMaker
    pip install -e .
    python scripts/test_content_pipeline.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Setup paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


# ---------------------------------------------------------------------------
# Mock LLM Router (used when no API key is available)
# ---------------------------------------------------------------------------

class MockLLMRouter:
    """Returns pre-built responses for each pipeline stage."""

    def __init__(self) -> None:
        self._expand_idx = 0

    async def complete_structured(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        *,
        response_model: type,
        **kwargs: Any,
    ):
        from deckforge.content.models import (
            ExpandedSlide,
            ParsedIntent,
            PresentationOutline,
            RefinedPresentation,
            SlideOutline,
        )
        from deckforge.ir.enums import Audience, Purpose, SlideType, Tone

        if response_model is ParsedIntent:
            return ParsedIntent(
                purpose=Purpose.SALES_PITCH,
                audience=Audience.INVESTORS,
                topic="AI Logistics Startup Pitch",
                key_messages=[
                    "AI reduces logistics costs by 30%",
                    "$50B addressable market",
                    "Strong founding team with domain expertise",
                ],
                target_slide_count=5,
                tone=Tone.BOLD,
                suggested_slide_types=[
                    SlideType.TITLE_SLIDE,
                    SlideType.BULLET_POINTS,
                    SlideType.CHART_SLIDE,
                    SlideType.TABLE_SLIDE,
                    SlideType.THANK_YOU,
                ],
            )

        if response_model is PresentationOutline:
            return PresentationOutline(
                title="LogiAI: AI-Powered Logistics",
                narrative_arc="pyramid",
                sections=["Vision", "Market", "Product", "Financials", "Ask"],
                slides=[
                    SlideOutline(
                        position=1,
                        slide_type=SlideType.TITLE_SLIDE,
                        headline="LogiAI: Smarter Logistics",
                        key_points=["AI-driven logistics", "Series A pitch"],
                        narrative_role="opening",
                    ),
                    SlideOutline(
                        position=2,
                        slide_type=SlideType.BULLET_POINTS,
                        headline="The $50B Problem",
                        key_points=["Logistics waste", "Manual processes"],
                        narrative_role="evidence",
                    ),
                    SlideOutline(
                        position=3,
                        slide_type=SlideType.CHART_SLIDE,
                        headline="Revenue Trajectory",
                        key_points=["3x growth", "Strong unit economics"],
                        narrative_role="data",
                    ),
                    SlideOutline(
                        position=4,
                        slide_type=SlideType.TABLE_SLIDE,
                        headline="Use of Funds",
                        key_points=["Engineering 40%", "Sales 35%"],
                        narrative_role="evidence",
                    ),
                    SlideOutline(
                        position=5,
                        slide_type=SlideType.THANK_YOU,
                        headline="Join Our Journey",
                        key_points=["Contact info", "Next steps"],
                        narrative_role="conclusion",
                    ),
                ],
            )

        if response_model is ExpandedSlide:
            slides = [
                ExpandedSlide(
                    slide_type="title_slide",
                    title="LogiAI: Smarter Logistics",
                    elements=[
                        {"type": "heading", "content": {"text": "LogiAI", "level": "h1"}},
                        {
                            "type": "subheading",
                            "content": {"text": "AI-Powered Logistics | Series A | $15M"},
                        },
                    ],
                    speaker_notes="Welcome. LogiAI uses AI to cut logistics costs 30%.",
                    layout_hint="centered",
                ),
                ExpandedSlide(
                    slide_type="bullet_points",
                    title="The $50B Problem",
                    elements=[
                        {
                            "type": "heading",
                            "content": {"text": "The $50B Problem", "level": "h1"},
                        },
                        {
                            "type": "bullet_list",
                            "content": {
                                "items": [
                                    "Logistics companies waste $50B annually on inefficient routing",
                                    "Manual dispatch costs 3x more than AI-optimized",
                                    "Last-mile delivery is 53% of total shipping cost",
                                ],
                            },
                        },
                    ],
                    speaker_notes="These numbers from McKinsey 2025 report.",
                    layout_hint="full",
                ),
                ExpandedSlide(
                    slide_type="chart_slide",
                    title="Revenue Trajectory",
                    elements=[
                        {
                            "type": "heading",
                            "content": {"text": "Revenue Trajectory", "level": "h1"},
                        },
                        {
                            "type": "chart",
                            "chart_data": {
                                "chart_type": "line",
                                "categories": ["Q1'25", "Q2'25", "Q3'25", "Q4'25", "Q1'26"],
                                "series": [
                                    {"name": "ARR ($M)", "values": [0.5, 1.2, 2.1, 3.8, 6.2]}
                                ],
                            },
                        },
                    ],
                    speaker_notes="12x growth in 5 quarters.",
                    layout_hint="full",
                ),
                ExpandedSlide(
                    slide_type="table_slide",
                    title="Use of Funds",
                    elements=[
                        {
                            "type": "heading",
                            "content": {"text": "Use of Funds", "level": "h1"},
                        },
                        {
                            "type": "table",
                            "content": {
                                "headers": ["Category", "Amount ($M)", "%"],
                                "rows": [
                                    ["Engineering", "6.0", "40%"],
                                    ["Sales & Marketing", "5.25", "35%"],
                                    ["Operations", "2.25", "15%"],
                                    ["G&A", "1.5", "10%"],
                                ],
                            },
                        },
                    ],
                    speaker_notes="40% to engineering to build moat.",
                    layout_hint="full",
                ),
                ExpandedSlide(
                    slide_type="thank_you",
                    title="Join Our Journey",
                    elements=[
                        {
                            "type": "heading",
                            "content": {"text": "Join Our Journey", "level": "h1"},
                        },
                        {
                            "type": "body_text",
                            "content": {
                                "text": "Contact: founders@logiai.com | logiai.com"
                            },
                        },
                    ],
                    speaker_notes="Thank you. Happy to take questions.",
                    layout_hint="centered",
                ),
            ]
            idx = self._expand_idx
            self._expand_idx += 1
            return slides[idx]

        if response_model.__name__ == "RefinedPresentation":
            from deckforge.content.models import RefinedPresentation

            # Re-read the slides that were expanded (we need to reconstruct)
            # Reset and re-expand
            self._expand_idx = 0
            expanded_list = []
            for _ in range(5):
                s = await self.complete_structured(
                    messages, response_model=ExpandedSlide
                )
                expanded_list.append(s)
            return RefinedPresentation(
                slides=expanded_list,
                changes_made=["Ensured consistent tone across all slides"],
            )

        raise ValueError(f"Unexpected response_model: {response_model}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def run_pipeline_mock() -> dict:
    """Run the content pipeline with a mock LLM router."""
    from deckforge.content.pipeline import ContentPipeline

    router = MockLLMRouter()
    pipeline = ContentPipeline(router)

    progress_log: list[tuple[str, float]] = []

    async def on_progress(stage: str, progress: float) -> None:
        progress_log.append((stage, progress))
        print(f"  [{progress:5.1%}] {stage}")

    print("Running pipeline with MOCK LLM router (no API key found)...")
    print()

    ir_dict = await pipeline.run(
        "Create a 5-slide pitch deck for an AI logistics startup",
        progress_callback=on_progress,
    )

    print()
    print(f"Pipeline complete. {len(progress_log)} progress events emitted.")
    return ir_dict


async def run_pipeline_real() -> dict:
    """Run the content pipeline with a real Claude adapter."""
    from deckforge.content.pipeline import ContentPipeline
    from deckforge.llm.router import create_router

    router = create_router()
    pipeline = ContentPipeline(router)

    print("Running pipeline with REAL Claude API...")
    print()

    async def on_progress(stage: str, progress: float) -> None:
        print(f"  [{progress:5.1%}] {stage}")

    ir_dict = await pipeline.run(
        "Create a 5-slide pitch deck for an AI logistics startup",
        progress_callback=on_progress,
    )

    print()
    print("Pipeline complete with real LLM calls.")
    return ir_dict


def validate_ir(ir_dict: dict) -> None:
    """Validate the IR output against the Pydantic schema."""
    from deckforge.ir import Presentation

    print("Validating IR against Pydantic schema...")
    presentation = Presentation.model_validate(ir_dict)
    print(f"  Valid! {len(presentation.slides)} slides, theme={presentation.theme}")
    print(f"  Title: {presentation.metadata.title}")

    for i, slide in enumerate(presentation.slides):
        stype = slide.slide_type.value if hasattr(slide.slide_type, "value") else slide.slide_type
        print(f"  Slide {i + 1}: {stype} ({len(slide.elements)} elements)")


def main() -> None:
    print("=" * 60)
    print("DeckForge Content Pipeline Test")
    print("=" * 60)
    print()

    # Check for API key
    api_key = (
        os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("DECKFORGE_ANTHROPIC_API_KEY")
    )

    if api_key:
        print(f"API key found (ends with ...{api_key[-4:]})")
        ir_dict = asyncio.run(run_pipeline_real())
    else:
        print("No API key found. Running mock pipeline.")
        ir_dict = asyncio.run(run_pipeline_mock())

    print()
    validate_ir(ir_dict)

    print()
    print("Generated IR (JSON):")
    print("-" * 60)
    print(json.dumps(ir_dict, indent=2))
    print("-" * 60)
    print()
    print("SUCCESS: Content pipeline test passed.")


if __name__ == "__main__":
    main()
