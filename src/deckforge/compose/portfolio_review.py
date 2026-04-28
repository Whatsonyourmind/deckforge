"""Portfolio review composer.

Internal quarterly portfolio review presented by GP deal teams to the
investment committee. Frank, action-oriented counterpart to the LP
quarterly report — same underlying data, internal voice. Slide spine:

    1.  Title (fund + Q# YYYY portfolio review)
    2.  Portfolio Overview (table of all holdings: invested, FMV, MOIC, status)
    3.  Top Performers (bullet_points — biggest value drivers + commentary)
    4.  Watchlist (bullet_points — companies underperforming or at risk)
    5.  Value-Creation Actions (table — open initiatives across portfolio)
    6.  Capital Deployment (chart — invested vs available dry powder)
    7.  Portfolio Metrics Dashboard (stats_callout — fund-level KPIs)
    8.  Exits & Realizations (table — closed and pipeline exits)
    9.  Market View (key_message — outlook + sector commentary)
    10. Key Risks (bullet_points — top risks across portfolio)
    11. Asks & Decisions (key_message — IC asks for this meeting)

Vertical-agnostic — same shape works for PE, PERE, credit, VC.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from deckforge.ir.charts.types import (
    BarChartData,
    ChartDataSeries,
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


class PortfolioCompany(BaseModel):
    """One row of the portfolio overview table."""

    company: str
    sector: str = ""
    invested_eur_m: float
    current_fmv_eur_m: float
    moic: Optional[float] = None
    status: Literal[
        "outperforming", "on_plan", "watchlist", "underperforming", "exited"
    ] = "on_plan"
    notes: str = ""


class TopPerformer(BaseModel):
    company: str
    value_change_eur_m: float
    driver: str = ""


class WatchlistItem(BaseModel):
    company: str
    issue: str
    severity: Literal["low", "medium", "high"] = "medium"


class ValueCreationAction(BaseModel):
    company: str
    action: str
    owner: str = ""
    target_date: Optional[date] = None


class ExitRecord(BaseModel):
    company: str
    status: Literal["closed", "in_process", "preparing"] = "closed"
    proceeds_eur_m: Optional[float] = None
    moic: Optional[float] = None
    notes: str = ""


class IcAsk(BaseModel):
    """One IC-level ask or decision request from this meeting."""

    label: str
    detail: str = ""


class PortfolioReviewFacts(BaseModel):
    """Input shape for the internal portfolio review composer."""

    fund_name: str
    vintage_year: int
    reporting_quarter: Literal["Q1", "Q2", "Q3", "Q4"]
    reporting_year: int
    review_date: date
    author: str = "GP Deal Team"
    company: str = "Aither"
    confidentiality: Literal[
        "public", "internal", "confidential", "restricted"
    ] = "internal"

    # Portfolio
    holdings: list[PortfolioCompany] = Field(default_factory=list)
    top_performers: list[TopPerformer] = Field(default_factory=list)
    watchlist: list[WatchlistItem] = Field(default_factory=list)
    value_creation_actions: list[ValueCreationAction] = Field(default_factory=list)

    # Capital deployment
    fund_size_eur_m: float
    invested_capital_eur_m: float
    reserved_capital_eur_m: float = 0.0
    available_dry_powder_eur_m: float = 0.0

    # Fund-level KPIs
    portfolio_nav_eur_m: float
    weighted_avg_moic: Optional[float] = None
    gross_irr_pct: Optional[float] = None
    net_irr_pct: Optional[float] = None
    realized_eur_m: float = 0.0
    unrealized_eur_m: float = 0.0

    # Exits
    exits: list[ExitRecord] = Field(default_factory=list)

    # Commentary
    market_view: str = ""
    sector_commentary: str = ""

    # Risks
    portfolio_risks: list[str] = Field(default_factory=list)

    # Asks
    ic_asks: list[IcAsk] = Field(default_factory=list)


# ── Formatters ───────────────────────────────────────────────────────────


def _format_eur(value: float) -> str:
    return f"€{value:,.1f}M"


def _format_pct(value: float) -> str:
    return f"{value * 100:.1f}%"


_STATUS_LABEL = {
    "outperforming": "OUTPERFORMING",
    "on_plan": "ON PLAN",
    "watchlist": "WATCHLIST",
    "underperforming": "UNDERPERFORMING",
    "exited": "EXITED",
}


# ── Slide builders ───────────────────────────────────────────────────────


def _title_slide(facts: PortfolioReviewFacts) -> dict[str, Any]:
    return {
        "slide_type": "title_slide",
        "elements": [
            HeadingElement(
                content=HeadingContent(
                    text=f"{facts.fund_name} — Portfolio Review"
                )
            ),
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
                        f"Internal Investment Committee Review · "
                        f"{facts.review_date.isoformat()}"
                    )
                )
            ),
        ],
    }


def _portfolio_overview_slide(facts: PortfolioReviewFacts) -> dict[str, Any]:
    if not facts.holdings:
        return {
            "slide_type": "table_slide",
            "elements": [
                HeadingElement(content=HeadingContent(text="Portfolio Overview")),
                BodyTextElement(
                    content=BodyTextContent(
                        text=(
                            "Portfolio table to be populated. "
                            "No holdings provided for this review."
                        )
                    )
                ),
            ],
        }
    headers = [
        "Company", "Sector", "Invested (€M)", "FMV (€M)", "MOIC", "Status"
    ]
    rows: list[list[str | float | int | None]] = []
    for h in facts.holdings:
        moic_cell = f"{h.moic:.2f}x" if h.moic is not None else "—"
        rows.append(
            [
                h.company,
                h.sector,
                f"{h.invested_eur_m:.1f}",
                f"{h.current_fmv_eur_m:.1f}",
                moic_cell,
                _STATUS_LABEL[h.status],
            ]
        )
    return {
        "slide_type": "table_slide",
        "elements": [
            HeadingElement(content=HeadingContent(text="Portfolio Overview")),
            TableElement(content=TableContent(headers=headers, rows=rows)),
        ],
    }


def _top_performers_slide(facts: PortfolioReviewFacts) -> dict[str, Any]:
    if not facts.top_performers:
        items = [
            "No standout performers in the period — portfolio in line with plan.",
            "Continue monitoring for breakout candidates.",
        ]
    else:
        items = []
        for performer in facts.top_performers:
            sign = "+" if performer.value_change_eur_m >= 0 else ""
            driver = f" — {performer.driver}" if performer.driver else ""
            items.append(
                f"{performer.company}: {sign}{performer.value_change_eur_m:.1f} €M{driver}"
            )
    return {
        "slide_type": "bullet_points",
        "elements": [
            HeadingElement(content=HeadingContent(text="Top Performers")),
            BulletListElement(content=BulletListContent(items=items)),
        ],
    }


def _watchlist_slide(facts: PortfolioReviewFacts) -> dict[str, Any]:
    if not facts.watchlist:
        items = [
            "No companies on watchlist — full portfolio at or above plan.",
        ]
    else:
        items = [
            f"[{item.severity.upper()}] {item.company}: {item.issue}"
            for item in facts.watchlist
        ]
    return {
        "slide_type": "bullet_points",
        "elements": [
            HeadingElement(content=HeadingContent(text="Watchlist")),
            BulletListElement(content=BulletListContent(items=items)),
        ],
    }


def _value_creation_slide(facts: PortfolioReviewFacts) -> dict[str, Any]:
    if not facts.value_creation_actions:
        return {
            "slide_type": "table_slide",
            "elements": [
                HeadingElement(
                    content=HeadingContent(text="Value-Creation Actions")
                ),
                BodyTextElement(
                    content=BodyTextContent(
                        text=(
                            "No open value-creation actions tracked. "
                            "Add new initiatives to the next review."
                        )
                    )
                ),
            ],
        }
    headers = ["Company", "Action", "Owner", "Target Date"]
    rows: list[list[str | float | int | None]] = []
    for action in facts.value_creation_actions:
        date_cell = (
            action.target_date.isoformat() if action.target_date is not None else "—"
        )
        rows.append([action.company, action.action, action.owner or "—", date_cell])
    return {
        "slide_type": "table_slide",
        "elements": [
            HeadingElement(
                content=HeadingContent(text="Value-Creation Actions")
            ),
            TableElement(content=TableContent(headers=headers, rows=rows)),
        ],
    }


def _capital_deployment_slide(facts: PortfolioReviewFacts) -> dict[str, Any]:
    available = (
        facts.available_dry_powder_eur_m
        if facts.available_dry_powder_eur_m
        else max(
            facts.fund_size_eur_m
            - facts.invested_capital_eur_m
            - facts.reserved_capital_eur_m,
            0.0,
        )
    )
    chart_data = BarChartData(
        categories=["Invested", "Reserved", "Dry Powder"],
        series=[
            ChartDataSeries(
                name="Capital (€M)",
                values=[
                    facts.invested_capital_eur_m,
                    facts.reserved_capital_eur_m,
                    available,
                ],
            )
        ],
        title="Capital Deployment (EUR M)",
    )
    summary = (
        f"Fund {_format_eur(facts.fund_size_eur_m)} · "
        f"Invested {_format_eur(facts.invested_capital_eur_m)} · "
        f"Dry Powder {_format_eur(available)}"
    )
    return {
        "slide_type": "chart_slide",
        "elements": [
            HeadingElement(content=HeadingContent(text="Capital Deployment")),
            ChartElement(chart_data=chart_data),
            BodyTextElement(content=BodyTextContent(text=summary)),
        ],
    }


def _portfolio_metrics_slide(facts: PortfolioReviewFacts) -> dict[str, Any]:
    metrics: list[KpiCardContent] = [
        KpiCardContent(
            label="Portfolio NAV", value=_format_eur(facts.portfolio_nav_eur_m)
        ),
        KpiCardContent(
            label="Realized", value=_format_eur(facts.realized_eur_m)
        ),
        KpiCardContent(
            label="Unrealized", value=_format_eur(facts.unrealized_eur_m)
        ),
    ]
    if facts.weighted_avg_moic is not None:
        metrics.append(
            KpiCardContent(
                label="Wtd Avg MOIC", value=f"{facts.weighted_avg_moic:.2f}x"
            )
        )
    if facts.gross_irr_pct is not None:
        metrics.append(
            KpiCardContent(
                label="Gross IRR", value=_format_pct(facts.gross_irr_pct)
            )
        )
    if facts.net_irr_pct is not None:
        metrics.append(
            KpiCardContent(label="Net IRR", value=_format_pct(facts.net_irr_pct))
        )
    return {
        "slide_type": "stats_callout",
        "elements": [
            HeadingElement(
                content=HeadingContent(text="Portfolio Metrics Dashboard")
            ),
            MetricGroupElement(content=MetricGroupContent(metrics=metrics)),
        ],
    }


def _exits_slide(facts: PortfolioReviewFacts) -> dict[str, Any]:
    if not facts.exits:
        return {
            "slide_type": "table_slide",
            "elements": [
                HeadingElement(
                    content=HeadingContent(text="Exits & Realizations")
                ),
                BodyTextElement(
                    content=BodyTextContent(
                        text=(
                            "No closed or in-process exits this period. "
                            "Pipeline tracking continues."
                        )
                    )
                ),
            ],
        }
    headers = ["Company", "Status", "Proceeds (€M)", "MOIC", "Notes"]
    rows: list[list[str | float | int | None]] = []
    for exit_record in facts.exits:
        proceeds_cell = (
            f"{exit_record.proceeds_eur_m:.1f}"
            if exit_record.proceeds_eur_m is not None
            else "—"
        )
        moic_cell = (
            f"{exit_record.moic:.2f}x" if exit_record.moic is not None else "—"
        )
        rows.append(
            [
                exit_record.company,
                exit_record.status.replace("_", " ").upper(),
                proceeds_cell,
                moic_cell,
                exit_record.notes,
            ]
        )
    return {
        "slide_type": "table_slide",
        "elements": [
            HeadingElement(content=HeadingContent(text="Exits & Realizations")),
            TableElement(content=TableContent(headers=headers, rows=rows)),
        ],
    }


def _market_view_slide(facts: PortfolioReviewFacts) -> dict[str, Any]:
    headline = facts.market_view or (
        "Market conditions stable. Selective deployment opportunities "
        "across target sectors."
    )
    detail = facts.sector_commentary or (
        "Sector-specific tailwinds and headwinds being monitored. "
        "Watchlist updated as conditions evolve."
    )
    return {
        "slide_type": "key_message",
        "elements": [
            HeadingElement(content=HeadingContent(text="Market View")),
            SubheadingElement(content=SubheadingContent(text=headline)),
            BodyTextElement(content=BodyTextContent(text=detail)),
        ],
    }


def _risks_slide(facts: PortfolioReviewFacts) -> dict[str, Any]:
    items = facts.portfolio_risks or [
        "No material portfolio-level risks identified this period.",
        "Continue ongoing monitoring of macro and sector indicators.",
    ]
    return {
        "slide_type": "bullet_points",
        "elements": [
            HeadingElement(content=HeadingContent(text="Key Risks")),
            BulletListElement(content=BulletListContent(items=items)),
        ],
    }


def _asks_slide(facts: PortfolioReviewFacts) -> dict[str, Any]:
    if facts.ic_asks:
        items = [
            f"{ask.label}" + (f" — {ask.detail}" if ask.detail else "")
            for ask in facts.ic_asks
        ]
    else:
        items = [
            "No formal asks for this review — informational update only.",
            "Next review will include capital allocation requests.",
        ]
    return {
        "slide_type": "key_message",
        "elements": [
            HeadingElement(content=HeadingContent(text="Asks & Decisions")),
            BulletListElement(content=BulletListContent(items=items)),
        ],
    }


# ── Public composer ──────────────────────────────────────────────────────


def compose_portfolio_review(facts: PortfolioReviewFacts) -> Presentation:
    """Turn PortfolioReviewFacts into an 11-slide internal portfolio review.

    Output is a fully validated IR ready for render_pipeline or /v1/render.
    Uses the ``finance-pro`` theme. Audience=BOARD, purpose=QUARTERLY_REVIEW.
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
            f"{facts.reporting_year} Portfolio Review"
        ),
        subtitle=f"Vintage {facts.vintage_year}",
        author=facts.author,
        company=facts.company,
        date=facts.review_date.isoformat(),
        language="en",
        purpose=Purpose.QUARTERLY_REVIEW,
        audience=Audience.BOARD,
        confidentiality=confidentiality_map.get(
            facts.confidentiality, Confidentiality.INTERNAL
        ),
    )

    slides = [
        _title_slide(facts),
        _portfolio_overview_slide(facts),
        _top_performers_slide(facts),
        _watchlist_slide(facts),
        _value_creation_slide(facts),
        _capital_deployment_slide(facts),
        _portfolio_metrics_slide(facts),
        _exits_slide(facts),
        _market_view_slide(facts),
        _risks_slide(facts),
        _asks_slide(facts),
    ]

    return Presentation(
        schema_version="1.0",
        metadata=metadata,
        theme="finance-pro",
        slides=slides,  # type: ignore[arg-type]
    )
