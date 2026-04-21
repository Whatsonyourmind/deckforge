"""Tests for the deal teaser composer."""
from __future__ import annotations

from datetime import date

from deckforge.compose.teaser import (
    ProcessMilestone,
    TeaserFacts,
    compose_teaser,
)
from deckforge.ir.enums import Audience, Confidentiality, Purpose


def _sample_teaser() -> TeaserFacts:
    return TeaserFacts(
        project_codename="Project Aurora",
        company_real_name="Aurora S.p.A.",
        anonymized=True,
        sector="Industrial Automation",
        vertical="pe",
        country="IT",
        geography_detail="Lombardia",
        deal_date=date(2026, 5, 1),
        author="Advisor",
        company="Aither",
        one_line_thesis=(
            "Italian mid-cap automation leader with 40% EBITDA margin "
            "and 15% export growth."
        ),
        revenue_eur_m=80.0,
        ebitda_eur_m=20.0,
        ebitda_margin_pct=0.25,
        ask_eur_m=120.0,
        enterprise_value_eur_m=180.0,
        company_snapshot_bullets=[
            "Family-owned, 35 years operating history",
            "3 manufacturing plants in Northern Italy",
            "Top-3 supplier in DACH region",
        ],
        investment_highlights=[
            "Defensible market position with 25% share in niche verticals",
            "Buy-and-build opportunity — 4 identified adjacencies",
            "Succession-driven sale, motivated seller",
        ],
        process_milestones=[
            ProcessMilestone(label="Teaser circulated", date=date(2026, 5, 1)),
            ProcessMilestone(label="IOIs due", date=date(2026, 5, 30)),
            ProcessMilestone(label="Management presentations", date=date(2026, 6, 15)),
            ProcessMilestone(label="Binding bids", date=date(2026, 7, 20)),
        ],
        contact_name="Deal Captain",
        contact_role="Managing Director",
        contact_email="advisor@aither.example",
    )


def test_compose_produces_6_slides():
    pres = compose_teaser(_sample_teaser())
    assert len(pres.slides) == 6


def test_compose_uses_finance_pro_theme():
    pres = compose_teaser(_sample_teaser())
    assert pres.theme == "finance-pro"


def test_compose_sets_sales_pitch_metadata():
    pres = compose_teaser(_sample_teaser())
    assert pres.metadata.purpose == Purpose.SALES_PITCH
    assert pres.metadata.audience == Audience.CLIENTS
    assert pres.metadata.confidentiality == Confidentiality.CONFIDENTIAL
    assert "Teaser" in pres.metadata.title


def test_compose_slide_spine_is_stable():
    pres = compose_teaser(_sample_teaser())
    expected = [
        "title_slide",
        "key_message",
        "deal_overview",
        "investment_thesis",
        "timeline",
        "key_message",
    ]
    assert [s.slide_type for s in pres.slides] == expected


def test_anonymized_uses_codename_only():
    facts = _sample_teaser()
    facts.anonymized = True
    pres = compose_teaser(facts)
    title_el = pres.slides[0].elements[0]
    assert "Aurora S.p.A." not in title_el.content.text
    assert "Project Aurora" in title_el.content.text


def test_non_anonymized_reveals_real_name():
    facts = _sample_teaser()
    facts.anonymized = False
    pres = compose_teaser(facts)
    title_el = pres.slides[0].elements[0]
    assert "Aurora S.p.A." in title_el.content.text


def test_executive_summary_carries_thesis_and_size():
    pres = compose_teaser(_sample_teaser())
    es = pres.slides[1]
    subheading = es.elements[1]
    body = es.elements[2]
    assert "40% EBITDA" in subheading.content.text
    assert "EV" in body.content.text
    assert "EBITDA" in body.content.text


def test_snapshot_slide_carries_kpis_when_financials_given():
    pres = compose_teaser(_sample_teaser())
    snapshot = pres.slides[2]
    kinds = [el.type for el in snapshot.elements]
    # heading + bullet list + metric group
    assert "metric_group" in kinds


def test_snapshot_slide_drops_kpis_when_financials_absent():
    facts = _sample_teaser()
    facts.revenue_eur_m = None
    facts.ebitda_eur_m = None
    facts.ebitda_margin_pct = None
    pres = compose_teaser(facts)
    snapshot = pres.slides[2]
    kinds = [el.type for el in snapshot.elements]
    assert "metric_group" not in kinds


def test_highlights_falls_back_to_defaults_when_none_provided():
    facts = _sample_teaser()
    facts.investment_highlights = []
    pres = compose_teaser(facts)
    highlights = pres.slides[3]
    bullet_el = highlights.elements[1]
    assert len(bullet_el.content.items) >= 3


def test_process_milestones_surface_as_dated_bullets():
    pres = compose_teaser(_sample_teaser())
    timeline = pres.slides[4]
    bullet_el = timeline.elements[1]
    joined = "\n".join(bullet_el.content.items)
    assert "2026-05-30" in joined
    assert "IOIs due" in joined


def test_contact_slide_includes_email_and_name():
    pres = compose_teaser(_sample_teaser())
    contact = pres.slides[5]
    body = contact.elements[1]
    assert "advisor@aither.example" in body.content.text
    assert "Deal Captain" in body.content.text


def test_vertical_agnostic():
    for vertical in ["pe", "re", "infrastructure", "credit", "npl", "vc", "m_and_a"]:
        facts = _sample_teaser()
        facts.vertical = vertical  # type: ignore[assignment]
        pres = compose_teaser(facts)
        assert len(pres.slides) == 6
