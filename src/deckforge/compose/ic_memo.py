"""IC memo deck composer.

Turns a DealFacts payload into a 12-slide Investment Committee memo using
the ``finance-pro`` theme. Slide spine mirrors bulge-bracket IC templates:

    1.  Title (deal name + sector + date)
    2.  Executive Summary (key_message)
    3.  Deal Overview (bullet list of structure/size/location)
    4.  Investment Thesis (bullet list of why-win rationale)
    5.  Returns Summary (metric group: IRR / MOIC / levered / yield-on-cost)
    6.  Cash Flow Waterfall (waterfall chart)
    7.  Capital Structure (stacked bar)
    8.  Comparable Transactions (table)
    9.  Sensitivity Analysis (heatmap / bullet_list fallback)
    10. Risk Matrix (placeholder — risk_matrix slide_type)
    11. Key Risks & Mitigants (two-column)
    12. Recommendation (key_message)

Callers pass a flat DealFacts model; they do NOT need to know DeckForge IR
internals. The composer produces a fully validated Presentation.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from deckforge.ir.charts.types import (
    HeatmapChartData,
    StackedBarChartData,
    WaterfallChartData,
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


class ComparableTransaction(BaseModel):
    """One row of the comp-transactions slide."""

    target: str
    year: int
    size_eur_m: float
    multiple: Optional[float] = None  # EV/EBITDA or cap rate
    notes: str = ""


class DealFacts(BaseModel):
    """The universal deal-data shape every composer consumes.

    Vertical-agnostic so the same model serves PE, PERE, credit,
    infrastructure, and NPL deals. Vertical-specific metrics go in
    ``sector_metrics``.
    """

    # Identity
    deal_name: str
    sector: str = "Private Markets"
    vertical: Literal[
        "pe", "re", "infrastructure", "credit", "npl", "vc", "m_and_a"
    ] = "pe"
    country: str = "IT"
    deal_date: date
    author: str = "Deal Team"
    company: str = "Aither"
    confidentiality: Literal[
        "public", "internal", "confidential", "restricted"
    ] = "confidential"

    # Deal structure
    total_size_eur_m: float
    equity_required_eur_m: float
    debt_eur_m: float = 0.0
    hold_period_years: int = 7

    # Thesis (3-5 bullets)
    investment_thesis_title: str = "Investment Thesis"
    investment_thesis_bullets: list[str] = Field(default_factory=list)

    # Returns
    target_irr_pct: float = 0.15
    target_moic: float = 2.0
    yield_on_cost_pct: Optional[float] = None  # RE-specific
    levered_irr_pct: Optional[float] = None
    unlevered_irr_pct: Optional[float] = None

    # Waterfall (entry → exit flow, 5-7 steps)
    waterfall_categories: list[str] = Field(
        default_factory=lambda: [
            "Entry Equity", "Operating Cash", "Debt Service",
            "CapEx", "Exit Proceeds", "Net to LP",
        ]
    )
    waterfall_values: list[float] = Field(
        default_factory=lambda: [-100.0, 40.0, -30.0, -20.0, 180.0, 70.0]
    )

    # Capital stack (split by tranche)
    capital_stack_tranches: list[str] = Field(
        default_factory=lambda: ["Senior", "Mezz", "Preferred", "Common Equity"]
    )
    capital_stack_values: list[float] = Field(
        default_factory=lambda: [50.0, 15.0, 10.0, 25.0]
    )

    # Comps (3-5 rows typical)
    comparable_transactions: list[ComparableTransaction] = Field(default_factory=list)

    # Sensitivity — IRR swing grid (rows: exit multiple, cols: revenue growth)
    sensitivity_row_labels: list[str] = Field(default_factory=list)
    sensitivity_col_labels: list[str] = Field(default_factory=list)
    sensitivity_values: list[list[float]] = Field(default_factory=list)

    # Risks (3-5 items; each an IC-level material risk)
    risks: list[str] = Field(default_factory=list)
    mitigants: list[str] = Field(default_factory=list)

    # Recommendation
    recommendation: Literal[
        "approve", "approve_with_conditions", "reject", "defer"
    ] = "approve"
    recommendation_rationale: str = ""
    ask_eur_m: Optional[float] = None

    # Vertical-specific extras
    sector_metrics: dict[str, Any] = Field(default_factory=dict)


# ── Formatters ───────────────────────────────────────────────────────────


def _format_eur(value: float) -> str:
    return f"€{value:,.1f}M"


def _format_pct(value: float) -> str:
    return f"{value * 100:.1f}%"


# ── Slide builders ───────────────────────────────────────────────────────


def _title_slide(deal: DealFacts) -> dict[str, Any]:
    return {
        "slide_type": "title_slide",
        "elements": [
            HeadingElement(content=HeadingContent(text=deal.deal_name)),
            SubheadingElement(
                content=SubheadingContent(
                    text=(
                        f"{deal.sector} · {deal.country} · "
                        f"{deal.deal_date.isoformat()}"
                    )
                )
            ),
            BodyTextElement(
                content=BodyTextContent(
                    text=f"{deal.company} Investment Committee"
                )
            ),
        ],
    }


def _executive_summary_slide(deal: DealFacts) -> dict[str, Any]:
    thesis_summary = (
        deal.investment_thesis_bullets[0]
        if deal.investment_thesis_bullets
        else "High-conviction deal in Italian private markets."
    )
    summary_line = (
        f"Size {_format_eur(deal.total_size_eur_m)} · "
        f"Equity {_format_eur(deal.equity_required_eur_m)} · "
        f"Target IRR {_format_pct(deal.target_irr_pct)} · "
        f"Hold {deal.hold_period_years}y"
    )
    return {
        "slide_type": "key_message",
        "elements": [
            HeadingElement(content=HeadingContent(text="Executive Summary")),
            SubheadingElement(content=SubheadingContent(text=thesis_summary)),
            BodyTextElement(content=BodyTextContent(text=summary_line)),
        ],
    }


def _deal_overview_slide(deal: DealFacts) -> dict[str, Any]:
    items = [
        f"Deal: {deal.deal_name}",
        f"Sector: {deal.sector}",
        f"Country: {deal.country}",
        f"Total Size: {_format_eur(deal.total_size_eur_m)}",
        f"Equity Required: {_format_eur(deal.equity_required_eur_m)}",
        f"Debt: {_format_eur(deal.debt_eur_m)}",
        f"Hold Period: {deal.hold_period_years} years",
    ]
    if deal.yield_on_cost_pct is not None:
        items.append(f"Yield on Cost: {_format_pct(deal.yield_on_cost_pct)}")
    return {
        "slide_type": "deal_overview",
        "elements": [
            HeadingElement(content=HeadingContent(text="Deal Overview")),
            BulletListElement(content=BulletListContent(items=items)),
        ],
    }


def _thesis_slide(deal: DealFacts) -> dict[str, Any]:
    items = deal.investment_thesis_bullets or [
        "Attractive entry valuation vs comparable transactions.",
        "Strong operating tailwinds in target sector and geography.",
        "Clear value-creation levers under deal-team control.",
    ]
    return {
        "slide_type": "investment_thesis",
        "elements": [
            HeadingElement(content=HeadingContent(text=deal.investment_thesis_title)),
            BulletListElement(content=BulletListContent(items=items)),
        ],
    }


def _returns_callout_slide(deal: DealFacts) -> dict[str, Any]:
    metrics: list[KpiCardContent] = [
        KpiCardContent(label="Target IRR", value=_format_pct(deal.target_irr_pct)),
        KpiCardContent(label="Target MOIC", value=f"{deal.target_moic:.1f}x"),
    ]
    if deal.levered_irr_pct is not None:
        metrics.append(
            KpiCardContent(
                label="Levered IRR", value=_format_pct(deal.levered_irr_pct)
            )
        )
    if deal.yield_on_cost_pct is not None:
        metrics.append(
            KpiCardContent(
                label="Yield on Cost",
                value=_format_pct(deal.yield_on_cost_pct),
            )
        )
    return {
        "slide_type": "stats_callout",
        "elements": [
            HeadingElement(content=HeadingContent(text="Returns Summary")),
            MetricGroupElement(content=MetricGroupContent(metrics=metrics)),
        ],
    }


def _waterfall_slide(deal: DealFacts) -> dict[str, Any]:
    chart_data = WaterfallChartData(
        categories=deal.waterfall_categories,
        values=deal.waterfall_values,
        title="Cash Flow Waterfall (EUR M)",
    )
    return {
        "slide_type": "waterfall_chart",
        "elements": [
            HeadingElement(content=HeadingContent(text="Cash Flow Waterfall")),
            ChartElement(chart_data=chart_data),
        ],
    }


def _capital_structure_slide(deal: DealFacts) -> dict[str, Any]:
    total = sum(deal.capital_stack_values) or 1.0
    breakdown = " · ".join(
        f"{name} {value / total * 100:.0f}%"
        for name, value in zip(
            deal.capital_stack_tranches, deal.capital_stack_values
        )
    )
    chart_data = StackedBarChartData(
        categories=["Sources"],
        series=[
            {"name": name, "values": [value]}
            for name, value in zip(
                deal.capital_stack_tranches, deal.capital_stack_values
            )
        ],
        title="Capital Structure (EUR M)",
    )
    return {
        "slide_type": "capital_structure",
        "elements": [
            HeadingElement(content=HeadingContent(text="Capital Structure")),
            ChartElement(chart_data=chart_data),
            BodyTextElement(content=BodyTextContent(text=breakdown)),
        ],
    }


def _comps_slide(deal: DealFacts) -> dict[str, Any]:
    if not deal.comparable_transactions:
        return {
            "slide_type": "comp_table",
            "elements": [
                HeadingElement(content=HeadingContent(text="Comparable Transactions")),
                BodyTextElement(
                    content=BodyTextContent(
                        text="Comparable transactions to be sourced prior to IC final."
                    )
                ),
            ],
        }
    headers = ["Target", "Year", "Size (€M)", "Multiple", "Notes"]
    rows: list[list[str | float | int | None]] = [
        [
            c.target,
            c.year,
            f"{c.size_eur_m:.1f}",
            f"{c.multiple:.1f}x" if c.multiple is not None else "—",
            c.notes,
        ]
        for c in deal.comparable_transactions
    ]
    return {
        "slide_type": "comp_table",
        "elements": [
            HeadingElement(content=HeadingContent(text="Comparable Transactions")),
            TableElement(content=TableContent(headers=headers, rows=rows)),
        ],
    }


def _sensitivity_slide(deal: DealFacts) -> dict[str, Any]:
    if not deal.sensitivity_values:
        return {
            "slide_type": "table_slide",
            "elements": [
                HeadingElement(content=HeadingContent(text="Sensitivity Analysis")),
                BodyTextElement(
                    content=BodyTextContent(
                        text="IRR sensitivity grid to be populated post-DD."
                    )
                ),
            ],
        }
    chart_data = HeatmapChartData(
        x_labels=deal.sensitivity_col_labels,
        y_labels=deal.sensitivity_row_labels,
        data=deal.sensitivity_values,
        title="IRR Sensitivity (Exit Multiple × Revenue Growth)",
    )
    return {
        "slide_type": "chart_slide",
        "elements": [
            HeadingElement(content=HeadingContent(text="IRR Sensitivity")),
            ChartElement(chart_data=chart_data),
        ],
    }


def _risk_matrix_slide(deal: DealFacts) -> dict[str, Any]:
    return {
        "slide_type": "risk_matrix",
        "elements": [
            HeadingElement(content=HeadingContent(text="Risk Matrix")),
            BodyTextElement(
                content=BodyTextContent(
                    text=(
                        "Probability (low→high) × Impact (low→high). "
                        "Upper-right cell items require mitigation before approval."
                    )
                )
            ),
        ],
        "axes_labels": {"x": "Probability", "y": "Impact"},
    }


def _risks_and_mitigants_slide(deal: DealFacts) -> dict[str, Any]:
    risks = deal.risks or ["Execution risk during integration phase."]
    mitigants = deal.mitigants or ["Experienced operating partner in place."]
    return {
        "slide_type": "two_column_text",
        "elements": [
            HeadingElement(content=HeadingContent(text="Key Risks & Mitigants")),
            BulletListElement(
                content=BulletListContent(
                    items=[f"Risk: {r}" for r in risks]
                )
            ),
            BulletListElement(
                content=BulletListContent(
                    items=[f"Mitigant: {m}" for m in mitigants]
                )
            ),
        ],
    }


def _recommendation_slide(deal: DealFacts) -> dict[str, Any]:
    label_map = {
        "approve": "APPROVE",
        "approve_with_conditions": "APPROVE WITH CONDITIONS",
        "reject": "REJECT",
        "defer": "DEFER",
    }
    label = label_map[deal.recommendation]
    rationale = (
        deal.recommendation_rationale
        or "See executive summary + returns + risks for full rationale."
    )
    body_parts = [rationale]
    if deal.ask_eur_m is not None:
        body_parts.append(f"Committing {_format_eur(deal.ask_eur_m)} from the fund.")
    return {
        "slide_type": "key_message",
        "elements": [
            HeadingElement(
                content=HeadingContent(text=f"Recommendation: {label}")
            ),
            BodyTextElement(content=BodyTextContent(text="\n".join(body_parts))),
        ],
    }


# ── Public composer ──────────────────────────────────────────────────────


def compose_ic_memo(deal: DealFacts) -> Presentation:
    """Turn deal facts into a 12-slide IC memo Presentation.

    Output is a fully validated IR ready for render_pipeline or /v1/render.
    Uses the ``finance-pro`` theme (navy + money-green + loss-red, Calibri).
    """
    confidentiality_map = {
        "public": Confidentiality.PUBLIC,
        "internal": Confidentiality.INTERNAL,
        "confidential": Confidentiality.CONFIDENTIAL,
        "restricted": Confidentiality.RESTRICTED,
    }
    metadata = PresentationMetadata(
        title=f"{deal.deal_name} — IC Memo",
        subtitle=f"{deal.sector} · {deal.country}",
        author=deal.author,
        company=deal.company,
        date=deal.deal_date.isoformat(),
        language="en",
        purpose=Purpose.IC_PRESENTATION,
        audience=Audience.BOARD,
        confidentiality=confidentiality_map.get(
            deal.confidentiality, Confidentiality.CONFIDENTIAL
        ),
    )

    slides = [
        _title_slide(deal),
        _executive_summary_slide(deal),
        _deal_overview_slide(deal),
        _thesis_slide(deal),
        _returns_callout_slide(deal),
        _waterfall_slide(deal),
        _capital_structure_slide(deal),
        _comps_slide(deal),
        _sensitivity_slide(deal),
        _risk_matrix_slide(deal),
        _risks_and_mitigants_slide(deal),
        _recommendation_slide(deal),
    ]

    return Presentation(
        schema_version="1.0",
        metadata=metadata,
        theme="finance-pro",
        slides=slides,  # type: ignore[arg-type]  # discriminated union on slide_type
    )
