"""Tests for the IC memo deck composer."""
from __future__ import annotations

from datetime import date

import pytest

from deckforge.compose.ic_memo import (
    ComparableTransaction,
    DealFacts,
    compose_ic_memo,
)
from deckforge.ir.enums import Audience, Confidentiality, Purpose


def _sample_deal() -> DealFacts:
    return DealFacts(
        deal_name="Via Pirelli 4 Milano — PBSA Acquisition",
        sector="Real Estate — PBSA",
        vertical="re",
        country="IT",
        deal_date=date(2026, 4, 21),
        author="Deal Team",
        company="Aither",
        total_size_eur_m=45.0,
        equity_required_eur_m=20.25,
        debt_eur_m=24.75,
        hold_period_years=7,
        investment_thesis_bullets=[
            "Strong university demand in Milano Bicocca submarket.",
            "State co-financing (L.338) covers 50% of eligible CapEx.",
            "Exit cap at 4.5% aligns with 2025-26 Italian PBSA comps.",
        ],
        target_irr_pct=0.15,
        target_moic=2.1,
        yield_on_cost_pct=0.065,
        levered_irr_pct=0.18,
        comparable_transactions=[
            ComparableTransaction(
                target="Torino Politecnico",
                year=2025,
                size_eur_m=38.0,
                multiple=4.8,
                notes="PBSA 450 beds",
            ),
            ComparableTransaction(
                target="Milano Bovisa",
                year=2024,
                size_eur_m=52.0,
                multiple=4.5,
                notes="PBSA 620 beds",
            ),
        ],
        risks=[
            "Planning permit timing slippage.",
            "Construction cost inflation over 18-month build.",
        ],
        mitigants=[
            "Pre-application dialogue concluded.",
            "Fixed-price GMP contract.",
        ],
        recommendation="approve",
        recommendation_rationale=(
            "Strong demand + grant funding + experienced operator. "
            "Priced in comp range."
        ),
        ask_eur_m=20.25,
    )


def test_compose_produces_12_slides():
    pres = compose_ic_memo(_sample_deal())
    assert len(pres.slides) == 12


def test_compose_uses_finance_pro_theme():
    pres = compose_ic_memo(_sample_deal())
    assert pres.theme == "finance-pro"


def test_compose_sets_ic_metadata():
    pres = compose_ic_memo(_sample_deal())
    assert pres.metadata.purpose == Purpose.IC_PRESENTATION
    assert pres.metadata.audience == Audience.BOARD
    assert pres.metadata.confidentiality == Confidentiality.CONFIDENTIAL
    assert "IC Memo" in pres.metadata.title


def test_compose_slide_spine_is_stable():
    """The IC memo spine is a contract — downstream renderers + PMs assume it."""
    pres = compose_ic_memo(_sample_deal())
    expected_types = [
        "title_slide",
        "key_message",
        "deal_overview",
        "investment_thesis",
        "stats_callout",
        "waterfall_chart",
        "capital_structure",
        "comp_table",
        "table_slide",  # sensitivity fallback (no grid provided)
        "risk_matrix",
        "two_column_text",
        "key_message",
    ]
    actual = [s.slide_type for s in pres.slides]
    assert actual == expected_types


def test_returns_callout_carries_kpis():
    pres = compose_ic_memo(_sample_deal())
    returns_slide = pres.slides[4]  # stats_callout
    assert returns_slide.slide_type == "stats_callout"
    # 2 elements: heading + metric group
    assert len(returns_slide.elements) == 2
    metric_el = returns_slide.elements[1]
    assert metric_el.type == "metric_group"
    kpi_labels = [m.label for m in metric_el.content.metrics]
    # Must have target IRR + MOIC. Levered IRR + Yield on Cost are conditional.
    assert "Target IRR" in kpi_labels
    assert "Target MOIC" in kpi_labels
    assert "Levered IRR" in kpi_labels  # we set this in the sample
    assert "Yield on Cost" in kpi_labels  # we set this in the sample


def test_waterfall_slide_emits_waterfall_chart():
    pres = compose_ic_memo(_sample_deal())
    waterfall = pres.slides[5]
    chart_el = waterfall.elements[1]
    assert chart_el.type == "chart"
    assert chart_el.chart_data.chart_type == "waterfall"
    assert len(chart_el.chart_data.categories) == len(chart_el.chart_data.values)


def test_capital_structure_emits_stacked_bar():
    pres = compose_ic_memo(_sample_deal())
    cap = pres.slides[6]
    chart_el = cap.elements[1]
    assert chart_el.type == "chart"
    assert chart_el.chart_data.chart_type == "stacked_bar"


def test_comps_table_has_5_columns():
    pres = compose_ic_memo(_sample_deal())
    comps = pres.slides[7]
    table_el = comps.elements[1]
    assert table_el.type == "table"
    assert table_el.content.headers == [
        "Target", "Year", "Size (€M)", "Multiple", "Notes"
    ]
    assert len(table_el.content.rows) == 2  # 2 comps in the sample


def test_sensitivity_falls_back_when_empty():
    """Without sensitivity data, slide falls back to table_slide with a nudge."""
    pres = compose_ic_memo(_sample_deal())
    sens = pres.slides[8]
    assert sens.slide_type == "table_slide"


def test_sensitivity_renders_heatmap_when_provided():
    deal = _sample_deal()
    deal.sensitivity_row_labels = ["4.0x", "4.5x", "5.0x"]
    deal.sensitivity_col_labels = ["2%", "3%", "4%"]
    deal.sensitivity_values = [
        [0.12, 0.14, 0.16],
        [0.14, 0.16, 0.18],
        [0.16, 0.18, 0.20],
    ]
    pres = compose_ic_memo(deal)
    sens = pres.slides[8]
    assert sens.slide_type == "chart_slide"
    chart_el = sens.elements[1]
    assert chart_el.chart_data.chart_type == "heatmap"


def test_recommendation_approve_renders_bold_label():
    pres = compose_ic_memo(_sample_deal())
    rec = pres.slides[-1]
    heading = rec.elements[0]
    assert heading.type == "heading"
    assert "APPROVE" in heading.content.text


def test_recommendation_reject_surfaces_reject_label():
    deal = _sample_deal()
    deal.recommendation = "reject"
    pres = compose_ic_memo(deal)
    heading = pres.slides[-1].elements[0]
    assert "REJECT" in heading.content.text


def test_vertical_agnostic():
    """Same composer works for NPL, PE, infrastructure — no exceptions."""
    for vertical in ["pe", "re", "infrastructure", "credit", "npl", "vc", "m_and_a"]:
        deal = _sample_deal()
        deal.vertical = vertical  # type: ignore[assignment]
        pres = compose_ic_memo(deal)
        assert len(pres.slides) == 12
