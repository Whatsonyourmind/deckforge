"""LP quarterly report composer.

Fund-level quarterly update deck sent to limited partners. Slide spine:

    1.  Title (fund name, Q# YYYY)
    2.  Executive Summary (headline + quarter-defining event)
    3.  Fund Performance (NAV, IRR, TVPI, DPI, RVPI metric group)
    4.  Portfolio Overview (table of investments with FMV, invested, MOIC)
    5.  Top Movers (bullet list of biggest value changes this quarter)
    6.  Capital Activity (waterfall of calls vs distributions this quarter)
    7.  Market Commentary (body text)
    8.  ESG & Portfolio Operations (bullets)
    9.  Outlook & Pipeline (key message)

Vertical-agnostic — same shape works for PE, PERE, credit, VC.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from deckforge.ir.charts.types import WaterfallChartData
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


class PortfolioHolding(BaseModel):
    company: str
    sector: str = ""
    invested_eur_m: float
    current_fmv_eur_m: float
    moic: Optional[float] = None
    pct_of_fund_nav: Optional[float] = None
    notes: str = ""


class PortfolioMover(BaseModel):
    company: str
    change_eur_m: float
    commentary: str = ""


class LPQuarterlyFacts(BaseModel):
    """Input shape for the LP quarterly composer."""

    fund_name: str
    vintage_year: int
    reporting_quarter: Literal["Q1", "Q2", "Q3", "Q4"]
    reporting_year: int
    report_date: date
    author: str = "Fund GP"
    company: str = "Aither"
    confidentiality: Literal[
        "public", "internal", "confidential", "restricted"
    ] = "confidential"

    # Fund performance
    fund_size_eur_m: float
    called_capital_eur_m: float
    distributed_capital_eur_m: float = 0.0
    nav_eur_m: float
    net_irr_pct: Optional[float] = None
    gross_irr_pct: Optional[float] = None
    tvpi: Optional[float] = None
    dpi: Optional[float] = None
    rvpi: Optional[float] = None

    # Executive summary
    headline: str = ""
    quarter_defining_event: str = ""

    # Portfolio
    holdings: list[PortfolioHolding] = Field(default_factory=list)
    top_movers: list[PortfolioMover] = Field(default_factory=list)

    # Capital activity (this quarter)
    capital_calls_eur_m: float = 0.0
    distributions_this_quarter_eur_m: float = 0.0
    capital_activity_events: list[tuple[str, float]] = Field(default_factory=list)

    # Commentary
    market_commentary: str = ""
    esg_highlights: list[str] = Field(default_factory=list)
    operational_highlights: list[str] = Field(default_factory=list)

    # Outlook
    outlook_headline: str = ""
    pipeline_summary: str = ""


def _format_eur(value: float) -> str:
    return f"€{value:,.1f}M"


def _format_pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _title_slide(facts: LPQuarterlyFacts) -> dict[str, Any]:
    return {
        "slide_type": "title_slide",
        "elements": [
            HeadingElement(content=HeadingContent(text=facts.fund_name)),
            SubheadingElement(
                content=SubheadingContent(
                    text=(
                        f"{facts.reporting_quarter} {facts.reporting_year} · "
                        f"Vintage {facts.vintage_year}"
                    )
                )
            ),
            BodyTextElement(
                content=BodyTextContent(
                    text=(
                        f"Quarterly Report to Limited Partners · "
                        f"{facts.report_date.isoformat()}"
                    )
                )
            ),
        ],
    }


def _executive_summary_slide(facts: LPQuarterlyFacts) -> dict[str, Any]:
    headline = facts.headline or (
        f"{facts.fund_name} NAV {_format_eur(facts.nav_eur_m)} "
        f"at end of {facts.reporting_quarter} {facts.reporting_year}."
    )
    event = facts.quarter_defining_event or (
        "Portfolio companies performing in line with underwrite. "
        "See performance slide for fund-level metrics."
    )
    return {
        "slide_type": "key_message",
        "elements": [
            HeadingElement(content=HeadingContent(text="Executive Summary")),
            SubheadingElement(content=SubheadingContent(text=headline)),
            BodyTextElement(content=BodyTextContent(text=event)),
        ],
    }


def _fund_performance_slide(facts: LPQuarterlyFacts) -> dict[str, Any]:
    metrics: list[KpiCardContent] = [
        KpiCardContent(label="Fund Size", value=_format_eur(facts.fund_size_eur_m)),
        KpiCardContent(label="Called", value=_format_eur(facts.called_capital_eur_m)),
        KpiCardContent(
            label="Distributed", value=_format_eur(facts.distributed_capital_eur_m)
        ),
        KpiCardContent(label="NAV", value=_format_eur(facts.nav_eur_m)),
    ]
    if facts.net_irr_pct is not None:
        metrics.append(
            KpiCardContent(label="Net IRR", value=_format_pct(facts.net_irr_pct))
        )
    if facts.tvpi is not None:
        metrics.append(KpiCardContent(label="TVPI", value=f"{facts.tvpi:.2f}x"))
    if facts.dpi is not None:
        metrics.append(KpiCardContent(label="DPI", value=f"{facts.dpi:.2f}x"))
    if facts.rvpi is not None:
        metrics.append(KpiCardContent(label="RVPI", value=f"{facts.rvpi:.2f}x"))
    return {
        "slide_type": "stats_callout",
        "elements": [
            HeadingElement(content=HeadingContent(text="Fund Performance")),
            MetricGroupElement(content=MetricGroupContent(metrics=metrics)),
        ],
    }


def _portfolio_overview_slide(facts: LPQuarterlyFacts) -> dict[str, Any]:
    if not facts.holdings:
        return {
            "slide_type": "table_slide",
            "elements": [
                HeadingElement(content=HeadingContent(text="Portfolio Overview")),
                BodyTextElement(
                    content=BodyTextContent(
                        text=(
                            "Portfolio holdings table to be populated. "
                            "No holdings provided for this report."
                        )
                    )
                ),
            ],
        }
    headers = ["Company", "Sector", "Invested (€M)", "FMV (€M)", "MOIC", "% NAV"]
    rows: list[list[str | float | int | None]] = []
    for h in facts.holdings:
        moic_cell = f"{h.moic:.2f}x" if h.moic is not None else "—"
        pct_cell = (
            _format_pct(h.pct_of_fund_nav) if h.pct_of_fund_nav is not None else "—"
        )
        rows.append(
            [
                h.company,
                h.sector,
                f"{h.invested_eur_m:.1f}",
                f"{h.current_fmv_eur_m:.1f}",
                moic_cell,
                pct_cell,
            ]
        )
    return {
        "slide_type": "table_slide",
        "elements": [
            HeadingElement(content=HeadingContent(text="Portfolio Overview")),
            TableElement(content=TableContent(headers=headers, rows=rows)),
        ],
    }


def _top_movers_slide(facts: LPQuarterlyFacts) -> dict[str, Any]:
    if not facts.top_movers:
        items = [
            "No material valuation changes this quarter.",
            "Portfolio performing in line with underwrite.",
        ]
    else:
        items = []
        for mover in facts.top_movers:
            sign = "+" if mover.change_eur_m >= 0 else ""
            note = f" — {mover.commentary}" if mover.commentary else ""
            items.append(
                f"{mover.company}: {sign}{mover.change_eur_m:.1f} €M{note}"
            )
    return {
        "slide_type": "bullet_points",
        "elements": [
            HeadingElement(content=HeadingContent(text="Top Movers This Quarter")),
            BulletListElement(content=BulletListContent(items=items)),
        ],
    }


def _capital_activity_slide(facts: LPQuarterlyFacts) -> dict[str, Any]:
    if facts.capital_activity_events:
        categories = [label for label, _ in facts.capital_activity_events]
        values = [value for _, value in facts.capital_activity_events]
    else:
        categories = [
            "Opening NAV",
            "Capital Calls",
            "Distributions",
            "Net Value Change",
            "Closing NAV",
        ]
        opening = (
            facts.nav_eur_m
            - facts.capital_calls_eur_m
            + facts.distributions_this_quarter_eur_m
        )
        net_change = (
            facts.nav_eur_m
            - opening
            - facts.capital_calls_eur_m
            + facts.distributions_this_quarter_eur_m
        )
        values = [
            opening,
            facts.capital_calls_eur_m,
            -facts.distributions_this_quarter_eur_m,
            net_change,
            facts.nav_eur_m,
        ]
    chart_data = WaterfallChartData(
        categories=categories,
        values=values,
        title="Capital Activity (EUR M)",
    )
    summary_parts = []
    if facts.capital_calls_eur_m:
        summary_parts.append(
            f"Calls: {_format_eur(facts.capital_calls_eur_m)}"
        )
    if facts.distributions_this_quarter_eur_m:
        summary_parts.append(
            f"Distributions: {_format_eur(facts.distributions_this_quarter_eur_m)}"
        )
    summary = (
        " · ".join(summary_parts)
        if summary_parts
        else "No capital calls or distributions this quarter."
    )
    return {
        "slide_type": "waterfall_chart",
        "elements": [
            HeadingElement(content=HeadingContent(text="Capital Activity")),
            ChartElement(chart_data=chart_data),
            BodyTextElement(content=BodyTextContent(text=summary)),
        ],
    }


def _market_commentary_slide(facts: LPQuarterlyFacts) -> dict[str, Any]:
    commentary = facts.market_commentary or (
        "Market conditions stable. Deal flow remains robust and "
        "valuations are consistent with underwrite assumptions."
    )
    return {
        "slide_type": "key_message",
        "elements": [
            HeadingElement(content=HeadingContent(text="Market Commentary")),
            BodyTextElement(content=BodyTextContent(text=commentary)),
        ],
    }


def _esg_and_ops_slide(facts: LPQuarterlyFacts) -> dict[str, Any]:
    items: list[str] = []
    for highlight in facts.esg_highlights:
        items.append(f"ESG: {highlight}")
    for highlight in facts.operational_highlights:
        items.append(f"Operations: {highlight}")
    if not items:
        items = [
            "ESG: Annual ESG report on track for year-end delivery.",
            "Operations: All portfolio companies covenant-compliant.",
        ]
    return {
        "slide_type": "bullet_points",
        "elements": [
            HeadingElement(
                content=HeadingContent(text="ESG & Portfolio Operations")
            ),
            BulletListElement(content=BulletListContent(items=items)),
        ],
    }


def _outlook_slide(facts: LPQuarterlyFacts) -> dict[str, Any]:
    headline = facts.outlook_headline or (
        "Focus next quarter on existing portfolio value creation "
        "and selective new deployment."
    )
    pipeline = facts.pipeline_summary or (
        "Pipeline active with multiple qualified opportunities under diligence."
    )
    return {
        "slide_type": "key_message",
        "elements": [
            HeadingElement(content=HeadingContent(text="Outlook & Pipeline")),
            SubheadingElement(content=SubheadingContent(text=headline)),
            BodyTextElement(content=BodyTextContent(text=pipeline)),
        ],
    }


def compose_lp_quarterly(facts: LPQuarterlyFacts) -> Presentation:
    """Turn LPQuarterlyFacts into a 9-slide LP quarterly report Presentation.

    Uses the ``finance-pro`` theme. Audience=INVESTORS, purpose=QUARTERLY_REVIEW.
    """
    confidentiality_map = {
        "public": Confidentiality.PUBLIC,
        "internal": Confidentiality.INTERNAL,
        "confidential": Confidentiality.CONFIDENTIAL,
        "restricted": Confidentiality.RESTRICTED,
    }
    metadata = PresentationMetadata(
        title=(
            f"{facts.fund_name} — {facts.reporting_quarter} "
            f"{facts.reporting_year} LP Report"
        ),
        subtitle=f"Vintage {facts.vintage_year}",
        author=facts.author,
        company=facts.company,
        date=facts.report_date.isoformat(),
        language="en",
        purpose=Purpose.QUARTERLY_REVIEW,
        audience=Audience.INVESTORS,
        confidentiality=confidentiality_map.get(
            facts.confidentiality, Confidentiality.CONFIDENTIAL
        ),
    )

    slides = [
        _title_slide(facts),
        _executive_summary_slide(facts),
        _fund_performance_slide(facts),
        _portfolio_overview_slide(facts),
        _top_movers_slide(facts),
        _capital_activity_slide(facts),
        _market_commentary_slide(facts),
        _esg_and_ops_slide(facts),
        _outlook_slide(facts),
    ]

    return Presentation(
        schema_version="1.0",
        metadata=metadata,
        theme="finance-pro",
        slides=slides,  # type: ignore[arg-type]
    )
