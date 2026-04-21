"""Tests for the LP quarterly report composer."""
from __future__ import annotations

from datetime import date

from deckforge.compose.lp_quarterly import (
    LPQuarterlyFacts,
    PortfolioHolding,
    PortfolioMover,
    compose_lp_quarterly,
)
from deckforge.ir.enums import Audience, Confidentiality, Purpose


def _sample_report() -> LPQuarterlyFacts:
    return LPQuarterlyFacts(
        fund_name="Aither PERE Italia I",
        vintage_year=2023,
        reporting_quarter="Q1",
        reporting_year=2026,
        report_date=date(2026, 4, 30),
        fund_size_eur_m=250.0,
        called_capital_eur_m=180.0,
        distributed_capital_eur_m=22.0,
        nav_eur_m=210.0,
        net_irr_pct=0.14,
        gross_irr_pct=0.19,
        tvpi=1.29,
        dpi=0.12,
        rvpi=1.17,
        headline=(
            "Fund NAV +6% QoQ driven by PBSA lease-up at Project Bicocca."
        ),
        quarter_defining_event=(
            "Partial exit on Project Navigli — €22M distribution, 2.3x MOIC."
        ),
        holdings=[
            PortfolioHolding(
                company="Project Bicocca",
                sector="PBSA",
                invested_eur_m=40.0,
                current_fmv_eur_m=52.0,
                moic=1.30,
                pct_of_fund_nav=0.24,
            ),
            PortfolioHolding(
                company="Project Tortona",
                sector="Office-to-Resi",
                invested_eur_m=25.0,
                current_fmv_eur_m=28.0,
                moic=1.12,
                pct_of_fund_nav=0.13,
            ),
        ],
        top_movers=[
            PortfolioMover(
                company="Project Bicocca",
                change_eur_m=4.5,
                commentary="Lease-up ahead of schedule at +5% vs underwrite",
            ),
            PortfolioMover(
                company="Project Palermo",
                change_eur_m=-1.2,
                commentary="Permit delay — 3-month slippage, cost contingency holds",
            ),
        ],
        capital_calls_eur_m=12.0,
        distributions_this_quarter_eur_m=22.0,
        market_commentary=(
            "Italian PBSA market remains supply-constrained. "
            "Investor appetite for value-add strategies strengthening."
        ),
        esg_highlights=["First green bond issuance at Project Bicocca"],
        operational_highlights=["All covenants in compliance"],
        outlook_headline="Focus on value creation + selective deployment",
    )


def test_compose_produces_9_slides():
    pres = compose_lp_quarterly(_sample_report())
    assert len(pres.slides) == 9


def test_compose_uses_finance_pro_theme():
    pres = compose_lp_quarterly(_sample_report())
    assert pres.theme == "finance-pro"


def test_compose_sets_quarterly_review_metadata():
    pres = compose_lp_quarterly(_sample_report())
    assert pres.metadata.purpose == Purpose.QUARTERLY_REVIEW
    assert pres.metadata.audience == Audience.INVESTORS
    assert pres.metadata.confidentiality == Confidentiality.CONFIDENTIAL
    assert "Q1 2026" in pres.metadata.title
    assert "LP Report" in pres.metadata.title


def test_compose_slide_spine_is_stable():
    pres = compose_lp_quarterly(_sample_report())
    expected = [
        "title_slide",
        "key_message",
        "stats_callout",
        "table_slide",
        "bullet_points",
        "waterfall_chart",
        "key_message",
        "bullet_points",
        "key_message",
    ]
    assert [s.slide_type for s in pres.slides] == expected


def test_fund_performance_kpis_carry_core_metrics():
    pres = compose_lp_quarterly(_sample_report())
    perf = pres.slides[2]
    metric_el = perf.elements[1]
    labels = [m.label for m in metric_el.content.metrics]
    # Core 4 always present
    assert "Fund Size" in labels
    assert "Called" in labels
    assert "Distributed" in labels
    assert "NAV" in labels
    # Returns metrics conditional
    assert "Net IRR" in labels
    assert "TVPI" in labels
    assert "DPI" in labels
    assert "RVPI" in labels


def test_fund_performance_kpis_skip_absent_returns():
    facts = _sample_report()
    facts.net_irr_pct = None
    facts.tvpi = None
    facts.dpi = None
    facts.rvpi = None
    pres = compose_lp_quarterly(facts)
    perf = pres.slides[2]
    labels = [m.label for m in perf.elements[1].content.metrics]
    assert "Net IRR" not in labels
    assert "TVPI" not in labels


def test_portfolio_table_has_6_columns():
    pres = compose_lp_quarterly(_sample_report())
    portfolio = pres.slides[3]
    table_el = portfolio.elements[1]
    assert table_el.type == "table"
    assert table_el.content.headers == [
        "Company", "Sector", "Invested (€M)", "FMV (€M)", "MOIC", "% NAV"
    ]
    assert len(table_el.content.rows) == 2


def test_portfolio_table_falls_back_when_empty():
    facts = _sample_report()
    facts.holdings = []
    pres = compose_lp_quarterly(facts)
    portfolio = pres.slides[3]
    assert portfolio.slide_type == "table_slide"
    # No table element — just heading + body text placeholder
    kinds = [el.type for el in portfolio.elements]
    assert "table" not in kinds
    assert "body_text" in kinds


def test_top_movers_surface_with_change_and_commentary():
    pres = compose_lp_quarterly(_sample_report())
    movers = pres.slides[4]
    bullet_el = movers.elements[1]
    joined = "\n".join(bullet_el.content.items)
    assert "Project Bicocca" in joined
    assert "+4.5" in joined or "+4.5 €M" in joined
    assert "-1.2" in joined
    assert "Permit delay" in joined


def test_capital_activity_uses_waterfall_chart():
    pres = compose_lp_quarterly(_sample_report())
    cap = pres.slides[5]
    chart_el = cap.elements[1]
    assert chart_el.type == "chart"
    assert chart_el.chart_data.chart_type == "waterfall"
    # Default 5-step spine: Opening → Calls → Distributions → Net Change → Closing
    assert len(chart_el.chart_data.categories) == 5


def test_outlook_slide_is_closing_message():
    pres = compose_lp_quarterly(_sample_report())
    outlook = pres.slides[-1]
    assert outlook.slide_type == "key_message"
    heading = outlook.elements[0]
    assert "Outlook" in heading.content.text
