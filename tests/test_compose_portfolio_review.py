"""Tests for the internal portfolio review composer."""
from __future__ import annotations

from datetime import date

from deckforge.compose.portfolio_review import (
    ExitRecord,
    IcAsk,
    PortfolioCompany,
    PortfolioReviewFacts,
    TopPerformer,
    ValueCreationAction,
    WatchlistItem,
    compose_portfolio_review,
)
from deckforge.ir.enums import Audience, Confidentiality, Purpose


def _sample_review() -> PortfolioReviewFacts:
    return PortfolioReviewFacts(
        fund_name="Aither PERE Italia I",
        vintage_year=2023,
        reporting_quarter="Q1",
        reporting_year=2026,
        review_date=date(2026, 4, 30),
        author="GP Deal Team",
        company="Aither",
        holdings=[
            PortfolioCompany(
                company="Project Bicocca",
                sector="PBSA",
                invested_eur_m=40.0,
                current_fmv_eur_m=52.0,
                moic=1.30,
                status="outperforming",
                notes="Lease-up ahead of plan",
            ),
            PortfolioCompany(
                company="Project Tortona",
                sector="Office-to-Resi",
                invested_eur_m=25.0,
                current_fmv_eur_m=23.0,
                moic=0.92,
                status="watchlist",
                notes="Permit slippage",
            ),
        ],
        top_performers=[
            TopPerformer(
                company="Project Bicocca",
                value_change_eur_m=4.5,
                driver="Lease-up +5% vs underwrite",
            ),
        ],
        watchlist=[
            WatchlistItem(
                company="Project Tortona",
                issue="3-month permit delay",
                severity="medium",
            ),
        ],
        value_creation_actions=[
            ValueCreationAction(
                company="Project Bicocca",
                action="Negotiate 5-year fixed lease with anchor tenant",
                owner="Asset Mgmt — MR",
                target_date=date(2026, 6, 30),
            ),
            ValueCreationAction(
                company="Project Tortona",
                action="Engage external planning consultant",
                owner="Deal Captain — LF",
                target_date=date(2026, 5, 15),
            ),
        ],
        fund_size_eur_m=250.0,
        invested_capital_eur_m=180.0,
        reserved_capital_eur_m=20.0,
        available_dry_powder_eur_m=50.0,
        portfolio_nav_eur_m=210.0,
        weighted_avg_moic=1.18,
        gross_irr_pct=0.19,
        net_irr_pct=0.14,
        realized_eur_m=22.0,
        unrealized_eur_m=188.0,
        exits=[
            ExitRecord(
                company="Project Navigli",
                status="closed",
                proceeds_eur_m=46.0,
                moic=2.30,
                notes="Sold to strategic operator",
            ),
            ExitRecord(
                company="Project Lambrate",
                status="in_process",
                notes="IOIs received, binding bids July",
            ),
        ],
        market_view="Italian PBSA supply-constrained — selective buy and hold",
        sector_commentary="Office-to-resi conversions watch construction cost inflation",
        portfolio_risks=[
            "Construction cost inflation across 3 active developments.",
            "Permit timing risk in Lombardia conversions.",
        ],
        ic_asks=[
            IcAsk(
                label="Approve €5M follow-on for Project Bicocca",
                detail="Fund minority recap of remaining sponsor equity",
            ),
            IcAsk(
                label="Sign off on Project Tortona action plan",
            ),
        ],
    )


def test_compose_produces_11_slides():
    pres = compose_portfolio_review(_sample_review())
    assert len(pres.slides) == 11


def test_compose_uses_finance_pro_theme():
    pres = compose_portfolio_review(_sample_review())
    assert pres.theme == "finance-pro"


def test_compose_sets_internal_review_metadata():
    pres = compose_portfolio_review(_sample_review())
    assert pres.metadata.purpose == Purpose.QUARTERLY_REVIEW
    assert pres.metadata.audience == Audience.BOARD
    # Internal-facing — not LP-facing
    assert pres.metadata.confidentiality == Confidentiality.INTERNAL
    assert "Portfolio Review" in pres.metadata.title
    assert "Q1 2026" in pres.metadata.title


def test_compose_slide_spine_is_stable():
    pres = compose_portfolio_review(_sample_review())
    expected = [
        "title_slide",
        "table_slide",  # portfolio overview
        "bullet_points",  # top performers
        "bullet_points",  # watchlist
        "table_slide",  # value-creation actions
        "chart_slide",  # capital deployment
        "stats_callout",  # portfolio metrics
        "table_slide",  # exits
        "key_message",  # market view
        "bullet_points",  # risks
        "key_message",  # asks
    ]
    assert [s.slide_type for s in pres.slides] == expected


def test_portfolio_overview_has_6_columns_with_status():
    pres = compose_portfolio_review(_sample_review())
    overview = pres.slides[1]
    table_el = overview.elements[1]
    assert table_el.type == "table"
    assert table_el.content.headers == [
        "Company", "Sector", "Invested (€M)", "FMV (€M)", "MOIC", "Status"
    ]
    assert len(table_el.content.rows) == 2
    # Status column upper-cased
    statuses = [row[5] for row in table_el.content.rows]
    assert "OUTPERFORMING" in statuses
    assert "WATCHLIST" in statuses


def test_top_performers_carry_change_and_driver():
    pres = compose_portfolio_review(_sample_review())
    top = pres.slides[2]
    bullet_el = top.elements[1]
    joined = "\n".join(bullet_el.content.items)
    assert "Project Bicocca" in joined
    assert "+4.5" in joined
    assert "Lease-up" in joined


def test_watchlist_surfaces_severity_tag():
    pres = compose_portfolio_review(_sample_review())
    wl = pres.slides[3]
    bullet_el = wl.elements[1]
    joined = "\n".join(bullet_el.content.items)
    assert "MEDIUM" in joined
    assert "Project Tortona" in joined


def test_value_creation_table_has_4_columns():
    pres = compose_portfolio_review(_sample_review())
    vc = pres.slides[4]
    table_el = vc.elements[1]
    assert table_el.type == "table"
    assert table_el.content.headers == ["Company", "Action", "Owner", "Target Date"]
    assert len(table_el.content.rows) == 2


def test_capital_deployment_emits_bar_chart():
    pres = compose_portfolio_review(_sample_review())
    cap = pres.slides[5]
    chart_el = cap.elements[1]
    assert chart_el.type == "chart"
    assert chart_el.chart_data.chart_type == "bar"
    assert chart_el.chart_data.categories == ["Invested", "Reserved", "Dry Powder"]


def test_portfolio_metrics_carry_core_kpis():
    pres = compose_portfolio_review(_sample_review())
    metrics = pres.slides[6]
    metric_el = metrics.elements[1]
    labels = [m.label for m in metric_el.content.metrics]
    assert "Portfolio NAV" in labels
    assert "Realized" in labels
    assert "Unrealized" in labels
    assert "Wtd Avg MOIC" in labels
    assert "Gross IRR" in labels
    assert "Net IRR" in labels


def test_exits_table_drops_empty_state_when_data_present():
    pres = compose_portfolio_review(_sample_review())
    exits = pres.slides[7]
    table_el = exits.elements[1]
    assert table_el.type == "table"
    assert table_el.content.headers == [
        "Buyer", "Status", "Proceeds (€M)", "MOIC", "Notes"
    ] or table_el.content.headers == [
        "Company", "Status", "Proceeds (€M)", "MOIC", "Notes"
    ]
    assert len(table_el.content.rows) == 2


def test_holdings_table_falls_back_when_empty():
    facts = _sample_review()
    facts.holdings = []
    pres = compose_portfolio_review(facts)
    overview = pres.slides[1]
    kinds = [el.type for el in overview.elements]
    assert "table" not in kinds
    assert "body_text" in kinds


def test_asks_slide_lists_decision_requests():
    pres = compose_portfolio_review(_sample_review())
    asks = pres.slides[-1]
    bullet_el = asks.elements[1]
    joined = "\n".join(bullet_el.content.items)
    assert "Project Bicocca" in joined
    assert "follow-on" in joined.lower()


def test_asks_slide_falls_back_when_empty():
    facts = _sample_review()
    facts.ic_asks = []
    pres = compose_portfolio_review(facts)
    asks = pres.slides[-1]
    bullet_el = asks.elements[1]
    joined = "\n".join(bullet_el.content.items)
    assert "informational" in joined.lower()
