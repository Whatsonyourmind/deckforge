"""MCP tool implementations for DeckForge.

Each function is a standalone async tool that imports dependencies locally
(lazy imports) to avoid circular dependencies and reduce startup time.
Functions accept simple types (str, int) and return dicts -- MCP handles
JSON serialization.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def render_presentation(
    ir_json: str,
    theme: str = "corporate-blue",
    output_format: str = "pptx",
) -> dict[str, Any]:
    """Render a presentation from IR (Intermediate Representation) JSON.

    Takes a DeckForge IR JSON string, renders it into a PowerPoint file,
    and returns the download URL, slide count, and quality score.

    Args:
        ir_json: JSON string of the DeckForge Presentation IR schema.
        theme: Theme identifier (e.g., 'corporate-blue', 'executive-dark').
            Defaults to 'corporate-blue'.
        output_format: Output format -- 'pptx' (default) or 'gslides'.

    Returns:
        Dict with download_url, slide_count, quality_score, and format.
    """
    from deckforge.ir.presentation import Presentation
    from deckforge.workers.tasks import render_pipeline

    # Parse and validate the IR
    ir_dict = json.loads(ir_json)

    # Override theme if specified
    if theme:
        ir_dict["theme"] = theme

    presentation = Presentation.model_validate(ir_dict)

    # Render via the shared pipeline
    result, qa_report = render_pipeline(presentation, output_format=output_format)

    slide_count = len(presentation.slides)
    quality_score = qa_report.score

    return {
        "slide_count": slide_count,
        "quality_score": quality_score,
        "format": output_format,
        "size_bytes": len(result) if isinstance(result, bytes) else 0,
        "qa_issues": len(qa_report.issues),
    }


async def generate_presentation(
    prompt: str,
    slide_count: int = 10,
    theme: str = "corporate-blue",
) -> dict[str, Any]:
    """Generate a presentation from a natural language prompt.

    Uses DeckForge's AI content pipeline to transform a text prompt into
    a full presentation with professionally laid out slides.

    Args:
        prompt: Natural language description of the desired presentation
            (e.g., 'Create a Q4 earnings deck for the board').
        slide_count: Target number of slides (default: 10, range: 3-50).
        theme: Theme identifier (default: 'corporate-blue').

    Returns:
        Dict with title, slide_count, theme, and the generated IR.
    """
    from deckforge.content.pipeline import ContentPipeline
    from deckforge.ir.metadata import GenerationOptions
    from deckforge.llm.router import LLMRouter

    # Build generation options
    gen_options = GenerationOptions(
        target_slide_count=slide_count,
    )

    # Run the content generation pipeline
    router = LLMRouter()
    pipeline = ContentPipeline(router)
    ir_dict = await pipeline.run(prompt, generation_options=gen_options)

    # Apply theme
    ir_dict["theme"] = theme

    title = ir_dict.get("metadata", {}).get("title", "Untitled Presentation")
    actual_slide_count = len(ir_dict.get("slides", []))

    return {
        "title": title,
        "slide_count": actual_slide_count,
        "theme": theme,
        "ir": ir_dict,
    }


async def list_themes() -> list[dict[str, Any]]:
    """List all available DeckForge themes.

    Returns the full catalog of built-in themes with their names,
    descriptions, and version information. DeckForge ships with 15
    professionally designed themes suitable for business, finance,
    and creative presentations.

    Returns:
        List of dicts with id, name, description, and version for each theme.
    """
    from deckforge.themes.registry import ThemeRegistry

    registry = ThemeRegistry()
    return registry.list_themes()


async def list_slide_types(category: str | None = None) -> list[dict[str, Any]]:
    """List available slide types in DeckForge.

    DeckForge supports 32 slide types across 2 categories:
    - universal (23 types): title, bullets, chart, table, comparison, timeline, etc.
    - finance (9 types): DCF summary, comp table, waterfall, deal overview, etc.

    Args:
        category: Optional filter -- 'universal' or 'finance'. Returns all if None.

    Returns:
        List of dicts with id, name, description, category, required_elements,
        and optional_elements for each slide type.
    """
    from deckforge.services.slide_type_registry import SlideTypeRegistry

    registry = SlideTypeRegistry()

    if category:
        types = registry.get_by_category(category)
    else:
        types = registry.get_all()

    # Return simplified view (exclude example_ir for brevity)
    return [
        {
            "id": st["id"],
            "name": st["name"],
            "description": st["description"],
            "category": st["category"],
            "required_elements": st["required_elements"],
            "optional_elements": st["optional_elements"],
        }
        for st in types
    ]


async def estimate_cost(ir_json: str) -> dict[str, Any]:
    """Estimate the credit cost for rendering a presentation.

    Analyzes the IR to calculate credit costs based on slide count,
    finance slide surcharges, chart element surcharges, and NL generation.

    Args:
        ir_json: JSON string of the DeckForge Presentation IR schema.

    Returns:
        Dict with total_credits, base_credits, surcharges breakdown,
        and a human-readable cost explanation.
    """
    from deckforge.services.cost_estimator import CostEstimator

    ir_dict = json.loads(ir_json)
    estimator = CostEstimator()
    estimate = estimator.estimate_from_ir(ir_dict)

    # Calculate x402 USD equivalent (1 credit = $0.05)
    x402_usd = round(estimate.total_credits * 0.05, 2)

    return {
        "total_credits": estimate.total_credits,
        "base_credits": estimate.base_credits,
        "surcharges": estimate.surcharges,
        "breakdown": estimate.breakdown,
        "x402_usd": x402_usd,
    }


async def get_pricing() -> dict[str, Any]:
    """Get DeckForge pricing information.

    Returns the full pricing structure including subscription tiers
    (Starter, Pro, Enterprise) and per-call x402 machine payment rates.

    Returns:
        Dict with tiers (list of tier details) and x402 per-call pricing.
    """
    from deckforge.billing.tiers import TIERS

    tiers_list = []
    for tier in TIERS.values():
        tiers_list.append(
            {
                "name": tier.name,
                "display_name": tier.display_name,
                "credit_limit": tier.credit_limit,
                "price_usd": tier.price_cents / 100,
                "overage_rate_usd": tier.overage_rate_cents / 100,
                "rate_limit_rpm": tier.rate_limit,
            }
        )

    x402_pricing = {
        "render_per_call_usd": 0.05,
        "generate_per_call_usd": 0.15,
        "estimate_per_call_usd": 0.00,
        "list_themes_per_call_usd": 0.00,
        "list_slide_types_per_call_usd": 0.00,
        "get_pricing_per_call_usd": 0.00,
        "currency": "USD",
        "protocol": "x402",
    }

    return {
        "tiers": tiers_list,
        "x402": x402_pricing,
    }
