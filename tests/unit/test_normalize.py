"""Tests for IR normalization (simplified -> strict schema transform).

Validates that normalize_ir() correctly handles:
- Slide type aliases (title -> title_slide, bullets -> bullet_points, etc.)
- Element type transforms (text+role -> heading/subheading/body_text)
- Chart data normalization (pie/donut/waterfall/funnel/radar/treemap)
- Table normalization
- Timeline -> bullet_list conversion
- Passthrough of already-strict IR
- Idempotency (normalizing already-normalized IR returns equivalent result)
"""

from __future__ import annotations

import copy

import pytest

from deckforge.ir.normalize import normalize_ir


class TestSlideTypeNormalization:
    """Simplified slide type names are mapped to strict enum values."""

    def test_title_maps_to_title_slide(self):
        ir = _minimal_ir(slide_type="title")
        result = normalize_ir(ir)
        assert result["slides"][0]["slide_type"] == "title_slide"

    def test_bullets_maps_to_bullet_points(self):
        ir = _minimal_ir(slide_type="bullets")
        result = normalize_ir(ir)
        assert result["slides"][0]["slide_type"] == "bullet_points"

    def test_chart_maps_to_chart_slide(self):
        ir = _minimal_ir(slide_type="chart")
        result = normalize_ir(ir)
        assert result["slides"][0]["slide_type"] == "chart_slide"

    def test_table_maps_to_table_slide(self):
        ir = _minimal_ir(slide_type="table")
        result = normalize_ir(ir)
        assert result["slides"][0]["slide_type"] == "table_slide"

    def test_closing_maps_to_thank_you(self):
        ir = _minimal_ir(slide_type="closing")
        result = normalize_ir(ir)
        assert result["slides"][0]["slide_type"] == "thank_you"

    def test_already_strict_passes_through(self):
        ir = _minimal_ir(slide_type="title_slide")
        result = normalize_ir(ir)
        assert result["slides"][0]["slide_type"] == "title_slide"

    def test_unknown_type_passes_through(self):
        ir = _minimal_ir(slide_type="custom_future_type")
        result = normalize_ir(ir)
        assert result["slides"][0]["slide_type"] == "custom_future_type"


class TestElementNormalization:
    """Simplified elements are transformed into strict schema format."""

    def test_text_title_becomes_heading_h1(self):
        ir = _minimal_ir(elements=[
            {"type": "text", "content": "Hello World", "role": "title"},
        ])
        elem = normalize_ir(ir)["slides"][0]["elements"][0]
        assert elem["type"] == "heading"
        assert elem["content"]["text"] == "Hello World"
        assert elem["content"]["level"] == "h1"

    def test_text_subtitle_becomes_subheading(self):
        ir = _minimal_ir(elements=[
            {"type": "text", "content": "Sub text", "role": "subtitle"},
        ])
        elem = normalize_ir(ir)["slides"][0]["elements"][0]
        assert elem["type"] == "subheading"
        assert elem["content"]["text"] == "Sub text"

    def test_text_body_becomes_body_text(self):
        ir = _minimal_ir(elements=[
            {"type": "text", "content": "Body content", "role": "body"},
        ])
        elem = normalize_ir(ir)["slides"][0]["elements"][0]
        assert elem["type"] == "body_text"
        assert elem["content"]["text"] == "Body content"

    def test_list_becomes_bullet_list(self):
        ir = _minimal_ir(elements=[
            {"type": "list", "items": ["A", "B", "C"]},
        ])
        elem = normalize_ir(ir)["slides"][0]["elements"][0]
        assert elem["type"] == "bullet_list"
        assert elem["content"]["items"] == ["A", "B", "C"]

    def test_table_normalized_correctly(self):
        ir = _minimal_ir(elements=[
            {
                "type": "table",
                "data": {
                    "headers": ["Col1", "Col2"],
                    "rows": [["a", "b"], ["c", "d"]],
                },
            },
        ])
        elem = normalize_ir(ir)["slides"][0]["elements"][0]
        assert elem["type"] == "table"
        assert elem["content"]["headers"] == ["Col1", "Col2"]
        assert elem["content"]["rows"] == [["a", "b"], ["c", "d"]]

    def test_strict_element_passes_through(self):
        ir = _minimal_ir(elements=[
            {"type": "heading", "content": {"text": "Already strict", "level": "h1"}},
        ])
        elem = normalize_ir(ir)["slides"][0]["elements"][0]
        assert elem["type"] == "heading"
        assert elem["content"]["text"] == "Already strict"


class TestChartNormalization:
    """Chart elements are transformed from simplified format to ChartUnion schema."""

    def test_bar_chart_normalized(self):
        ir = _minimal_ir(elements=[
            {
                "type": "chart",
                "chart_type": "bar",
                "data": {
                    "categories": ["A", "B"],
                    "series": [{"name": "S1", "values": [10, 20]}],
                },
            },
        ])
        elem = normalize_ir(ir)["slides"][0]["elements"][0]
        assert elem["type"] == "chart"
        assert elem["chart_data"]["chart_type"] == "bar"
        assert elem["chart_data"]["categories"] == ["A", "B"]

    def test_pie_chart_uses_labels_not_categories(self):
        ir = _minimal_ir(elements=[
            {
                "type": "chart",
                "chart_type": "pie",
                "data": {
                    "categories": ["X", "Y", "Z"],
                    "series": [{"name": "Values", "values": [40, 35, 25]}],
                },
            },
        ])
        elem = normalize_ir(ir)["slides"][0]["elements"][0]
        cd = elem["chart_data"]
        assert cd["chart_type"] == "pie"
        assert cd["labels"] == ["X", "Y", "Z"]
        assert cd["values"] == [40, 35, 25]
        assert "categories" not in cd

    def test_waterfall_chart_flattens_series(self):
        ir = _minimal_ir(elements=[
            {
                "type": "chart",
                "chart_type": "waterfall",
                "data": {
                    "categories": ["Start", "+A", "-B", "End"],
                    "series": [{"name": "Values", "values": [100, 30, -20, 110]}],
                },
            },
        ])
        elem = normalize_ir(ir)["slides"][0]["elements"][0]
        cd = elem["chart_data"]
        assert cd["chart_type"] == "waterfall"
        assert cd["categories"] == ["Start", "+A", "-B", "End"]
        assert cd["values"] == [100, 30, -20, 110]

    def test_funnel_chart_uses_stages(self):
        ir = _minimal_ir(elements=[
            {
                "type": "chart",
                "chart_type": "funnel",
                "data": {
                    "categories": ["Leads", "Qualified", "Closed"],
                    "series": [{"name": "Count", "values": [1000, 250, 50]}],
                },
            },
        ])
        elem = normalize_ir(ir)["slides"][0]["elements"][0]
        cd = elem["chart_data"]
        assert cd["chart_type"] == "funnel"
        assert cd["stages"] == ["Leads", "Qualified", "Closed"]
        assert cd["values"] == [1000, 250, 50]


class TestTimelineNormalization:
    """Timeline elements are converted to bullet_list."""

    def test_timeline_dict_items_to_bullet_list(self):
        ir = _minimal_ir(elements=[
            {
                "type": "timeline",
                "items": [
                    {"date": "Q1", "title": "Launch", "description": "v1.0 shipped"},
                    {"date": "Q2", "title": "Growth", "description": "10K users"},
                ],
            },
        ])
        elem = normalize_ir(ir)["slides"][0]["elements"][0]
        assert elem["type"] == "bullet_list"
        assert len(elem["content"]["items"]) == 2
        assert "Q1" in elem["content"]["items"][0]
        assert "Launch" in elem["content"]["items"][0]


class TestIdempotency:
    """Normalizing already-normalized IR produces equivalent output."""

    def test_double_normalize_is_idempotent(self):
        ir = {
            "schema_version": "1.0",
            "metadata": {"title": "Test"},
            "theme": "executive-dark",
            "slides": [
                {
                    "slide_type": "title",
                    "elements": [
                        {"type": "text", "content": "Hello", "role": "title"},
                    ],
                },
            ],
        }
        first = normalize_ir(ir)
        second = normalize_ir(first)
        assert first == second

    def test_does_not_mutate_input(self):
        ir = {
            "schema_version": "1.0",
            "metadata": {"title": "Test"},
            "slides": [
                {
                    "slide_type": "title",
                    "elements": [
                        {"type": "text", "content": "Hello", "role": "title"},
                    ],
                },
            ],
        }
        original = copy.deepcopy(ir)
        normalize_ir(ir)
        assert ir == original


class TestFullNormalizationValidation:
    """Normalized simplified IR passes Presentation.model_validate()."""

    def test_startup_pitch_simplified_validates(self):
        """A realistic simplified IR normalizes into valid Presentation."""
        from deckforge.ir import Presentation

        ir = {
            "schema_version": "1.0",
            "metadata": {"title": "AI Startup Pitch"},
            "theme": "modern-gradient",
            "slides": [
                {
                    "slide_type": "title",
                    "elements": [
                        {"type": "text", "content": "AI Startup", "role": "title"},
                        {"type": "text", "content": "Series A Pitch", "role": "subtitle"},
                    ],
                },
                {
                    "slide_type": "bullets",
                    "elements": [
                        {"type": "text", "content": "The Problem", "role": "title"},
                        {"type": "list", "items": ["Issue A", "Issue B", "Issue C"]},
                    ],
                },
                {
                    "slide_type": "chart",
                    "elements": [
                        {"type": "text", "content": "Market Size", "role": "title"},
                        {
                            "type": "chart",
                            "chart_type": "bar",
                            "data": {
                                "categories": ["TAM", "SAM", "SOM"],
                                "series": [{"name": "Size ($B)", "values": [50, 15, 3]}],
                            },
                        },
                    ],
                },
                {
                    "slide_type": "closing",
                    "elements": [
                        {"type": "text", "content": "Thank You", "role": "title"},
                    ],
                },
            ],
        }

        normalized = normalize_ir(ir)
        presentation = Presentation.model_validate(normalized)
        assert len(presentation.slides) == 4


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_ir(
    slide_type: str = "title_slide",
    elements: list | None = None,
) -> dict:
    """Build a minimal IR dict with one slide."""
    return {
        "schema_version": "1.0",
        "metadata": {"title": "Test Presentation"},
        "slides": [
            {
                "slide_type": slide_type,
                "elements": elements or [
                    {"type": "heading", "content": {"text": "Test", "level": "h1"}},
                ],
            },
        ],
    }
