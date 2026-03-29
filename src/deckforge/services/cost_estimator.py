"""Credit cost estimation from IR metadata.

Estimates the credit cost for rendering a presentation based on slide count,
finance slide types, chart elements, and NL generation usage.
"""

from __future__ import annotations

import math
from typing import Any

from pydantic import BaseModel


# Finance slide types that incur surcharges
FINANCE_TYPES: frozenset[str] = frozenset(
    {
        "comp_table",
        "dcf_summary",
        "waterfall_chart",
        "deal_overview",
        "returns_analysis",
        "capital_structure",
        "market_landscape",
        "investment_thesis",
        "risk_matrix",
    }
)


class CostEstimate(BaseModel):
    """Result of a cost estimation."""

    base_credits: int
    surcharges: dict[str, float]
    total_credits: int
    breakdown: str


class CostEstimator:
    """Estimates credit cost for rendering a Presentation IR.

    Pricing model:
    - Base: ceil(slide_count / 10) credits
    - Finance slide surcharge: +0.5 per finance-type slide
    - Chart element surcharge: +0.2 per chart element across all slides
    - NL generation surcharge: +2 if generation_options is present
    - Google Slides surcharge: future placeholder (0 for now)
    """

    FINANCE_SURCHARGE_PER_SLIDE: float = 0.5
    CHART_SURCHARGE_PER_ELEMENT: float = 0.2
    NL_GENERATION_SURCHARGE: float = 2.0

    def estimate_from_ir(self, ir_dict: dict[str, Any]) -> CostEstimate:
        """Estimate cost from an IR dictionary.

        Args:
            ir_dict: The full Presentation IR as a dictionary.

        Returns:
            CostEstimate with base credits, surcharges, total, and breakdown.
        """
        slides = ir_dict.get("slides", [])
        slide_count = len(slides)

        # Base credits: ceil(slide_count / 10), minimum 1
        base = max(1, math.ceil(slide_count / 10))

        surcharges: dict[str, float] = {}

        # Finance slide surcharge
        finance_count = sum(
            1
            for s in slides
            if s.get("slide_type", "") in FINANCE_TYPES
        )
        if finance_count > 0:
            surcharges["finance"] = finance_count * self.FINANCE_SURCHARGE_PER_SLIDE

        # Chart element surcharge
        chart_count = 0
        for s in slides:
            for elem in s.get("elements", []):
                if elem.get("type") == "chart":
                    chart_count += 1
        if chart_count > 0:
            surcharges["charts"] = chart_count * self.CHART_SURCHARGE_PER_ELEMENT

        # NL generation surcharge
        if ir_dict.get("generation_options") is not None:
            surcharges["nl_generation"] = self.NL_GENERATION_SURCHARGE
        else:
            surcharges["nl_generation"] = 0

        # Google Slides surcharge (placeholder)
        surcharges["gslides"] = 0

        # Total
        total_raw = base + sum(surcharges.values())
        total = math.ceil(total_raw)

        # Breakdown
        parts = [f"Base: {base} credit(s) ({slide_count} slides)"]
        if surcharges.get("finance", 0) > 0:
            parts.append(f"Finance slides: +{surcharges['finance']:.1f} ({finance_count} slides)")
        if surcharges.get("charts", 0) > 0:
            parts.append(f"Chart elements: +{surcharges['charts']:.1f} ({chart_count} charts)")
        if surcharges.get("nl_generation", 0) > 0:
            parts.append(f"NL generation: +{surcharges['nl_generation']:.1f}")
        breakdown = "; ".join(parts)

        return CostEstimate(
            base_credits=base,
            surcharges=surcharges,
            total_credits=total,
            breakdown=breakdown,
        )
