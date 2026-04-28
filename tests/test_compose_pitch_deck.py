"""Tests for the startup pitch deck composer."""
from __future__ import annotations

from datetime import date

from deckforge.compose.pitch_deck import (
    CompetitorRow,
    PitchDeckFacts,
    TeamMember,
    compose_pitch_deck,
)
from deckforge.ir.enums import Audience, Confidentiality, Purpose


def _sample_pitch() -> PitchDeckFacts:
    return PitchDeckFacts(
        company_name="Lumen AI",
        tagline="The fastest way to ship LLM features",
        sector="B2B SaaS — DevTools",
        stage="seed",
        country="IT",
        pitch_date=date(2026, 5, 15),
        author="Founders",
        company="Lumen AI S.r.l.",
        problem_headline="Engineering teams spend 6+ weeks on every LLM feature.",
        problem_detail=(
            "Plumbing, evals, observability, and rollout safety are reinvented "
            "by every team — slow, expensive, and risky."
        ),
        solution_headline="Lumen AI ships LLM features in days, not months.",
        solution_detail=(
            "All-in-one SDK + dashboard for prompts, evals, traces, and rollouts. "
            "Self-serve and developer-first."
        ),
        tam_eur_m=18000.0,
        sam_eur_m=2400.0,
        som_eur_m=180.0,
        market_commentary=(
            "European AI infrastructure spend growing 60% YoY through 2028."
        ),
        product_highlights=[
            "TypeScript + Python SDK with 5-line install.",
            "150+ evals out of the box across safety/quality/cost dimensions.",
            "Native MCP server for AI agents.",
        ],
        traction_metric_label="ARR (EUR k)",
        traction_periods=["Jul-25", "Oct-25", "Jan-26", "Apr-26"],
        traction_values=[12.0, 38.0, 110.0, 280.0],
        business_model_bullets=[
            "Usage-based SaaS, billed monthly.",
            "Net revenue retention 135% via expansion seats.",
            "12-month CAC payback at current ACV.",
        ],
        gtm_bullets=[
            "Inbound via OSS + content in dev community.",
            "Outbound to AI-forward eng teams.",
            "Strategic partnership with Anthropic / OpenAI partner ecosystems.",
        ],
        competitors=[
            CompetitorRow(
                name="Langfuse",
                positioning="OSS observability, self-host first",
                differentiator="We add evals + safe rollouts in same product.",
            ),
            CompetitorRow(
                name="Helicone",
                positioning="Proxy-based logging",
                differentiator="We are SDK-native — works without proxy rewiring.",
            ),
        ],
        team_members=[
            TeamMember(
                name="Luca Rossi",
                role="Co-founder/CEO",
                background="ex-Anthropic GTM, 8 yrs ML",
            ),
            TeamMember(
                name="Sara Bianchi",
                role="Co-founder/CTO",
                background="ex-Stripe, 12 yrs eng infra",
            ),
        ],
        financial_periods=["2026", "2027", "2028"],
        financial_revenue_eur_k=[1200.0, 5400.0, 18000.0],
        financial_ebitda_eur_k=[-1500.0, -800.0, 2400.0],
        ask_eur_m=4.0,
        pre_money_eur_m=20.0,
        use_of_funds=[
            "60% Engineering — ship enterprise features.",
            "30% GTM — first 3 AE hires.",
            "10% Working capital + reserves.",
        ],
        contact_name="Luca Rossi",
        contact_role="Co-founder/CEO",
        contact_email="luca@lumen.example",
    )


def test_compose_produces_13_slides():
    pres = compose_pitch_deck(_sample_pitch())
    assert len(pres.slides) == 13


def test_compose_uses_finance_pro_theme():
    pres = compose_pitch_deck(_sample_pitch())
    assert pres.theme == "finance-pro"


def test_compose_sets_pitch_metadata():
    pres = compose_pitch_deck(_sample_pitch())
    assert pres.metadata.purpose == Purpose.SALES_PITCH
    assert pres.metadata.audience == Audience.INVESTORS
    assert pres.metadata.confidentiality == Confidentiality.CONFIDENTIAL
    assert "Pitch Deck" in pres.metadata.title


def test_compose_slide_spine_is_stable():
    """The pitch deck spine is a contract — downstream renderers + PMs assume it."""
    pres = compose_pitch_deck(_sample_pitch())
    expected = [
        "title_slide",
        "key_message",  # problem
        "key_message",  # solution
        "stats_callout",  # market size
        "bullet_points",  # product
        "chart_slide",  # traction
        "bullet_points",  # business model
        "bullet_points",  # gtm
        "comparison",  # competition
        "team_slide",
        "chart_slide",  # financials
        "key_message",  # ask
        "key_message",  # contact
    ]
    actual = [s.slide_type for s in pres.slides]
    assert actual == expected


def test_market_size_carries_tam_sam_som():
    pres = compose_pitch_deck(_sample_pitch())
    market = pres.slides[3]  # stats_callout
    metric_el = market.elements[1]
    assert metric_el.type == "metric_group"
    labels = [m.label for m in metric_el.content.metrics]
    assert "TAM" in labels
    assert "SAM" in labels
    assert "SOM" in labels


def test_traction_renders_line_chart_when_data_provided():
    pres = compose_pitch_deck(_sample_pitch())
    traction = pres.slides[5]
    chart_el = traction.elements[1]
    assert chart_el.type == "chart"
    assert chart_el.chart_data.chart_type == "line"
    assert len(chart_el.chart_data.categories) == 4


def test_traction_falls_back_when_data_missing():
    facts = _sample_pitch()
    facts.traction_periods = []
    facts.traction_values = []
    pres = compose_pitch_deck(facts)
    traction = pres.slides[5]
    kinds = [el.type for el in traction.elements]
    assert "chart" not in kinds
    assert "body_text" in kinds


def test_competition_table_has_3_columns():
    pres = compose_pitch_deck(_sample_pitch())
    comp = pres.slides[8]
    table_el = comp.elements[1]
    assert table_el.type == "table"
    assert table_el.content.headers == [
        "Competitor", "Positioning", "Our Differentiator"
    ]
    assert len(table_el.content.rows) == 2


def test_competition_falls_back_when_empty():
    facts = _sample_pitch()
    facts.competitors = []
    pres = compose_pitch_deck(facts)
    comp = pres.slides[8]
    kinds = [el.type for el in comp.elements]
    assert "table" not in kinds


def test_team_slide_lists_members_with_roles():
    pres = compose_pitch_deck(_sample_pitch())
    team = pres.slides[9]
    bullet_el = team.elements[1]
    joined = "\n".join(bullet_el.content.items)
    assert "Luca Rossi" in joined
    assert "Co-founder/CEO" in joined
    assert "Sara Bianchi" in joined


def test_financials_renders_bar_chart_when_provided():
    pres = compose_pitch_deck(_sample_pitch())
    fin = pres.slides[10]
    chart_el = fin.elements[1]
    assert chart_el.type == "chart"
    assert chart_el.chart_data.chart_type == "bar"
    # Two series: revenue + ebitda
    assert len(chart_el.chart_data.series) == 2


def test_ask_slide_carries_round_size_and_use_of_funds():
    pres = compose_pitch_deck(_sample_pitch())
    ask = pres.slides[11]
    sub = ask.elements[1]
    assert "€4" in sub.content.text
    bullets = ask.elements[2]
    joined = "\n".join(bullets.content.items)
    assert "Engineering" in joined


def test_contact_slide_includes_email_and_name():
    pres = compose_pitch_deck(_sample_pitch())
    contact = pres.slides[12]
    body = contact.elements[1]
    assert "luca@lumen.example" in body.content.text
    assert "Luca Rossi" in body.content.text


def test_vertical_agnostic_across_stages():
    for stage in ["pre_seed", "seed", "series_a", "series_b"]:
        facts = _sample_pitch()
        facts.stage = stage  # type: ignore[assignment]
        pres = compose_pitch_deck(facts)
        assert len(pres.slides) == 13
