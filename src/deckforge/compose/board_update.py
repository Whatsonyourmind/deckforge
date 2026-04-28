"""Board update composer.

Monthly or quarterly board update presented by portfolio company
operators (CEO/CFO) to their board of directors. Operating-company
focused, with a tilt toward growth-stage SaaS / tech companies but
vertical-agnostic. Slide spine:

    1.  Title (company + period)
    2.  Period Highlights (key_message — top 3-5 wins / events)
    3.  KPI Scorecard (stats_callout — north-star + supporting metrics)
    4.  Financials Snapshot (table — revenue / EBITDA / cash actuals + plan)
    5.  Hiring & Org (bullet_points — headcount + key hires)
    6.  Product & GTM Update (bullet_points — shipped features + pipeline)
    7.  Risks & Challenges (bullet_points — what's not working + asks)
    8.  Board Asks & Decisions (key_message — explicit decision requests)
    9.  Appendix (appendix — supporting detail link / next meeting)

Vertical-agnostic but optimised for operating-company language (KPI,
runway, headcount). Vertical-specific metrics go in ``sector_metrics``.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from deckforge.ir.elements.data import (
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


class KpiScorecardEntry(BaseModel):
    """One KPI on the board scorecard."""

    label: str
    value: str
    target: Optional[str] = None
    trend: Literal["up", "down", "flat"] = "flat"


class FinancialRow(BaseModel):
    """One row of the financial snapshot table."""

    metric: str
    actual: float
    plan: Optional[float] = None
    prior_period: Optional[float] = None
    unit: str = "€k"


class BoardAsk(BaseModel):
    """One explicit decision request to the board."""

    label: str
    detail: str = ""
    decision_required_by: Optional[date] = None


class BoardUpdateFacts(BaseModel):
    """Input shape for the portfolio-company board update composer.

    Vertical-agnostic so the same model serves SaaS, marketplace,
    consumer, and fintech operating companies.
    """

    # Identity
    company_name: str
    period_label: str  # e.g. "Q1 2026" or "March 2026"
    period_end_date: date
    cadence: Literal["monthly", "quarterly", "annual"] = "monthly"
    author: str = "CEO"
    company: str = ""
    confidentiality: Literal[
        "public", "internal", "confidential", "restricted"
    ] = "confidential"

    # Highlights
    headline: str = ""
    period_highlights: list[str] = Field(default_factory=list)

    # KPI scorecard
    kpi_entries: list[KpiScorecardEntry] = Field(default_factory=list)

    # Financials
    financial_rows: list[FinancialRow] = Field(default_factory=list)
    cash_balance_eur_k: Optional[float] = None
    runway_months: Optional[float] = None
    burn_rate_eur_k_per_month: Optional[float] = None

    # Hiring & org
    headcount_total: Optional[int] = None
    headcount_change_period: Optional[int] = None
    key_hires: list[str] = Field(default_factory=list)
    org_notes: list[str] = Field(default_factory=list)

    # Product & GTM
    product_updates: list[str] = Field(default_factory=list)
    gtm_updates: list[str] = Field(default_factory=list)

    # Risks
    risks: list[str] = Field(default_factory=list)

    # Asks
    board_asks: list[BoardAsk] = Field(default_factory=list)

    # Appendix
    appendix_link: str = ""
    next_meeting_date: Optional[date] = None

    # Vertical-specific extras
    sector_metrics: dict[str, Any] = Field(default_factory=dict)


# ── Formatters ───────────────────────────────────────────────────────────


def _format_eur_k(value: float) -> str:
    return f"€{value:,.0f}k"


def _format_unit(value: float, unit: str) -> str:
    if unit in {"€k", "€M", "$k", "$M"}:
        prefix = unit[0]
        scale = unit[1:]
        return f"{prefix}{value:,.0f}{scale}"
    return f"{value:,.0f} {unit}".strip()


_TREND_ARROW = {"up": "▲", "down": "▼", "flat": "→"}


# ── Slide builders ───────────────────────────────────────────────────────


def _title_slide(facts: BoardUpdateFacts) -> dict[str, Any]:
    cadence_label = {
        "monthly": "Monthly Board Update",
        "quarterly": "Quarterly Board Update",
        "annual": "Annual Board Update",
    }[facts.cadence]
    return {
        "slide_type": "title_slide",
        "elements": [
            HeadingElement(content=HeadingContent(text=facts.company_name)),
            SubheadingElement(
                content=SubheadingContent(
                    text=f"{cadence_label} · {facts.period_label}"
                )
            ),
            BodyTextElement(
                content=BodyTextContent(
                    text=(
                        f"Period ending {facts.period_end_date.isoformat()} · "
                        f"Prepared by {facts.author}"
                    )
                )
            ),
        ],
    }


def _highlights_slide(facts: BoardUpdateFacts) -> dict[str, Any]:
    headline = facts.headline or (
        f"{facts.company_name} on plan for {facts.period_label}."
    )
    items = facts.period_highlights or [
        "Headline KPIs tracking to plan.",
        "No material changes to strategy or roadmap.",
        "Detailed metrics on the following slides.",
    ]
    return {
        "slide_type": "key_message",
        "elements": [
            HeadingElement(content=HeadingContent(text="Period Highlights")),
            SubheadingElement(content=SubheadingContent(text=headline)),
            BulletListElement(content=BulletListContent(items=items)),
        ],
    }


def _kpi_scorecard_slide(facts: BoardUpdateFacts) -> dict[str, Any]:
    if facts.kpi_entries:
        metrics: list[KpiCardContent] = []
        for kpi in facts.kpi_entries:
            arrow = _TREND_ARROW[kpi.trend]
            target_suffix = f" (target {kpi.target})" if kpi.target else ""
            metrics.append(
                KpiCardContent(
                    label=kpi.label,
                    value=f"{kpi.value} {arrow}{target_suffix}",
                )
            )
    else:
        metrics = [
            KpiCardContent(label="ARR", value="To be reported"),
            KpiCardContent(label="Net New", value="To be reported"),
            KpiCardContent(label="NRR", value="To be reported"),
        ]
    return {
        "slide_type": "stats_callout",
        "elements": [
            HeadingElement(content=HeadingContent(text="KPI Scorecard")),
            MetricGroupElement(content=MetricGroupContent(metrics=metrics)),
        ],
    }


def _financials_slide(facts: BoardUpdateFacts) -> dict[str, Any]:
    elements: list[Any] = [
        HeadingElement(content=HeadingContent(text="Financials Snapshot")),
    ]
    if facts.financial_rows:
        headers = ["Metric", "Actual", "Plan", "Prior", "vs Plan"]
        rows: list[list[str | float | int | None]] = []
        for row in facts.financial_rows:
            actual_cell = _format_unit(row.actual, row.unit)
            plan_cell = (
                _format_unit(row.plan, row.unit)
                if row.plan is not None
                else "—"
            )
            prior_cell = (
                _format_unit(row.prior_period, row.unit)
                if row.prior_period is not None
                else "—"
            )
            if row.plan is not None and row.plan != 0:
                vs_plan_pct = (row.actual - row.plan) / abs(row.plan) * 100
                vs_plan_cell = f"{vs_plan_pct:+.1f}%"
            else:
                vs_plan_cell = "—"
            rows.append(
                [row.metric, actual_cell, plan_cell, prior_cell, vs_plan_cell]
            )
        elements.append(TableElement(content=TableContent(headers=headers, rows=rows)))
    else:
        elements.append(
            BodyTextElement(
                content=BodyTextContent(
                    text="Financial snapshot to be populated this period."
                )
            )
        )
    cash_parts: list[str] = []
    if facts.cash_balance_eur_k is not None:
        cash_parts.append(f"Cash {_format_eur_k(facts.cash_balance_eur_k)}")
    if facts.runway_months is not None:
        cash_parts.append(f"Runway {facts.runway_months:.1f}mo")
    if facts.burn_rate_eur_k_per_month is not None:
        cash_parts.append(
            f"Burn {_format_eur_k(facts.burn_rate_eur_k_per_month)}/mo"
        )
    if cash_parts:
        elements.append(
            BodyTextElement(content=BodyTextContent(text=" · ".join(cash_parts)))
        )
    return {
        "slide_type": "table_slide",
        "elements": elements,
    }


def _hiring_org_slide(facts: BoardUpdateFacts) -> dict[str, Any]:
    items: list[str] = []
    if facts.headcount_total is not None:
        change_suffix = ""
        if facts.headcount_change_period is not None:
            sign = "+" if facts.headcount_change_period >= 0 else ""
            change_suffix = f" ({sign}{facts.headcount_change_period} this period)"
        items.append(f"Total headcount: {facts.headcount_total}{change_suffix}")
    for hire in facts.key_hires:
        items.append(f"Key hire: {hire}")
    items.extend(facts.org_notes)
    if not items:
        items = [
            "Headcount stable this period.",
            "No material org changes.",
        ]
    return {
        "slide_type": "bullet_points",
        "elements": [
            HeadingElement(content=HeadingContent(text="Hiring & Org")),
            BulletListElement(content=BulletListContent(items=items)),
        ],
    }


def _product_gtm_slide(facts: BoardUpdateFacts) -> dict[str, Any]:
    items: list[str] = []
    for update in facts.product_updates:
        items.append(f"Product: {update}")
    for update in facts.gtm_updates:
        items.append(f"GTM: {update}")
    if not items:
        items = [
            "Product: roadmap on track, no major launches this period.",
            "GTM: pipeline coverage in line with plan.",
        ]
    return {
        "slide_type": "bullet_points",
        "elements": [
            HeadingElement(content=HeadingContent(text="Product & GTM Update")),
            BulletListElement(content=BulletListContent(items=items)),
        ],
    }


def _risks_slide(facts: BoardUpdateFacts) -> dict[str, Any]:
    items = facts.risks or [
        "No material risks or challenges to flag this period.",
        "Continue ongoing monitoring across key operating metrics.",
    ]
    return {
        "slide_type": "bullet_points",
        "elements": [
            HeadingElement(content=HeadingContent(text="Risks & Challenges")),
            BulletListElement(content=BulletListContent(items=items)),
        ],
    }


def _board_asks_slide(facts: BoardUpdateFacts) -> dict[str, Any]:
    if facts.board_asks:
        items = []
        for ask in facts.board_asks:
            line = ask.label
            if ask.detail:
                line += f" — {ask.detail}"
            if ask.decision_required_by is not None:
                line += f" (decision by {ask.decision_required_by.isoformat()})"
            items.append(line)
    else:
        items = [
            "No formal asks for this meeting — informational update only.",
        ]
    return {
        "slide_type": "key_message",
        "elements": [
            HeadingElement(content=HeadingContent(text="Board Asks & Decisions")),
            BulletListElement(content=BulletListContent(items=items)),
        ],
    }


def _appendix_slide(facts: BoardUpdateFacts) -> dict[str, Any]:
    lines: list[str] = []
    if facts.appendix_link:
        lines.append(f"Detail pack: {facts.appendix_link}")
    if facts.next_meeting_date is not None:
        lines.append(f"Next meeting: {facts.next_meeting_date.isoformat()}")
    if not lines:
        lines.append(
            "Supporting detail available on request. Next meeting TBD."
        )
    return {
        "slide_type": "appendix",
        "elements": [
            HeadingElement(content=HeadingContent(text="Appendix")),
            BodyTextElement(content=BodyTextContent(text="\n".join(lines))),
        ],
    }


# ── Public composer ──────────────────────────────────────────────────────


def compose_board_update(facts: BoardUpdateFacts) -> Presentation:
    """Turn BoardUpdateFacts into a 9-slide portfolio-company board update.

    Output is a fully validated IR ready for render_pipeline or /v1/render.
    Uses the ``finance-pro`` theme. Audience=BOARD, purpose=BOARD_MEETING.
    """
    confidentiality_map = {
        "public": Confidentiality.PUBLIC,
        "internal": Confidentiality.INTERNAL,
        "confidential": Confidentiality.CONFIDENTIAL,
        "restricted": Confidentiality.RESTRICTED,
    }
    metadata = PresentationMetadata(
        title=(
            f"{facts.company_name} — {facts.period_label} Board Update"
        ),
        subtitle=f"Period ending {facts.period_end_date.isoformat()}",
        author=facts.author,
        company=facts.company or facts.company_name,
        date=facts.period_end_date.isoformat(),
        language="en",
        purpose=Purpose.BOARD_MEETING,
        audience=Audience.BOARD,
        confidentiality=confidentiality_map.get(
            facts.confidentiality, Confidentiality.CONFIDENTIAL
        ),
    )

    slides = [
        _title_slide(facts),
        _highlights_slide(facts),
        _kpi_scorecard_slide(facts),
        _financials_slide(facts),
        _hiring_org_slide(facts),
        _product_gtm_slide(facts),
        _risks_slide(facts),
        _board_asks_slide(facts),
        _appendix_slide(facts),
    ]

    return Presentation(
        schema_version="1.0",
        metadata=metadata,
        theme="finance-pro",
        slides=slides,  # type: ignore[arg-type]
    )
