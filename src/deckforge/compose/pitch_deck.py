"""Startup pitch deck composer.

Seed/Series-A pitch deck used by founders to raise capital. Slide spine
mirrors classic Sequoia / YC pitch templates:

    1.  Title (company + tagline + date)
    2.  Problem (key_message — pain point)
    3.  Solution (key_message — what you do)
    4.  Market Size (stats_callout — TAM / SAM / SOM)
    5.  Product / Demo (bullet_points — product highlights)
    6.  Traction (chart — revenue / users / growth)
    7.  Business Model (bullet_points — pricing + unit economics)
    8.  Go-to-Market (bullet_points — channels + acquisition strategy)
    9.  Competition (table — competitive landscape)
    10. Team (team_slide — founders + key hires)
    11. Financials (chart — projections)
    12. Ask & Use of Funds (key_message — round size + allocation)
    13. Contact (key_message — founder contact)

Vertical-agnostic — same shape works for B2B SaaS, consumer, fintech,
deeptech. Vertical-specific metrics go in ``sector_metrics``.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from deckforge.ir.charts.types import (
    BarChartData,
    ChartDataSeries,
    LineChartData,
)
from deckforge.ir.elements.data import (
    ChartElement,
    KpiCardContent,
    MetricGroupContent,
    MetricGroupElement,
    TableContent,
    TableElement,
)
from deckforge.ir.elements.text import (
    BodyTextContent,
    BodyTextElement,
    BulletListContent,
    BulletListElement,
    HeadingContent,
    HeadingElement,
    SubheadingContent,
    SubheadingElement,
)
from deckforge.ir.enums import Audience, Confidentiality, Purpose
from deckforge.ir.metadata import PresentationMetadata
from deckforge.ir.presentation import Presentation


# ── Input ────────────────────────────────────────────────────────────────


class TeamMember(BaseModel):
    """One row of the team slide."""

    name: str
    role: str
    background: str = ""


class CompetitorRow(BaseModel):
    """One row of the competitive landscape table."""

    name: str
    positioning: str = ""
    differentiator: str = ""


class PitchDeckFacts(BaseModel):
    """Input shape for the startup pitch deck composer.

    Vertical-agnostic so the same model serves B2B SaaS, consumer,
    fintech, deeptech, and biotech pitches. Vertical-specific metrics go
    in ``sector_metrics``.
    """

    # Identity
    company_name: str
    tagline: str = ""
    sector: str = "Technology"
    stage: Literal["pre_seed", "seed", "series_a", "series_b"] = "seed"
    country: str = "IT"
    pitch_date: date
    author: str = "Founders"
    company: str = ""
    confidentiality: Literal[
        "public", "internal", "confidential", "restricted"
    ] = "confidential"

    # Problem / Solution
    problem_headline: str = ""
    problem_detail: str = ""
    solution_headline: str = ""
    solution_detail: str = ""

    # Market sizing (EUR M)
    tam_eur_m: Optional[float] = None
    sam_eur_m: Optional[float] = None
    som_eur_m: Optional[float] = None
    market_commentary: str = ""

    # Product
    product_highlights: list[str] = Field(default_factory=list)

    # Traction (5-7 periods typical: months or quarters)
    traction_metric_label: str = "ARR (EUR k)"
    traction_periods: list[str] = Field(default_factory=list)
    traction_values: list[float] = Field(default_factory=list)

    # Business model
    business_model_bullets: list[str] = Field(default_factory=list)

    # Go-to-market
    gtm_bullets: list[str] = Field(default_factory=list)

    # Competition (3-6 rows typical)
    competitors: list[CompetitorRow] = Field(default_factory=list)

    # Team
    team_members: list[TeamMember] = Field(default_factory=list)

    # Financials (revenue projection)
    financial_periods: list[str] = Field(default_factory=list)
    financial_revenue_eur_k: list[float] = Field(default_factory=list)
    financial_ebitda_eur_k: list[float] = Field(default_factory=list)

    # Ask
    ask_eur_m: Optional[float] = None
    pre_money_eur_m: Optional[float] = None
    use_of_funds: list[str] = Field(default_factory=list)

    # Contact
    contact_name: str = ""
    contact_role: str = ""
    contact_email: str = ""
    contact_phone: str = ""

    # Vertical-specific extras
    sector_metrics: dict[str, Any] = Field(default_factory=dict)


# ── Formatters ───────────────────────────────────────────────────────────


def _format_eur_m(value: float) -> str:
    return f"€{value:,.1f}M"


def _format_eur_k(value: float) -> str:
    return f"€{value:,.0f}k"


# ── Slide builders ───────────────────────────────────────────────────────


def _title_slide(facts: PitchDeckFacts) -> dict[str, Any]:
    subtitle_parts = [facts.sector, facts.country, facts.pitch_date.isoformat()]
    return {
        "slide_type": "title_slide",
        "elements": [
            HeadingElement(content=HeadingContent(text=facts.company_name)),
            SubheadingElement(
                content=SubheadingContent(
                    text=facts.tagline or " · ".join(subtitle_parts)
                )
            ),
            BodyTextElement(
                content=BodyTextContent(text=" · ".join(subtitle_parts))
            ),
        ],
    }


def _problem_slide(facts: PitchDeckFacts) -> dict[str, Any]:
    headline = facts.problem_headline or (
        "The market has a painful, unsolved problem."
    )
    detail = facts.problem_detail or (
        "Existing solutions are expensive, slow, or fragmented. "
        "Customers compensate with manual workarounds."
    )
    return {
        "slide_type": "key_message",
        "elements": [
            HeadingElement(content=HeadingContent(text="Problem")),
            SubheadingElement(content=SubheadingContent(text=headline)),
            BodyTextElement(content=BodyTextContent(text=detail)),
        ],
    }


def _solution_slide(facts: PitchDeckFacts) -> dict[str, Any]:
    headline = facts.solution_headline or (
        f"{facts.company_name} solves this with a 10x better approach."
    )
    detail = facts.solution_detail or (
        "Our product is faster, cheaper, and easier to adopt than incumbents."
    )
    return {
        "slide_type": "key_message",
        "elements": [
            HeadingElement(content=HeadingContent(text="Solution")),
            SubheadingElement(content=SubheadingContent(text=headline)),
            BodyTextElement(content=BodyTextContent(text=detail)),
        ],
    }


def _market_size_slide(facts: PitchDeckFacts) -> dict[str, Any]:
    metrics: list[KpiCardContent] = []
    if facts.tam_eur_m is not None:
        metrics.append(
            KpiCardContent(label="TAM", value=_format_eur_m(facts.tam_eur_m))
        )
    if facts.sam_eur_m is not None:
        metrics.append(
            KpiCardContent(label="SAM", value=_format_eur_m(facts.sam_eur_m))
        )
    if facts.som_eur_m is not None:
        metrics.append(
            KpiCardContent(label="SOM", value=_format_eur_m(facts.som_eur_m))
        )
    if not metrics:
        metrics = [
            KpiCardContent(label="TAM", value="To be sized"),
            KpiCardContent(label="SAM", value="To be sized"),
            KpiCardContent(label="SOM", value="To be sized"),
        ]
    elements: list[Any] = [
        HeadingElement(content=HeadingContent(text="Market Size")),
        MetricGroupElement(content=MetricGroupContent(metrics=metrics)),
    ]
    if facts.market_commentary:
        elements.append(
            BodyTextElement(content=BodyTextContent(text=facts.market_commentary))
        )
    return {
        "slide_type": "stats_callout",
        "elements": elements,
    }


def _product_slide(facts: PitchDeckFacts) -> dict[str, Any]:
    items = facts.product_highlights or [
        "Core product live and shipping to customers.",
        "Multi-tenant SaaS with self-serve onboarding.",
        "Public API + integrations with key ecosystem players.",
    ]
    return {
        "slide_type": "bullet_points",
        "elements": [
            HeadingElement(content=HeadingContent(text="Product")),
            BulletListElement(content=BulletListContent(items=items)),
        ],
    }


def _traction_slide(facts: PitchDeckFacts) -> dict[str, Any]:
    if facts.traction_periods and facts.traction_values:
        chart_data = LineChartData(
            categories=facts.traction_periods,
            series=[
                ChartDataSeries(
                    name=facts.traction_metric_label,
                    values=list(facts.traction_values),
                )
            ],
            title=f"Traction — {facts.traction_metric_label}",
        )
        return {
            "slide_type": "chart_slide",
            "elements": [
                HeadingElement(content=HeadingContent(text="Traction")),
                ChartElement(chart_data=chart_data),
            ],
        }
    return {
        "slide_type": "chart_slide",
        "elements": [
            HeadingElement(content=HeadingContent(text="Traction")),
            BodyTextElement(
                content=BodyTextContent(
                    text="Traction data to be shared in due diligence."
                )
            ),
        ],
    }


def _business_model_slide(facts: PitchDeckFacts) -> dict[str, Any]:
    items = facts.business_model_bullets or [
        "SaaS subscription, billed annually.",
        "Net revenue retention >120% via expansion seats.",
        "CAC payback inside 12 months.",
    ]
    return {
        "slide_type": "bullet_points",
        "elements": [
            HeadingElement(content=HeadingContent(text="Business Model")),
            BulletListElement(content=BulletListContent(items=items)),
        ],
    }


def _gtm_slide(facts: PitchDeckFacts) -> dict[str, Any]:
    items = facts.gtm_bullets or [
        "Inbound via content + community in core ICP segments.",
        "Outbound to ICP-fit accounts via SDR team.",
        "Channel partnerships with adjacent platforms.",
    ]
    return {
        "slide_type": "bullet_points",
        "elements": [
            HeadingElement(content=HeadingContent(text="Go-to-Market")),
            BulletListElement(content=BulletListContent(items=items)),
        ],
    }


def _competition_slide(facts: PitchDeckFacts) -> dict[str, Any]:
    if not facts.competitors:
        return {
            "slide_type": "comparison",
            "elements": [
                HeadingElement(content=HeadingContent(text="Competition")),
                BodyTextElement(
                    content=BodyTextContent(
                        text=(
                            "Competitive landscape mapping to be shared "
                            "in due diligence."
                        )
                    )
                ),
            ],
        }
    headers = ["Competitor", "Positioning", "Our Differentiator"]
    rows: list[list[str | float | int | None]] = [
        [c.name, c.positioning, c.differentiator]
        for c in facts.competitors
    ]
    return {
        "slide_type": "comparison",
        "elements": [
            HeadingElement(content=HeadingContent(text="Competition")),
            TableElement(content=TableContent(headers=headers, rows=rows)),
        ],
    }


def _team_slide(facts: PitchDeckFacts) -> dict[str, Any]:
    if facts.team_members:
        items = [
            f"{m.name} — {m.role}"
            + (f" · {m.background}" if m.background else "")
            for m in facts.team_members
        ]
    else:
        items = [
            "Founder/CEO — domain operator with track record.",
            "Founder/CTO — technical leader from top-tier engineering org.",
            "Key hires across product, sales, and customer success.",
        ]
    return {
        "slide_type": "team_slide",
        "elements": [
            HeadingElement(content=HeadingContent(text="Team")),
            BulletListElement(content=BulletListContent(items=items)),
        ],
    }


def _financials_slide(facts: PitchDeckFacts) -> dict[str, Any]:
    if facts.financial_periods and facts.financial_revenue_eur_k:
        series = [
            ChartDataSeries(
                name="Revenue (€k)",
                values=list(facts.financial_revenue_eur_k),
            )
        ]
        if facts.financial_ebitda_eur_k:
            series.append(
                ChartDataSeries(
                    name="EBITDA (€k)",
                    values=list(facts.financial_ebitda_eur_k),
                )
            )
        chart_data = BarChartData(
            categories=facts.financial_periods,
            series=series,
            title="Financial Projections (EUR k)",
        )
        return {
            "slide_type": "chart_slide",
            "elements": [
                HeadingElement(content=HeadingContent(text="Financials")),
                ChartElement(chart_data=chart_data),
            ],
        }
    return {
        "slide_type": "chart_slide",
        "elements": [
            HeadingElement(content=HeadingContent(text="Financials")),
            BodyTextElement(
                content=BodyTextContent(
                    text="Detailed financial model available on request."
                )
            ),
        ],
    }


def _ask_slide(facts: PitchDeckFacts) -> dict[str, Any]:
    parts: list[str] = []
    if facts.ask_eur_m is not None:
        parts.append(f"Raising {_format_eur_m(facts.ask_eur_m)}")
    if facts.pre_money_eur_m is not None:
        parts.append(f"Pre-money {_format_eur_m(facts.pre_money_eur_m)}")
    headline = " · ".join(parts) if parts else "Round size to be confirmed."
    use_items = facts.use_of_funds or [
        "Product engineering — accelerate roadmap execution.",
        "Go-to-market — scale sales and demand generation.",
        "Working capital — runway through next milestone.",
    ]
    return {
        "slide_type": "key_message",
        "elements": [
            HeadingElement(content=HeadingContent(text="Ask & Use of Funds")),
            SubheadingElement(content=SubheadingContent(text=headline)),
            BulletListElement(content=BulletListContent(items=use_items)),
        ],
    }


def _contact_slide(facts: PitchDeckFacts) -> dict[str, Any]:
    lines: list[str] = []
    if facts.contact_name:
        role = f" — {facts.contact_role}" if facts.contact_role else ""
        lines.append(f"{facts.contact_name}{role}")
    if facts.contact_email:
        lines.append(facts.contact_email)
    if facts.contact_phone:
        lines.append(facts.contact_phone)
    if not lines:
        lines.append("Contact details to be shared with interested investors.")
    return {
        "slide_type": "key_message",
        "elements": [
            HeadingElement(content=HeadingContent(text="Contact")),
            BodyTextElement(content=BodyTextContent(text="\n".join(lines))),
        ],
    }


# ── Public composer ──────────────────────────────────────────────────────


def compose_pitch_deck(facts: PitchDeckFacts) -> Presentation:
    """Turn PitchDeckFacts into a 13-slide startup pitch deck Presentation.

    Output is a fully validated IR ready for render_pipeline or /v1/render.
    Uses the ``finance-pro`` theme. Audience=INVESTORS, purpose=SALES_PITCH.
    """
    confidentiality_map = {
        "public": Confidentiality.PUBLIC,
        "internal": Confidentiality.INTERNAL,
        "confidential": Confidentiality.CONFIDENTIAL,
        "restricted": Confidentiality.RESTRICTED,
    }
    metadata = PresentationMetadata(
        title=f"{facts.company_name} — Pitch Deck",
        subtitle=f"{facts.sector} · {facts.country}",
        author=facts.author,
        company=facts.company or facts.company_name,
        date=facts.pitch_date.isoformat(),
        language="en",
        purpose=Purpose.SALES_PITCH,
        audience=Audience.INVESTORS,
        confidentiality=confidentiality_map.get(
            facts.confidentiality, Confidentiality.CONFIDENTIAL
        ),
    )

    slides = [
        _title_slide(facts),
        _problem_slide(facts),
        _solution_slide(facts),
        _market_size_slide(facts),
        _product_slide(facts),
        _traction_slide(facts),
        _business_model_slide(facts),
        _gtm_slide(facts),
        _competition_slide(facts),
        _team_slide(facts),
        _financials_slide(facts),
        _ask_slide(facts),
        _contact_slide(facts),
    ]

    return Presentation(
        schema_version="1.0",
        metadata=metadata,
        theme="finance-pro",
        slides=slides,  # type: ignore[arg-type]
    )
