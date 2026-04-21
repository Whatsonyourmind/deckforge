"""Deal teaser composer.

Produces a short anonymized teaser deck used for initial buyer / LP outreach:

    1. Title (project codename + sector + date)
    2. Executive Summary (one-line thesis + size + timing)
    3. Company Snapshot (bullet list: sector, geography, scale, key metric)
    4. Investment Highlights (3-5 bullets)
    5. Process & Timeline (milestones)
    6. Contact (advisor / sponsor)

The teaser shape is intentionally anonymizable — pass a ``project_codename``
and set ``anonymized=True`` to suppress company_real_name from output.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from deckforge.ir.elements.data import KpiCardContent, MetricGroupContent, MetricGroupElement
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


class ProcessMilestone(BaseModel):
    label: str
    date: date


class TeaserFacts(BaseModel):
    """Input shape for the deal teaser composer."""

    project_codename: str
    company_real_name: Optional[str] = None
    anonymized: bool = True

    sector: str = "Private Markets"
    vertical: Literal[
        "pe", "re", "infrastructure", "credit", "npl", "vc", "m_and_a"
    ] = "pe"
    country: str = "IT"
    geography_detail: str = ""
    deal_date: date
    author: str = "Advisor"
    company: str = "Aither"
    confidentiality: Literal[
        "public", "internal", "confidential", "restricted"
    ] = "confidential"

    one_line_thesis: str = ""

    revenue_eur_m: Optional[float] = None
    ebitda_eur_m: Optional[float] = None
    ebitda_margin_pct: Optional[float] = None
    ask_eur_m: Optional[float] = None
    enterprise_value_eur_m: Optional[float] = None

    company_snapshot_bullets: list[str] = Field(default_factory=list)
    investment_highlights: list[str] = Field(default_factory=list)

    process_milestones: list[ProcessMilestone] = Field(default_factory=list)

    contact_name: str = ""
    contact_role: str = ""
    contact_email: str = ""
    contact_phone: str = ""


def _format_eur(value: float) -> str:
    return f"€{value:,.1f}M"


def _format_pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _display_name(facts: TeaserFacts) -> str:
    if facts.anonymized or not facts.company_real_name:
        return facts.project_codename
    return f"{facts.company_real_name} ({facts.project_codename})"


def _title_slide(facts: TeaserFacts) -> dict[str, Any]:
    return {
        "slide_type": "title_slide",
        "elements": [
            HeadingElement(content=HeadingContent(text=_display_name(facts))),
            SubheadingElement(
                content=SubheadingContent(
                    text=(
                        f"{facts.sector} · {facts.country} · "
                        f"{facts.deal_date.isoformat()}"
                    )
                )
            ),
            BodyTextElement(
                content=BodyTextContent(
                    text=f"Confidential Teaser — {facts.company}"
                )
            ),
        ],
    }


def _executive_summary_slide(facts: TeaserFacts) -> dict[str, Any]:
    thesis = facts.one_line_thesis or (
        "High-conviction opportunity with clear value-creation levers."
    )
    parts: list[str] = []
    if facts.enterprise_value_eur_m is not None:
        parts.append(f"EV {_format_eur(facts.enterprise_value_eur_m)}")
    if facts.revenue_eur_m is not None:
        parts.append(f"Revenue {_format_eur(facts.revenue_eur_m)}")
    if facts.ebitda_eur_m is not None:
        parts.append(f"EBITDA {_format_eur(facts.ebitda_eur_m)}")
    if facts.ask_eur_m is not None:
        parts.append(f"Ask {_format_eur(facts.ask_eur_m)}")
    summary_line = " · ".join(parts) if parts else "Size and ask to be confirmed."
    return {
        "slide_type": "key_message",
        "elements": [
            HeadingElement(content=HeadingContent(text="Executive Summary")),
            SubheadingElement(content=SubheadingContent(text=thesis)),
            BodyTextElement(content=BodyTextContent(text=summary_line)),
        ],
    }


def _company_snapshot_slide(facts: TeaserFacts) -> dict[str, Any]:
    items = list(facts.company_snapshot_bullets)
    if not items:
        items = [
            f"Sector: {facts.sector}",
            f"Geography: {facts.country}"
            + (f" — {facts.geography_detail}" if facts.geography_detail else ""),
        ]
        if facts.revenue_eur_m is not None:
            items.append(f"Revenue: {_format_eur(facts.revenue_eur_m)}")
        if facts.ebitda_eur_m is not None:
            items.append(f"EBITDA: {_format_eur(facts.ebitda_eur_m)}")
        if facts.ebitda_margin_pct is not None:
            items.append(f"EBITDA margin: {_format_pct(facts.ebitda_margin_pct)}")

    elements: list[Any] = [
        HeadingElement(content=HeadingContent(text="Company Snapshot")),
        BulletListElement(content=BulletListContent(items=items)),
    ]

    kpis: list[KpiCardContent] = []
    if facts.revenue_eur_m is not None:
        kpis.append(KpiCardContent(label="Revenue", value=_format_eur(facts.revenue_eur_m)))
    if facts.ebitda_eur_m is not None:
        kpis.append(KpiCardContent(label="EBITDA", value=_format_eur(facts.ebitda_eur_m)))
    if facts.ebitda_margin_pct is not None:
        kpis.append(
            KpiCardContent(
                label="EBITDA Margin", value=_format_pct(facts.ebitda_margin_pct)
            )
        )
    if kpis:
        elements.append(MetricGroupElement(content=MetricGroupContent(metrics=kpis)))

    return {
        "slide_type": "deal_overview",
        "elements": elements,
    }


def _highlights_slide(facts: TeaserFacts) -> dict[str, Any]:
    items = facts.investment_highlights or [
        "Defensible market position with pricing power.",
        "Attractive entry valuation vs sector comps.",
        "Multiple value-creation levers under new ownership.",
    ]
    return {
        "slide_type": "investment_thesis",
        "elements": [
            HeadingElement(content=HeadingContent(text="Investment Highlights")),
            BulletListElement(content=BulletListContent(items=items)),
        ],
    }


def _process_slide(facts: TeaserFacts) -> dict[str, Any]:
    if facts.process_milestones:
        items = [
            f"{m.date.isoformat()} — {m.label}" for m in facts.process_milestones
        ]
    else:
        items = [
            "Process letter with bid instructions circulated.",
            "Management presentation in data room.",
            "First-round bids — indicative.",
            "Shortlist to second round — binding.",
            "Signing.",
        ]
    return {
        "slide_type": "timeline",
        "elements": [
            HeadingElement(content=HeadingContent(text="Process & Timeline")),
            BulletListElement(content=BulletListContent(items=items)),
        ],
    }


def _contact_slide(facts: TeaserFacts) -> dict[str, Any]:
    lines: list[str] = []
    if facts.contact_name:
        role = f" — {facts.contact_role}" if facts.contact_role else ""
        lines.append(f"{facts.contact_name}{role}")
    if facts.contact_email:
        lines.append(facts.contact_email)
    if facts.contact_phone:
        lines.append(facts.contact_phone)
    if not lines:
        lines.append("Contact details to be shared with interested parties.")
    return {
        "slide_type": "key_message",
        "elements": [
            HeadingElement(content=HeadingContent(text="Contact")),
            BodyTextElement(content=BodyTextContent(text="\n".join(lines))),
        ],
    }


def compose_teaser(facts: TeaserFacts) -> Presentation:
    """Turn TeaserFacts into a 6-slide confidential teaser Presentation.

    Uses ``finance-pro`` theme. Slide spine:

        title_slide, key_message, deal_overview, investment_thesis,
        timeline, key_message
    """
    confidentiality_map = {
        "public": Confidentiality.PUBLIC,
        "internal": Confidentiality.INTERNAL,
        "confidential": Confidentiality.CONFIDENTIAL,
        "restricted": Confidentiality.RESTRICTED,
    }
    metadata = PresentationMetadata(
        title=f"{_display_name(facts)} — Teaser",
        subtitle=f"{facts.sector} · {facts.country}",
        author=facts.author,
        company=facts.company,
        date=facts.deal_date.isoformat(),
        language="en",
        purpose=Purpose.SALES_PITCH,
        audience=Audience.CLIENTS,
        confidentiality=confidentiality_map.get(
            facts.confidentiality, Confidentiality.CONFIDENTIAL
        ),
    )

    slides = [
        _title_slide(facts),
        _executive_summary_slide(facts),
        _company_snapshot_slide(facts),
        _highlights_slide(facts),
        _process_slide(facts),
        _contact_slide(facts),
    ]

    return Presentation(
        schema_version="1.0",
        metadata=metadata,
        theme="finance-pro",
        slides=slides,  # type: ignore[arg-type]
    )
