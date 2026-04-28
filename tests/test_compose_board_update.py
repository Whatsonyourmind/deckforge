"""Tests for the portfolio-company board update composer."""
from __future__ import annotations

from datetime import date

from deckforge.compose.board_update import (
    BoardAsk,
    BoardUpdateFacts,
    FinancialRow,
    KpiScorecardEntry,
    compose_board_update,
)
from deckforge.ir.enums import Audience, Confidentiality, Purpose


def _sample_update() -> BoardUpdateFacts:
    return BoardUpdateFacts(
        company_name="Lumen AI",
        period_label="Q1 2026",
        period_end_date=date(2026, 3, 31),
        cadence="quarterly",
        author="CEO",
        company="Lumen AI S.r.l.",
        headline="Strong Q1 — ARR +130% QoQ, hit $300k milestone.",
        period_highlights=[
            "Closed seed round of $4M led by Acme Ventures.",
            "Shipped GA of evals product with 40 paying customers.",
            "Hired VP Engineering and 3 senior engineers.",
        ],
        kpi_entries=[
            KpiScorecardEntry(
                label="ARR", value="$300k", target="$280k", trend="up"
            ),
            KpiScorecardEntry(
                label="Net New Logos", value="18", target="15", trend="up"
            ),
            KpiScorecardEntry(
                label="NRR", value="135%", target="120%", trend="up"
            ),
            KpiScorecardEntry(
                label="Churn", value="0.5%", target="<2%", trend="flat"
            ),
        ],
        financial_rows=[
            FinancialRow(metric="Revenue", actual=85.0, plan=75.0, prior_period=42.0),
            FinancialRow(
                metric="Gross Margin", actual=72.0, plan=70.0, prior_period=68.0,
                unit="%",
            ),
            FinancialRow(
                metric="EBITDA", actual=-180.0, plan=-220.0, prior_period=-210.0,
            ),
        ],
        cash_balance_eur_k=3800.0,
        runway_months=18.0,
        burn_rate_eur_k_per_month=210.0,
        headcount_total=22,
        headcount_change_period=4,
        key_hires=[
            "Marco Esposito — VP Engineering (ex-Datadog)",
            "Anna Conte — Head of Sales (ex-MongoDB)",
        ],
        org_notes=[
            "All-hands offsite scheduled for May.",
        ],
        product_updates=[
            "Evals product GA — 40 paying customers in 60 days.",
            "TypeScript SDK 2.0 with streaming support.",
        ],
        gtm_updates=[
            "Sales team scaled from 1 to 3 AEs.",
            "First strategic partnership signed (Anthropic).",
        ],
        risks=[
            "AWS GPU constraints could limit rollout speed in Q2.",
            "VP Sales hire still open — top of priority list.",
        ],
        board_asks=[
            BoardAsk(
                label="Approve Q2 hiring plan (8 new roles)",
                detail="Total compensation budget €1.2M",
                decision_required_by=date(2026, 4, 30),
            ),
            BoardAsk(label="Endorse partnership with Anthropic"),
        ],
        appendix_link="https://drive.example/lumen-q1-2026-detail",
        next_meeting_date=date(2026, 7, 15),
    )


def test_compose_produces_9_slides():
    pres = compose_board_update(_sample_update())
    assert len(pres.slides) == 9


def test_compose_uses_finance_pro_theme():
    pres = compose_board_update(_sample_update())
    assert pres.theme == "finance-pro"


def test_compose_sets_board_meeting_metadata():
    pres = compose_board_update(_sample_update())
    assert pres.metadata.purpose == Purpose.BOARD_MEETING
    assert pres.metadata.audience == Audience.BOARD
    assert pres.metadata.confidentiality == Confidentiality.CONFIDENTIAL
    assert "Lumen AI" in pres.metadata.title
    assert "Q1 2026" in pres.metadata.title
    assert "Board Update" in pres.metadata.title


def test_compose_slide_spine_is_stable():
    pres = compose_board_update(_sample_update())
    expected = [
        "title_slide",
        "key_message",  # period highlights
        "stats_callout",  # KPI scorecard
        "table_slide",  # financials
        "bullet_points",  # hiring & org
        "bullet_points",  # product & GTM
        "bullet_points",  # risks
        "key_message",  # board asks
        "appendix",
    ]
    assert [s.slide_type for s in pres.slides] == expected


def test_title_slide_carries_cadence_label():
    pres = compose_board_update(_sample_update())
    title = pres.slides[0]
    sub = title.elements[1]
    assert "Quarterly Board Update" in sub.content.text
    assert "Q1 2026" in sub.content.text


def test_kpi_scorecard_carries_trend_arrows():
    pres = compose_board_update(_sample_update())
    scorecard = pres.slides[2]
    metric_el = scorecard.elements[1]
    assert metric_el.type == "metric_group"
    labels = [m.label for m in metric_el.content.metrics]
    values = [m.value for m in metric_el.content.metrics]
    assert "ARR" in labels
    assert "NRR" in labels
    # Trend arrows appear in the value strings
    arr_value = next(v for lbl, v in zip(labels, values) if lbl == "ARR")
    assert "▲" in arr_value or "up" in arr_value.lower()


def test_kpi_scorecard_includes_targets_when_provided():
    pres = compose_board_update(_sample_update())
    scorecard = pres.slides[2]
    values = [m.value for m in scorecard.elements[1].content.metrics]
    joined = " ".join(values)
    assert "target" in joined.lower()


def test_financials_table_has_5_columns():
    pres = compose_board_update(_sample_update())
    fin = pres.slides[3]
    table_el = fin.elements[1]
    assert table_el.type == "table"
    assert table_el.content.headers == [
        "Metric", "Actual", "Plan", "Prior", "vs Plan"
    ]
    assert len(table_el.content.rows) == 3


def test_financials_includes_cash_runway_burn_summary():
    pres = compose_board_update(_sample_update())
    fin = pres.slides[3]
    # Last element is the cash/runway summary body text
    body = fin.elements[-1]
    assert body.type == "body_text"
    assert "Cash" in body.content.text
    assert "Runway" in body.content.text


def test_hiring_org_includes_headcount_and_key_hires():
    pres = compose_board_update(_sample_update())
    org = pres.slides[4]
    bullet_el = org.elements[1]
    joined = "\n".join(bullet_el.content.items)
    assert "22" in joined
    assert "+4" in joined
    assert "Marco Esposito" in joined


def test_product_gtm_prefixes_each_update():
    pres = compose_board_update(_sample_update())
    pgtm = pres.slides[5]
    items = pgtm.elements[1].content.items
    joined = "\n".join(items)
    assert "Product:" in joined
    assert "GTM:" in joined


def test_board_asks_surface_decision_dates_when_provided():
    pres = compose_board_update(_sample_update())
    asks = pres.slides[7]
    bullet_el = asks.elements[1]
    joined = "\n".join(bullet_el.content.items)
    assert "hiring plan" in joined.lower()
    assert "2026-04-30" in joined


def test_appendix_includes_link_and_next_meeting():
    pres = compose_board_update(_sample_update())
    appendix = pres.slides[-1]
    body = appendix.elements[1]
    assert "drive.example/lumen" in body.content.text
    assert "2026-07-15" in body.content.text


def test_kpi_scorecard_falls_back_when_empty():
    facts = _sample_update()
    facts.kpi_entries = []
    pres = compose_board_update(facts)
    scorecard = pres.slides[2]
    metric_el = scorecard.elements[1]
    labels = [m.label for m in metric_el.content.metrics]
    assert len(labels) >= 1


def test_cadence_agnostic():
    for cadence in ["monthly", "quarterly", "annual"]:
        facts = _sample_update()
        facts.cadence = cadence  # type: ignore[assignment]
        pres = compose_board_update(facts)
        assert len(pres.slides) == 9
