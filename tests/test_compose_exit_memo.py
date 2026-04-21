"""Tests for the exit memo composer."""
from __future__ import annotations

from datetime import date

from deckforge.compose.exit_memo import (
    BuyerCandidate,
    ExitMemoFacts,
    ExitMilestone,
    compose_exit_memo,
)
from deckforge.ir.enums import Audience, Confidentiality, Purpose


def _sample_exit() -> ExitMemoFacts:
    return ExitMemoFacts(
        deal_name="Project Navigli",
        sector="Real Estate — PBSA",
        vertical="re",
        country="IT",
        exit_memo_date=date(2026, 4, 21),
        entry_date=date(2021, 6, 1),
        entry_equity_eur_m=20.0,
        entry_ev_eur_m=60.0,
        entry_ebitda_eur_m=4.0,
        entry_multiple=15.0,
        expected_exit_date=date(2026, 10, 1),
        expected_exit_ev_eur_m=110.0,
        expected_exit_ebitda_eur_m=7.0,
        expected_exit_multiple=15.7,
        ebitda_growth_contribution_eur_m=30.0,
        multiple_expansion_contribution_eur_m=12.0,
        debt_paydown_contribution_eur_m=8.0,
        actual_irr_pct=0.18,
        target_irr_pct=0.15,
        actual_moic=2.3,
        target_moic=2.0,
        actual_hold_years=5.3,
        target_hold_years=5.0,
        exit_headline="Recommend proceed to exit — market + returns favorable",
        exit_thesis=(
            "Asset has achieved stabilized NOI and lease-up is complete. "
            "Current PBSA transaction multiples are 10% above underwrite."
        ),
        market_commentary=(
            "Italian PBSA M&A activity robust — 3 comparable transactions "
            "closed in last 6 months at 4.5-4.8% cap rate."
        ),
        buyer_candidates=[
            BuyerCandidate(
                name="Global PBSA Operator Alpha",
                buyer_type="strategic",
                country="UK",
                fit_notes="Roll-up play — bolt-on to Italian portfolio",
                indicated_range_eur_m="€105-115M",
            ),
            BuyerCandidate(
                name="European Infra Sponsor Beta",
                buyer_type="financial",
                country="FR",
                fit_notes="Long-hold core-plus strategy",
                indicated_range_eur_m="€100-108M",
            ),
        ],
        milestones=[
            ExitMilestone(label="Advisor appointment", date=date(2026, 5, 1)),
            ExitMilestone(label="Marketing launch", date=date(2026, 6, 15)),
            ExitMilestone(label="IOIs due", date=date(2026, 7, 15)),
            ExitMilestone(label="Binding bids", date=date(2026, 9, 1)),
            ExitMilestone(label="Signing", date=date(2026, 10, 1)),
        ],
        recommendation="proceed",
        recommendation_rationale=(
            "Strong returns, supportive market, clear buyer interest."
        ),
    )


def test_compose_produces_8_slides():
    pres = compose_exit_memo(_sample_exit())
    assert len(pres.slides) == 8


def test_compose_uses_finance_pro_theme():
    pres = compose_exit_memo(_sample_exit())
    assert pres.theme == "finance-pro"


def test_compose_sets_ic_metadata():
    pres = compose_exit_memo(_sample_exit())
    assert pres.metadata.purpose == Purpose.IC_PRESENTATION
    assert pres.metadata.audience == Audience.BOARD
    assert pres.metadata.confidentiality == Confidentiality.CONFIDENTIAL
    assert "Exit Memo" in pres.metadata.title


def test_compose_slide_spine_is_stable():
    pres = compose_exit_memo(_sample_exit())
    expected = [
        "title_slide",
        "key_message",
        "waterfall_chart",
        "stats_callout",
        "key_message",
        "table_slide",
        "timeline",
        "key_message",
    ]
    assert [s.slide_type for s in pres.slides] == expected


def test_value_creation_bridge_has_6_categories():
    pres = compose_exit_memo(_sample_exit())
    bridge = pres.slides[2]
    chart_el = bridge.elements[1]
    assert chart_el.type == "chart"
    assert chart_el.chart_data.chart_type == "waterfall"
    assert chart_el.chart_data.categories == [
        "Entry EV",
        "EBITDA Growth",
        "Multiple Expansion",
        "Debt Paydown",
        "Other",
        "Exit EV",
    ]


def test_value_creation_bridge_endpoints_match_entry_and_exit():
    pres = compose_exit_memo(_sample_exit())
    bridge = pres.slides[2]
    chart = bridge.elements[1].chart_data
    assert chart.values[0] == 60.0
    assert chart.values[-1] == 110.0


def test_returns_slide_compares_actual_vs_target():
    pres = compose_exit_memo(_sample_exit())
    returns = pres.slides[3]
    metric_el = returns.elements[1]
    labels = [m.label for m in metric_el.content.metrics]
    values = [m.value for m in metric_el.content.metrics]
    assert "Actual IRR" in labels
    assert "Actual MOIC" in labels
    assert "Hold Period" in labels
    irr_value = next(v for lbl, v in zip(labels, values) if lbl == "Actual IRR")
    assert "target" in irr_value.lower()


def test_returns_slide_drops_comparisons_when_targets_missing():
    facts = _sample_exit()
    facts.target_irr_pct = None
    facts.target_moic = None
    facts.target_hold_years = None
    pres = compose_exit_memo(facts)
    returns = pres.slides[3]
    values = [m.value for m in returns.elements[1].content.metrics]
    for value in values:
        assert "target" not in value.lower()


def test_buyer_landscape_table_has_5_columns():
    pres = compose_exit_memo(_sample_exit())
    buyers = pres.slides[5]
    table_el = buyers.elements[1]
    assert table_el.type == "table"
    assert table_el.content.headers == [
        "Buyer", "Type", "Country", "Indicated Range", "Fit Notes"
    ]
    assert len(table_el.content.rows) == 2
    # Type column upper-cased
    first_row_type = table_el.content.rows[0][1]
    assert first_row_type == "STRATEGIC"


def test_buyer_landscape_falls_back_when_empty():
    facts = _sample_exit()
    facts.buyer_candidates = []
    pres = compose_exit_memo(facts)
    buyers = pres.slides[5]
    kinds = [el.type for el in buyers.elements]
    assert "table" not in kinds


def test_timeline_milestones_appear_with_dates():
    pres = compose_exit_memo(_sample_exit())
    timeline = pres.slides[6]
    bullets = timeline.elements[1].content.items
    joined = "\n".join(bullets)
    assert "2026-09-01" in joined
    assert "Binding bids" in joined


def test_recommendation_proceed_label():
    pres = compose_exit_memo(_sample_exit())
    rec = pres.slides[-1]
    heading = rec.elements[0]
    assert "PROCEED" in heading.content.text


def test_recommendation_delay_label():
    facts = _sample_exit()
    facts.recommendation = "delay"
    pres = compose_exit_memo(facts)
    heading = pres.slides[-1].elements[0]
    assert "DELAY" in heading.content.text


def test_vertical_agnostic():
    for vertical in ["pe", "re", "infrastructure", "credit", "npl", "vc", "m_and_a"]:
        facts = _sample_exit()
        facts.vertical = vertical  # type: ignore[assignment]
        pres = compose_exit_memo(facts)
        assert len(pres.slides) == 8
