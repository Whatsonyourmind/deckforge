"""Slide type registry — static catalog of all 32 slide types with metadata and example IR.

Provides discovery data for the GET /v1/slide-types endpoint so agents and
developers can programmatically explore DeckForge's slide capabilities.
"""

from __future__ import annotations

from typing import Any

from deckforge.ir.enums import SlideType

# ---------------------------------------------------------------------------
# Helpers for building minimal valid example IR
# ---------------------------------------------------------------------------

_META = {"title": "Example", "language": "en"}


def _ir(slide_type: str, elements: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Build a minimal valid Presentation IR dict for a single slide."""
    slide: dict[str, Any] = {"slide_type": slide_type, "elements": elements or []}
    return {
        "schema_version": "1.0",
        "metadata": _META,
        "theme": "executive-dark",
        "slides": [slide],
    }


def _heading(text: str) -> dict[str, Any]:
    return {"type": "heading", "content": {"text": text}}


def _subheading(text: str) -> dict[str, Any]:
    return {"type": "subheading", "content": {"text": text}}


def _body(text: str) -> dict[str, Any]:
    return {"type": "body_text", "content": {"text": text}}


def _bullets(items: list[str]) -> dict[str, Any]:
    return {"type": "bullet_list", "content": {"items": items}}


def _table(headers: list[str], rows: list[list[str]]) -> dict[str, Any]:
    return {
        "type": "table",
        "content": {
            "headers": headers,
            "rows": rows,
        },
    }


def _bar_chart(categories: list[str], series: list[dict]) -> dict[str, Any]:
    """Build a bar chart element with proper chart_data field."""
    return {
        "type": "chart",
        "chart_data": {
            "chart_type": "bar",
            "categories": categories,
            "series": series,
        },
    }


def _waterfall_chart(categories: list[str], values: list[int | float]) -> dict[str, Any]:
    """Build a waterfall chart element with proper chart_data field."""
    return {
        "type": "chart",
        "chart_data": {
            "chart_type": "waterfall",
            "categories": categories,
            "values": values,
        },
    }


def _kpi(label: str, value: str) -> dict[str, Any]:
    return {"type": "kpi_card", "content": {"label": label, "value": value}}


# ---------------------------------------------------------------------------
# Slide type definitions: (id, name, description, category,
#   required_elements, optional_elements, example_ir)
# ---------------------------------------------------------------------------

_SLIDE_TYPES: list[dict[str, Any]] = [
    # ── Universal (23) ─────────────────────────────────────────────────
    {
        "id": "title_slide",
        "name": "Title Slide",
        "description": "Opening slide with presentation title, subtitle, and optional branding.",
        "category": "universal",
        "required_elements": ["heading"],
        "optional_elements": ["subheading", "image", "logo"],
        "example_ir": _ir("title_slide", [_heading("Quarterly Business Review"), _subheading("Q1 2026 Performance Summary")]),
    },
    {
        "id": "agenda",
        "name": "Agenda",
        "description": "Meeting agenda or table of contents with numbered topics.",
        "category": "universal",
        "required_elements": ["heading", "bullet_list"],
        "optional_elements": ["body_text"],
        "example_ir": _ir("agenda", [_heading("Agenda"), _bullets(["Financial Overview", "Product Updates", "Q&A"])]),
    },
    {
        "id": "section_divider",
        "name": "Section Divider",
        "description": "Visual break between presentation sections.",
        "category": "universal",
        "required_elements": ["heading"],
        "optional_elements": ["subheading", "body_text"],
        "example_ir": _ir("section_divider", [_heading("Financial Highlights")]),
    },
    {
        "id": "key_message",
        "name": "Key Message",
        "description": "Single impactful statement or key takeaway displayed prominently.",
        "category": "universal",
        "required_elements": ["heading"],
        "optional_elements": ["body_text", "subheading"],
        "example_ir": _ir("key_message", [_heading("Revenue grew 42% year-over-year")]),
    },
    {
        "id": "bullet_points",
        "name": "Bullet Points",
        "description": "Standard content slide with a heading and bullet list.",
        "category": "universal",
        "required_elements": ["heading", "bullet_list"],
        "optional_elements": ["subheading", "body_text"],
        "example_ir": _ir("bullet_points", [_heading("Key Achievements"), _bullets(["Exceeded revenue target by 15%", "Launched 3 new products", "Expanded to 5 new markets"])]),
    },
    {
        "id": "two_column_text",
        "name": "Two Column Text",
        "description": "Side-by-side text columns for comparing or organizing content.",
        "category": "universal",
        "required_elements": ["heading", "body_text"],
        "optional_elements": ["bullet_list", "subheading"],
        "example_ir": _ir("two_column_text", [_heading("Before & After"), _body("Previous approach with manual processes."), _body("New automated workflow with 60% efficiency gain.")]),
    },
    {
        "id": "comparison",
        "name": "Comparison",
        "description": "Side-by-side comparison of two or more options, products, or approaches.",
        "category": "universal",
        "required_elements": ["heading", "table"],
        "optional_elements": ["body_text", "bullet_list"],
        "example_ir": _ir("comparison", [_heading("Plan Comparison"), _table(["Feature", "Basic", "Pro"], [["Storage", "10 GB", "100 GB"], ["Support", "Email", "24/7"]])]),
    },
    {
        "id": "timeline",
        "name": "Timeline",
        "description": "Chronological sequence of events or milestones.",
        "category": "universal",
        "required_elements": ["heading"],
        "optional_elements": ["body_text", "bullet_list"],
        "example_ir": _ir("timeline", [_heading("Project Timeline"), _bullets(["Q1: Research", "Q2: Development", "Q3: Beta Launch", "Q4: GA Release"])]),
    },
    {
        "id": "process_flow",
        "name": "Process Flow",
        "description": "Step-by-step process or workflow visualization.",
        "category": "universal",
        "required_elements": ["heading"],
        "optional_elements": ["body_text", "bullet_list"],
        "example_ir": _ir("process_flow", [_heading("Approval Process"), _bullets(["Submit Request", "Manager Review", "Finance Approval", "Execution"])]),
    },
    {
        "id": "org_chart",
        "name": "Org Chart",
        "description": "Organizational hierarchy or team structure visualization.",
        "category": "universal",
        "required_elements": ["heading"],
        "optional_elements": ["body_text"],
        "example_ir": _ir("org_chart", [_heading("Leadership Team")]),
    },
    {
        "id": "team_slide",
        "name": "Team Slide",
        "description": "Team member profiles with photos, names, and titles.",
        "category": "universal",
        "required_elements": ["heading"],
        "optional_elements": ["body_text", "image"],
        "example_ir": _ir("team_slide", [_heading("Our Team"), _body("Led by experienced industry professionals.")]),
    },
    {
        "id": "quote_slide",
        "name": "Quote Slide",
        "description": "Featured quotation with attribution.",
        "category": "universal",
        "required_elements": ["heading"],
        "optional_elements": ["body_text", "subheading"],
        "example_ir": _ir("quote_slide", [_heading("Innovation distinguishes between a leader and a follower."), _body("Steve Jobs")]),
    },
    {
        "id": "image_with_caption",
        "name": "Image with Caption",
        "description": "Full or half-width image with descriptive caption.",
        "category": "universal",
        "required_elements": ["image"],
        "optional_elements": ["heading", "body_text"],
        "example_ir": _ir("image_with_caption", [_heading("Product Screenshot")]),
    },
    {
        "id": "icon_grid",
        "name": "Icon Grid",
        "description": "Grid of icons with labels for features, services, or categories.",
        "category": "universal",
        "required_elements": ["heading"],
        "optional_elements": ["body_text", "icon"],
        "example_ir": _ir("icon_grid", [_heading("Our Services"), _bullets(["Consulting", "Development", "Support", "Training"])]),
    },
    {
        "id": "stats_callout",
        "name": "Stats Callout",
        "description": "Prominent statistics or KPI cards with large numbers.",
        "category": "universal",
        "required_elements": ["heading", "kpi_card"],
        "optional_elements": ["body_text"],
        "example_ir": _ir("stats_callout", [_heading("Key Metrics"), _kpi("Revenue", "$42M"), _kpi("Growth", "+28%"), _kpi("Customers", "1,200")]),
    },
    {
        "id": "table_slide",
        "name": "Table Slide",
        "description": "Data table with headers and rows for structured information.",
        "category": "universal",
        "required_elements": ["heading", "table"],
        "optional_elements": ["body_text", "footnote"],
        "example_ir": _ir("table_slide", [_heading("Quarterly Results"), _table(["Metric", "Q1", "Q2"], [["Revenue", "$10M", "$12M"], ["EBITDA", "$3M", "$4M"]])]),
    },
    {
        "id": "chart_slide",
        "name": "Chart Slide",
        "description": "Data visualization chart (bar, line, pie, etc.).",
        "category": "universal",
        "required_elements": ["heading", "chart"],
        "optional_elements": ["body_text", "footnote"],
        "example_ir": _ir("chart_slide", [_heading("Revenue Trend"), _bar_chart(["Q1", "Q2", "Q3"], [{"name": "Revenue", "values": [10, 12, 15]}])]),
    },
    {
        "id": "matrix",
        "name": "Matrix",
        "description": "2x2 or larger matrix for categorization and prioritization.",
        "category": "universal",
        "required_elements": ["heading"],
        "optional_elements": ["body_text", "table"],
        "example_ir": _ir("matrix", [_heading("Priority Matrix"), _table(["", "High Impact", "Low Impact"], [["High Effort", "Strategic", "Avoid"], ["Low Effort", "Quick Win", "Fill-In"]])]),
    },
    {
        "id": "funnel",
        "name": "Funnel",
        "description": "Funnel visualization for sales pipeline or conversion stages.",
        "category": "universal",
        "required_elements": ["heading"],
        "optional_elements": ["body_text", "bullet_list"],
        "example_ir": _ir("funnel", [_heading("Sales Funnel"), _bullets(["Leads: 10,000", "Qualified: 2,500", "Proposals: 500", "Closed: 125"])]),
    },
    {
        "id": "map_slide",
        "name": "Map Slide",
        "description": "Geographic visualization for regional data or office locations.",
        "category": "universal",
        "required_elements": ["heading"],
        "optional_elements": ["body_text", "image"],
        "example_ir": _ir("map_slide", [_heading("Global Presence"), _body("Offices in 12 countries across 4 continents.")]),
    },
    {
        "id": "thank_you",
        "name": "Thank You",
        "description": "Closing slide with thank-you message and contact information.",
        "category": "universal",
        "required_elements": ["heading"],
        "optional_elements": ["body_text", "subheading"],
        "example_ir": _ir("thank_you", [_heading("Thank You"), _body("Questions? Contact us at info@example.com")]),
    },
    {
        "id": "appendix",
        "name": "Appendix",
        "description": "Supplementary material and supporting data.",
        "category": "universal",
        "required_elements": ["heading"],
        "optional_elements": ["body_text", "table", "chart"],
        "example_ir": _ir("appendix", [_heading("Appendix: Detailed Methodology"), _body("See attached spreadsheet for full calculation details.")]),
    },
    {
        "id": "q_and_a",
        "name": "Q&A",
        "description": "Question and answer session prompt.",
        "category": "universal",
        "required_elements": ["heading"],
        "optional_elements": ["body_text"],
        "example_ir": _ir("q_and_a", [_heading("Questions?")]),
    },
    # ── Finance (9) ────────────────────────────────────────────────────
    {
        "id": "dcf_summary",
        "name": "DCF Summary",
        "description": "Discounted cash flow valuation summary with implied share price range.",
        "category": "finance",
        "required_elements": ["heading", "table"],
        "optional_elements": ["chart", "body_text", "footnote"],
        "example_ir": _ir("dcf_summary", [
            _heading("DCF Valuation Summary"),
            _table(
                ["Metric", "Bear", "Base", "Bull"],
                [
                    ["Enterprise Value", "$8.2B", "$10.5B", "$13.1B"],
                    ["Equity Value", "$6.8B", "$9.1B", "$11.7B"],
                    ["Implied Share Price", "$45", "$60", "$78"],
                ],
            ),
        ]),
    },
    {
        "id": "comp_table",
        "name": "Comparable Companies Table",
        "description": "Trading comps with key financial multiples for peer comparison.",
        "category": "finance",
        "required_elements": ["heading", "table"],
        "optional_elements": ["body_text", "footnote"],
        "example_ir": _ir("comp_table", [
            _heading("Public Comparable Companies"),
            _table(
                ["Company", "EV/Revenue", "EV/EBITDA", "P/E"],
                [
                    ["Peer A", "8.2x", "22.1x", "35.4x"],
                    ["Peer B", "6.5x", "18.3x", "28.7x"],
                    ["Median", "7.4x", "20.2x", "32.1x"],
                ],
            ),
        ]),
    },
    {
        "id": "waterfall_chart",
        "name": "Waterfall Chart",
        "description": "Bridge chart showing incremental changes from starting to ending value.",
        "category": "finance",
        "required_elements": ["heading", "chart"],
        "optional_elements": ["body_text", "footnote"],
        "example_ir": _ir("waterfall_chart", [
            _heading("EBITDA Bridge"),
            _waterfall_chart(
                ["2025 EBITDA", "Revenue Growth", "Cost Savings", "Investments", "2026 EBITDA"],
                [100, 30, 15, -10, 135],
            ),
        ]),
    },
    {
        "id": "deal_overview",
        "name": "Deal Overview",
        "description": "Transaction summary with key terms, parties, and structure.",
        "category": "finance",
        "required_elements": ["heading", "table"],
        "optional_elements": ["body_text", "bullet_list"],
        "example_ir": _ir("deal_overview", [
            _heading("Transaction Overview"),
            _table(
                ["Parameter", "Detail"],
                [
                    ["Target", "Acme Corp"],
                    ["Transaction Type", "100% Acquisition"],
                    ["Enterprise Value", "$500M"],
                    ["Structure", "Cash + Stock"],
                ],
            ),
        ]),
    },
    {
        "id": "returns_analysis",
        "name": "Returns Analysis",
        "description": "Investment return metrics including IRR, MOIC, and payback period.",
        "category": "finance",
        "required_elements": ["heading", "table"],
        "optional_elements": ["chart", "body_text", "kpi_card"],
        "example_ir": _ir("returns_analysis", [
            _heading("Returns Analysis"),
            _table(
                ["Scenario", "IRR", "MOIC", "Payback"],
                [
                    ["Base", "22%", "2.8x", "4.2 years"],
                    ["Upside", "28%", "3.5x", "3.5 years"],
                    ["Downside", "14%", "1.8x", "5.8 years"],
                ],
            ),
        ]),
    },
    {
        "id": "capital_structure",
        "name": "Capital Structure",
        "description": "Debt and equity breakdown with cost of capital analysis.",
        "category": "finance",
        "required_elements": ["heading", "table"],
        "optional_elements": ["chart", "body_text"],
        "example_ir": _ir("capital_structure", [
            _heading("Capital Structure"),
            _table(
                ["Instrument", "Amount", "Rate", "% of Total"],
                [
                    ["Senior Debt", "$200M", "5.5%", "40%"],
                    ["Mezzanine", "$75M", "10.0%", "15%"],
                    ["Equity", "$225M", "—", "45%"],
                ],
            ),
        ]),
    },
    {
        "id": "market_landscape",
        "name": "Market Landscape",
        "description": "Competitive positioning, TAM/SAM/SOM, or market share overview.",
        "category": "finance",
        "required_elements": ["heading"],
        "optional_elements": ["chart", "table", "body_text", "bullet_list"],
        "example_ir": _ir("market_landscape", [
            _heading("Market Landscape"),
            _bullets(["TAM: $50B global market", "SAM: $12B addressable segment", "SOM: $2B achievable share"]),
        ]),
    },
    {
        "id": "risk_matrix",
        "name": "Risk Matrix",
        "description": "Risk assessment grid plotting likelihood against impact severity.",
        "category": "finance",
        "required_elements": ["heading", "table"],
        "optional_elements": ["body_text"],
        "example_ir": _ir("risk_matrix", [
            _heading("Risk Assessment Matrix"),
            _table(
                ["Risk", "Likelihood", "Impact", "Mitigation"],
                [
                    ["Regulatory Change", "Medium", "High", "Lobby and compliance monitoring"],
                    ["Key Person Risk", "Low", "High", "Succession planning"],
                    ["Market Downturn", "Medium", "Medium", "Diversification strategy"],
                ],
            ),
        ]),
    },
    {
        "id": "investment_thesis",
        "name": "Investment Thesis",
        "description": "Core investment rationale with key value drivers and catalysts.",
        "category": "finance",
        "required_elements": ["heading", "bullet_list"],
        "optional_elements": ["body_text", "subheading"],
        "example_ir": _ir("investment_thesis", [
            _heading("Investment Thesis"),
            _bullets([
                "Market leader in $12B addressable market",
                "30% recurring revenue with 95% retention",
                "Clear path to 25%+ EBITDA margins by 2028",
                "Multiple expansion catalysts in next 12 months",
            ]),
        ]),
    },
]


class SlideTypeRegistry:
    """Static registry of all 32 slide types with metadata and example IR.

    Used by the GET /v1/slide-types discovery endpoint.
    """

    def __init__(self) -> None:
        self._types: dict[str, dict[str, Any]] = {st["id"]: st for st in _SLIDE_TYPES}

    def get_all(self) -> list[dict[str, Any]]:
        """Return all slide type entries."""
        return list(self._types.values())

    def get_by_id(self, slide_type: str) -> dict[str, Any] | None:
        """Look up a single slide type by id."""
        return self._types.get(slide_type)

    def get_by_category(self, category: str) -> list[dict[str, Any]]:
        """Filter slide types by category (universal, finance, data, narrative)."""
        return [st for st in self._types.values() if st["category"] == category]
