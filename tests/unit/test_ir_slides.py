"""Tests for IR slide types — 23 universal + 9 finance + SlideUnion discriminated union."""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError


# ── Universal Slide Types ──────────────────────────────────────────────────────


UNIVERSAL_SLIDE_TYPES = [
    "title_slide",
    "agenda",
    "section_divider",
    "key_message",
    "bullet_points",
    "two_column_text",
    "comparison",
    "timeline",
    "process_flow",
    "org_chart",
    "team_slide",
    "quote_slide",
    "image_with_caption",
    "icon_grid",
    "stats_callout",
    "table_slide",
    "chart_slide",
    "matrix",
    "funnel",
    "map_slide",
    "thank_you",
    "appendix",
    "q_and_a",
]

FINANCE_SLIDE_TYPES = [
    "dcf_summary",
    "comp_table",
    "waterfall_chart",
    "deal_overview",
    "returns_analysis",
    "capital_structure",
    "market_landscape",
    "risk_matrix",
    "investment_thesis",
]


class TestUniversalSlideTypes:
    @pytest.mark.parametrize("slide_type", UNIVERSAL_SLIDE_TYPES)
    def test_universal_slide_validates(self, slide_type: str):
        from deckforge.ir.slides import SlideUnion

        adapter = TypeAdapter(SlideUnion)
        slide = adapter.validate_python({"slide_type": slide_type, "elements": []})
        assert slide.slide_type == slide_type

    def test_title_slide_basic(self):
        from deckforge.ir.slides.universal import TitleSlide

        slide = TitleSlide(slide_type="title_slide", elements=[])
        assert slide.slide_type == "title_slide"
        assert slide.elements == []

    def test_timeline_direction_default(self):
        from deckforge.ir.slides.universal import TimelineSlide

        slide = TimelineSlide(slide_type="timeline", elements=[])
        assert slide.timeline_direction == "horizontal"

    def test_timeline_direction_vertical(self):
        from deckforge.ir.slides.universal import TimelineSlide

        slide = TimelineSlide(
            slide_type="timeline", elements=[], timeline_direction="vertical"
        )
        assert slide.timeline_direction == "vertical"

    def test_process_flow_direction_default(self):
        from deckforge.ir.slides.universal import ProcessFlowSlide

        slide = ProcessFlowSlide(slide_type="process_flow", elements=[])
        assert slide.flow_direction == "horizontal"

    def test_icon_grid_columns_default(self):
        from deckforge.ir.slides.universal import IconGridSlide

        slide = IconGridSlide(slide_type="icon_grid", elements=[])
        assert slide.columns == 3


class TestFinanceSlideTypes:
    @pytest.mark.parametrize("slide_type", FINANCE_SLIDE_TYPES)
    def test_finance_slide_validates(self, slide_type: str):
        from deckforge.ir.slides import SlideUnion

        adapter = TypeAdapter(SlideUnion)
        slide = adapter.validate_python({"slide_type": slide_type, "elements": []})
        assert slide.slide_type == slide_type

    def test_dcf_summary_optional_fields(self):
        from deckforge.ir.slides.finance import DcfSummarySlide

        slide = DcfSummarySlide(
            slide_type="dcf_summary",
            elements=[],
            discount_rate_range=[8.0, 12.0],
            terminal_growth_range=[2.0, 3.0],
        )
        assert slide.discount_rate_range == [8.0, 12.0]

    def test_comp_table_optional_fields(self):
        from deckforge.ir.slides.finance import CompTableSlide

        slide = CompTableSlide(
            slide_type="comp_table",
            elements=[],
            highlight_column="EV/EBITDA",
            sort_by="Revenue",
        )
        assert slide.highlight_column == "EV/EBITDA"

    def test_waterfall_chart_show_running_total(self):
        from deckforge.ir.slides.finance import WaterfallChartSlide

        slide = WaterfallChartSlide(slide_type="waterfall_chart", elements=[])
        assert slide.show_running_total is True

    def test_risk_matrix_axes_labels(self):
        from deckforge.ir.slides.finance import RiskMatrixSlide

        slide = RiskMatrixSlide(
            slide_type="risk_matrix",
            elements=[],
            axes_labels={"x": "Impact", "y": "Probability"},
        )
        assert slide.axes_labels["x"] == "Impact"


class TestSlideUnionDiscriminator:
    def test_routes_title_slide(self):
        from deckforge.ir.slides import SlideUnion

        adapter = TypeAdapter(SlideUnion)
        slide = adapter.validate_python(
            {"slide_type": "title_slide", "elements": []}
        )
        assert type(slide).__name__ == "TitleSlide"

    def test_routes_chart_slide(self):
        from deckforge.ir.slides import SlideUnion

        adapter = TypeAdapter(SlideUnion)
        slide = adapter.validate_python(
            {"slide_type": "chart_slide", "elements": []}
        )
        assert type(slide).__name__ == "ChartSlideSlide"

    def test_routes_dcf_summary(self):
        from deckforge.ir.slides import SlideUnion

        adapter = TypeAdapter(SlideUnion)
        slide = adapter.validate_python(
            {"slide_type": "dcf_summary", "elements": []}
        )
        assert type(slide).__name__ == "DcfSummarySlide"

    def test_invalid_slide_type_raises(self):
        from deckforge.ir.slides import SlideUnion

        adapter = TypeAdapter(SlideUnion)
        with pytest.raises(ValidationError) as exc_info:
            adapter.validate_python(
                {"slide_type": "nonexistent_slide", "elements": []}
            )
        error_str = str(exc_info.value).lower()
        assert "nonexistent_slide" in error_str or "slide_type" in error_str

    def test_all_32_slide_types_covered(self):
        """Verify all 32 slide types are in the union."""
        from deckforge.ir.slides import SlideUnion

        adapter = TypeAdapter(SlideUnion)
        all_types = UNIVERSAL_SLIDE_TYPES + FINANCE_SLIDE_TYPES
        assert len(all_types) == 32
        for st in all_types:
            slide = adapter.validate_python({"slide_type": st, "elements": []})
            assert slide.slide_type == st


class TestSlideWithElements:
    def test_slide_with_heading_element(self):
        from deckforge.ir.slides import SlideUnion

        adapter = TypeAdapter(SlideUnion)
        slide = adapter.validate_python(
            {
                "slide_type": "title_slide",
                "elements": [
                    {"type": "heading", "content": {"text": "Welcome", "level": "h1"}}
                ],
            }
        )
        assert len(slide.elements) == 1
        assert slide.elements[0].type == "heading"

    def test_slide_with_mixed_elements(self):
        from deckforge.ir.slides import SlideUnion

        adapter = TypeAdapter(SlideUnion)
        slide = adapter.validate_python(
            {
                "slide_type": "bullet_points",
                "elements": [
                    {"type": "heading", "content": {"text": "Key Points"}},
                    {"type": "bullet_list", "content": {"items": ["Point 1", "Point 2"]}},
                    {"type": "footnote", "content": {"text": "Source: data"}},
                ],
            }
        )
        assert len(slide.elements) == 3


class TestSlideBaseFields:
    def test_layout_hint_default(self):
        from deckforge.ir.slides.universal import TitleSlide

        slide = TitleSlide(slide_type="title_slide", elements=[])
        assert slide.layout_hint is None

    def test_layout_hint_set(self):
        from deckforge.ir.slides.universal import TitleSlide

        slide = TitleSlide(
            slide_type="title_slide", elements=[], layout_hint="centered"
        )
        assert slide.layout_hint == "centered"

    def test_speaker_notes(self):
        from deckforge.ir.slides.universal import TitleSlide

        slide = TitleSlide(
            slide_type="title_slide",
            elements=[],
            speaker_notes="Remember to introduce yourself.",
        )
        assert slide.speaker_notes == "Remember to introduce yourself."

    def test_transition_default(self):
        from deckforge.ir.slides.universal import TitleSlide

        slide = TitleSlide(slide_type="title_slide", elements=[])
        assert slide.transition is None
