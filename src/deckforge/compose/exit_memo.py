"""Exit memo deck composer.

Portfolio company exit recommendation deck for the investment committee.
Slide spine:

    1. Title (portfolio company + "Exit Memo")
    2. Executive Summary (exit path + headline returns)
    3. Value Creation Bridge (waterfall: entry → EBITDA → multiple → debt → exit)
    4. Returns vs Underwrite (actual vs underwrite KPIs)
    5. Market Conditions (body text)
    6. Buyer Landscape (table of strategic + financial buyers)
    7. Process Timeline (key milestones)
    8. Recommendation (proceed / delay / hold with rationale)
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


class BuyerCandidate(BaseModel):
    name: str
    buyer_type: Literal["strategic", "financial", "secondary", "ipo"] = "strategic"
    country: str = "IT"
    fit_notes: str = ""
    indicated_range_eur_m: Optional[str] = None


class ExitMilestone(BaseModel):
    label: str
    date: date


class ExitMemoFacts(BaseModel):
    """Input shape for the exit memo composer."""

    deal_name: str
    sector: str = "Private Markets"
    vertical: Literal[
        "pe", "re", "infrastructure", "credit", "npl", "vc", "m_and_a"
    ] = "pe"
    country: str = "IT"
    exit_memo_date: date
    author: str = "Deal Team"
    company: str = "Aither"
    confidentiality: Literal[
        "public", "internal", "confidential", "restricted"
    ] = "confidential"

    # Entry vs current (or expected exit) snapshot
    entry_date: date
    entry_equity_eur_m: float
    entry_ev_eur_m: float
    entry_ebitda_eur_m: Optional[float] = None
    entry_multiple: Optional[float] = None

    expected_exit_date: date
    expected_exit_ev_eur_m: float
    expected_exit_ebitda_eur_m: Optional[float] = None
    expected_exit_multiple: Optional[float] = None

    # Value creation bridge components (EUR M)
    ebitda_growth_contribution_eur_m: float = 0.0
    multiple_expansion_contribution_eur_m: float = 0.0
    debt_paydown_contribution_eur_m: float = 0.0
    other_contribution_eur_m: float = 0.0

    # Returns
    actual_irr_pct: Optional[float] = None
    target_irr_pct: Optional[float] = None
    actual_moic: Optional[float] = None
    target_moic: Optional[float] = None
    actual_hold_years: Optional[float] = None
    target_hold_years: Optional[float] = None

    # Executive summary
    exit_headline: str = ""
    exit_thesis: str = ""

    # Market
    market_commentary: str = ""

    # Buyer landscape
    buyer_candidates: list[BuyerCandidate] = Field(default_factory=list)

    # Process
    milestones: list[ExitMilestone] = Field(default_factory=list)

    # Recommendation
    recommendation: Literal["proceed", "delay", "hold", "pivot"] = "proceed"
    recommendation_rationale: str = ""


def _format_eur(value: float) -> str:
    return f"€{value:,.1f}M"


def _format_pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _title_slide(facts: ExitMemoFacts) -> dict[str, Any]:
    return {
        "slide_type": "title_slide",
        "elements": [
            HeadingElement(content=HeadingContent(text=f"{facts.deal_name} — Exit")),
            SubheadingElement(
                content=SubheadingContent(
                    text=(
                        f"{facts.sector} · {facts.country} · "
                        f"{facts.exit_memo_date.isoformat()}"
                    )
                )
            ),
            BodyTextElement(
                content=BodyTextContent(
                    text=f"{facts.company} Investment Committee — Exit Memo"
                )
            ),
        ],
    }


def _executive_summary_slide(facts: ExitMemoFacts) -> dict[str, Any]:
    headline = facts.exit_headline or (
        f"Recommend proceed to exit of {facts.deal_name}."
    )
    thesis = facts.exit_thesis or (
        "Business has achieved underwrite milestones. "
        "Current market conditions support full realization."
    )
    hold = (
        f"Entered {facts.entry_date.year}, targeting exit "
        f"{facts.expected_exit_date.year}."
    )
    summary_line = (
        f"Entry EV {_format_eur(facts.entry_ev_eur_m)} → "
        f"Exit EV {_format_eur(facts.expected_exit_ev_eur_m)} · {hold}"
    )
    return {
        "slide_type": "key_message",
        "elements": [
            HeadingElement(content=HeadingContent(text="Executive Summary")),
            SubheadingElement(content=SubheadingContent(text=headline)),
            BodyTextElement(
                content=BodyTextContent(text=f"{thesis}\n{summary_line}")
            ),
        ],
    }


def _value_creation_bridge_slide(facts: ExitMemoFacts) -> dict[str, Any]:
    categories = [
        "Entry EV",
        "EBITDA Growth",
        "Multiple Expansion",
        "Debt Paydown",
        "Other",
        "Exit EV",
    ]
    residual = (
        facts.expected_exit_ev_eur_m
        - facts.entry_ev_eur_m
        - facts.ebitda_growth_contribution_eur_m
        - facts.multiple_expansion_contribution_eur_m
        - facts.debt_paydown_contribution_eur_m
        - facts.other_contribution_eur_m
    )
    other_total = facts.other_contribution_eur_m + residual
    values = [
        facts.entry_ev_eur_m,
        facts.ebitda_growth_contribution_eur_m,
        facts.multiple_expansion_contribution_eur_m,
        facts.debt_paydown_contribution_eur_m,
        other_total,
        facts.expected_exit_ev_eur_m,
    ]
    chart_data = WaterfallChartData(
        categories=categories,
        values=values,
        title="Value Creation Bridge (EUR M)",
    )
    return {
        "slide_type": "waterfall_chart",
        "elements": [
            HeadingElement(content=HeadingContent(text="Value Creation Bridge")),
            ChartElement(chart_data=chart_data),
        ],
    }


def _returns_vs_underwrite_slide(facts: ExitMemoFacts) -> dict[str, Any]:
    metrics: list[KpiCardContent] = []
    if facts.actual_irr_pct is not None:
        target = (
            f" (vs target {_format_pct(facts.target_irr_pct)})"
            if facts.target_irr_pct is not None
            else ""
        )
        metrics.append(
            KpiCardContent(
                label="Actual IRR",
                value=f"{_format_pct(facts.actual_irr_pct)}{target}",
            )
        )
    if facts.actual_moic is not None:
        target = (
            f" (vs target {facts.target_moic:.1f}x)"
            if facts.target_moic is not None
            else ""
        )
        metrics.append(
            KpiCardContent(
                label="Actual MOIC",
                value=f"{facts.actual_moic:.1f}x{target}",
            )
        )
    if facts.actual_hold_years is not None:
        target = (
            f" (vs plan {facts.target_hold_years:.1f}y)"
            if facts.target_hold_years is not None
            else ""
        )
        metrics.append(
            KpiCardContent(
                label="Hold Period",
                value=f"{facts.actual_hold_years:.1f}y{target}",
            )
        )
    if not metrics:
        metrics = [
            KpiCardContent(label="Entry EV", value=_format_eur(facts.entry_ev_eur_m)),
            KpiCardContent(
                label="Exit EV", value=_format_eur(facts.expected_exit_ev_eur_m)
            ),
        ]
    return {
        "slide_type": "stats_callout",
        "elements": [
            HeadingElement(content=HeadingContent(text="Returns vs Underwrite")),
            MetricGroupElement(content=MetricGroupContent(metrics=metrics)),
        ],
    }


def _market_conditions_slide(facts: ExitMemoFacts) -> dict[str, Any]:
    commentary = facts.market_commentary or (
        "Market conditions supportive of exit. "
        "Strategic interest strong and financial sponsor dry powder at record levels."
    )
    return {
        "slide_type": "key_message",
        "elements": [
            HeadingElement(content=HeadingContent(text="Market Conditions")),
            BodyTextElement(content=BodyTextContent(text=commentary)),
        ],
    }


def _buyer_landscape_slide(facts: ExitMemoFacts) -> dict[str, Any]:
    if not facts.buyer_candidates:
        return {
            "slide_type": "table_slide",
            "elements": [
                HeadingElement(content=HeadingContent(text="Buyer Landscape")),
                BodyTextElement(
                    content=BodyTextContent(
                        text=(
                            "Buyer universe mapping to be finalized in "
                            "partnership with advisor."
                        )
                    )
                ),
            ],
        }
    headers = ["Buyer", "Type", "Country", "Indicated Range", "Fit Notes"]
    rows: list[list[str | float | int | None]] = [
        [
            b.name,
            b.buyer_type.upper(),
            b.country,
            b.indicated_range_eur_m or "—",
            b.fit_notes,
        ]
        for b in facts.buyer_candidates
    ]
    return {
        "slide_type": "table_slide",
        "elements": [
            HeadingElement(content=HeadingContent(text="Buyer Landscape")),
            TableElement(content=TableContent(headers=headers, rows=rows)),
        ],
    }


def _timeline_slide(facts: ExitMemoFacts) -> dict[str, Any]:
    if facts.milestones:
        items = [f"{m.date.isoformat()} — {m.label}" for m in facts.milestones]
    else:
        items = [
            "Advisor appointment and process letter drafting.",
            "Confidential marketing to shortlisted buyers.",
            "First-round bids (IOIs).",
            "Management presentations and data room access.",
            "Binding bids.",
            "SPA signing and closing.",
        ]
    return {
        "slide_type": "timeline",
        "elements": [
            HeadingElement(content=HeadingContent(text="Process Timeline")),
            BulletListElement(content=BulletListContent(items=items)),
        ],
    }


def _recommendation_slide(facts: ExitMemoFacts) -> dict[str, Any]:
    label_map = {
        "proceed": "PROCEED TO EXIT",
        "delay": "DELAY EXIT",
        "hold": "HOLD AND REASSESS",
        "pivot": "PIVOT EXIT PATH",
    }
    label = label_map[facts.recommendation]
    rationale = facts.recommendation_rationale or (
        "See returns + market + buyer landscape for full rationale."
    )
    return {
        "slide_type": "key_message",
        "elements": [
            HeadingElement(
                content=HeadingContent(text=f"Recommendation: {label}")
            ),
            BodyTextElement(content=BodyTextContent(text=rationale)),
        ],
    }


def compose_exit_memo(facts: ExitMemoFacts) -> Presentation:
    """Turn ExitMemoFacts into an 8-slide exit memo Presentation.

    Uses the ``finance-pro`` theme. Audience=BOARD, purpose=IC_PRESENTATION.
    """
    confidentiality_map = {
        "public": Confidentiality.PUBLIC,
        "internal": Confidentiality.INTERNAL,
        "confidential": Confidentiality.CONFIDENTIAL,
        "restricted": Confidentiality.RESTRICTED,
    }
    metadata = PresentationMetadata(
        title=f"{facts.deal_name} — Exit Memo",
        subtitle=f"{facts.sector} · {facts.country}",
        author=facts.author,
        company=facts.company,
        date=facts.exit_memo_date.isoformat(),
        language="en",
        purpose=Purpose.IC_PRESENTATION,
        audience=Audience.BOARD,
        confidentiality=confidentiality_map.get(
            facts.confidentiality, Confidentiality.CONFIDENTIAL
        ),
    )

    slides = [
        _title_slide(facts),
        _executive_summary_slide(facts),
        _value_creation_bridge_slide(facts),
        _returns_vs_underwrite_slide(facts),
        _market_conditions_slide(facts),
        _buyer_landscape_slide(facts),
        _timeline_slide(facts),
        _recommendation_slide(facts),
    ]

    return Presentation(
        schema_version="1.0",
        metadata=metadata,
        theme="finance-pro",
        slides=slides,  # type: ignore[arg-type]
    )
