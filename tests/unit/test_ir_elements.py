"""Tests for IR element types — text, data, visual, layout + ElementUnion discriminated union."""

from __future__ import annotations

import pytest
from pydantic import ValidationError


# ── Text Elements ──────────────────────────────────────────────────────────────


class TestHeadingElement:
    def test_valid_heading(self):
        from deckforge.ir.elements.text import HeadingElement

        el = HeadingElement(type="heading", content={"text": "Hello", "level": "h1"})
        assert el.type == "heading"
        assert el.content.text == "Hello"
        assert el.content.level.value == "h1"

    def test_heading_default_level(self):
        from deckforge.ir.elements.text import HeadingElement

        el = HeadingElement(type="heading", content={"text": "Title"})
        assert el.content.level.value == "h1"


class TestSubheadingElement:
    def test_valid_subheading(self):
        from deckforge.ir.elements.text import SubheadingElement

        el = SubheadingElement(type="subheading", content={"text": "Sub"})
        assert el.type == "subheading"
        assert el.content.text == "Sub"


class TestBodyTextElement:
    def test_valid_body_text(self):
        from deckforge.ir.elements.text import BodyTextElement

        el = BodyTextElement(type="body_text", content={"text": "Paragraph here"})
        assert el.type == "body_text"
        assert el.content.text == "Paragraph here"
        assert el.content.markdown is False

    def test_body_text_markdown(self):
        from deckforge.ir.elements.text import BodyTextElement

        el = BodyTextElement(type="body_text", content={"text": "**bold**", "markdown": True})
        assert el.content.markdown is True


class TestBulletListElement:
    def test_valid_bullet_list(self):
        from deckforge.ir.elements.text import BulletListElement

        el = BulletListElement(type="bullet_list", content={"items": ["a", "b"]})
        assert el.type == "bullet_list"
        assert el.content.items == ["a", "b"]
        assert el.content.style == "disc"

    def test_bullet_list_custom_style(self):
        from deckforge.ir.elements.text import BulletListElement

        el = BulletListElement(
            type="bullet_list", content={"items": ["x"], "style": "arrow"}
        )
        assert el.content.style == "arrow"


class TestNumberedListElement:
    def test_valid_numbered_list(self):
        from deckforge.ir.elements.text import NumberedListElement

        el = NumberedListElement(type="numbered_list", content={"items": ["first", "second"]})
        assert el.type == "numbered_list"
        assert el.content.start == 1


class TestCalloutBoxElement:
    def test_valid_callout(self):
        from deckforge.ir.elements.text import CalloutBoxElement

        el = CalloutBoxElement(type="callout_box", content={"text": "Important!", "style": "warning"})
        assert el.content.style == "warning"


class TestPullQuoteElement:
    def test_valid_pull_quote(self):
        from deckforge.ir.elements.text import PullQuoteElement

        el = PullQuoteElement(type="pull_quote", content={"text": "Quote here"})
        assert el.content.text == "Quote here"
        assert el.content.attribution is None

    def test_pull_quote_with_attribution(self):
        from deckforge.ir.elements.text import PullQuoteElement

        el = PullQuoteElement(
            type="pull_quote", content={"text": "Wise words", "attribution": "Author"}
        )
        assert el.content.attribution == "Author"


class TestFootnoteElement:
    def test_valid_footnote(self):
        from deckforge.ir.elements.text import FootnoteElement

        el = FootnoteElement(type="footnote", content={"text": "Source: data"})
        assert el.content.text == "Source: data"
        assert el.content.number is None


class TestLabelElement:
    def test_valid_label(self):
        from deckforge.ir.elements.text import LabelElement

        el = LabelElement(type="label", content={"text": "Figure 1"})
        assert el.content.text == "Figure 1"


# ── Data Elements ──────────────────────────────────────────────────────────────


class TestTableElement:
    def test_valid_table(self):
        from deckforge.ir.elements.data import TableElement

        el = TableElement(
            type="table",
            content={"headers": ["Name", "Value"], "rows": [["A", 1], ["B", 2]]},
        )
        assert el.type == "table"
        assert el.content.headers == ["Name", "Value"]
        assert len(el.content.rows) == 2

    def test_table_with_footer(self):
        from deckforge.ir.elements.data import TableElement

        el = TableElement(
            type="table",
            content={
                "headers": ["Item", "Total"],
                "rows": [["X", 100]],
                "footer_row": ["Total", 100],
            },
        )
        assert el.content.footer_row == ["Total", 100]


class TestChartElement:
    def test_valid_chart_element_with_bar(self):
        from deckforge.ir.elements.data import ChartElement

        el = ChartElement(
            type="chart",
            chart_data={
                "chart_type": "bar",
                "categories": ["Q1", "Q2"],
                "series": [{"name": "Revenue", "values": [100, 200]}],
            },
        )
        assert el.type == "chart"
        assert el.chart_data.chart_type == "bar"


class TestKpiCardElement:
    def test_valid_kpi_card(self):
        from deckforge.ir.elements.data import KpiCardElement

        el = KpiCardElement(
            type="kpi_card",
            content={"label": "Revenue", "value": "$1.2M", "change": 15.5, "change_direction": "up"},
        )
        assert el.content.label == "Revenue"
        assert el.content.change_direction == "up"


class TestMetricGroupElement:
    def test_valid_metric_group(self):
        from deckforge.ir.elements.data import MetricGroupElement

        el = MetricGroupElement(
            type="metric_group",
            content={
                "metrics": [
                    {"label": "Rev", "value": "1M"},
                    {"label": "EBITDA", "value": "200K"},
                ]
            },
        )
        assert len(el.content.metrics) == 2


class TestProgressBarElement:
    def test_valid_progress_bar(self):
        from deckforge.ir.elements.data import ProgressBarElement

        el = ProgressBarElement(
            type="progress_bar", content={"label": "Complete", "value": 75.0}
        )
        assert el.content.value == 75.0
        assert el.content.max_value == 100


class TestGaugeElement:
    def test_valid_gauge(self):
        from deckforge.ir.elements.data import GaugeElement

        el = GaugeElement(
            type="gauge",
            content={"label": "Performance", "value": 85.0},
        )
        assert el.content.min_value == 0
        assert el.content.max_value == 100


class TestSparklineElement:
    def test_valid_sparkline(self):
        from deckforge.ir.elements.data import SparklineElement

        el = SparklineElement(
            type="sparkline", content={"values": [1.0, 2.0, 3.0, 2.5]}
        )
        assert el.content.values == [1.0, 2.0, 3.0, 2.5]


# ── Visual Elements ────────────────────────────────────────────────────────────


class TestImageElement:
    def test_valid_image(self):
        from deckforge.ir.elements.visual import ImageElement

        el = ImageElement(
            type="image",
            content={"url": "https://example.com/img.png", "alt_text": "Photo"},
        )
        assert el.content.url == "https://example.com/img.png"
        assert el.content.fit == "contain"


class TestIconElement:
    def test_valid_icon(self):
        from deckforge.ir.elements.visual import IconElement

        el = IconElement(type="icon", content={"name": "chart-bar"})
        assert el.content.name == "chart-bar"
        assert el.content.set == "default"


class TestShapeElement:
    def test_valid_shape(self):
        from deckforge.ir.elements.visual import ShapeElement

        el = ShapeElement(
            type="shape", content={"shape": "circle", "fill": "#FF0000"}
        )
        assert el.content.shape == "circle"


class TestDividerElement:
    def test_valid_divider(self):
        from deckforge.ir.elements.visual import DividerElement

        el = DividerElement(type="divider")
        assert el.type == "divider"


class TestSpacerElement:
    def test_valid_spacer(self):
        from deckforge.ir.elements.visual import SpacerElement

        el = SpacerElement(type="spacer")
        assert el.type == "spacer"


class TestLogoElement:
    def test_valid_logo(self):
        from deckforge.ir.elements.visual import LogoElement

        el = LogoElement(
            type="logo", content={"url": "https://example.com/logo.svg"}
        )
        assert el.content.placement == "top_left"


class TestBackgroundElement:
    def test_valid_background(self):
        from deckforge.ir.elements.visual import BackgroundElement

        el = BackgroundElement(
            type="background", content={"color": "#1a1a2e"}
        )
        assert el.content.color == "#1a1a2e"


# ── Layout Elements ────────────────────────────────────────────────────────────


class TestContainerElement:
    def test_valid_container(self):
        from deckforge.ir.elements.layout import ContainerElement

        el = ContainerElement(type="container", content={"children": []})
        assert el.type == "container"
        assert el.content.children == []


class TestColumnElement:
    def test_valid_column(self):
        from deckforge.ir.elements.layout import ColumnElement

        el = ColumnElement(type="column", content={"children": []})
        assert el.type == "column"


class TestRowElement:
    def test_valid_row(self):
        from deckforge.ir.elements.layout import RowElement

        el = RowElement(type="row", content={"children": []})
        assert el.type == "row"


class TestGridCellElement:
    def test_valid_grid_cell(self):
        from deckforge.ir.elements.layout import GridCellElement

        el = GridCellElement(type="grid_cell", content={"span": 2, "children": []})
        assert el.content.span == 2


# ── ElementUnion Discriminated Union ───────────────────────────────────────────


class TestElementUnion:
    def test_routes_heading(self):
        from pydantic import TypeAdapter
        from deckforge.ir.elements import ElementUnion

        adapter = TypeAdapter(ElementUnion)
        el = adapter.validate_python(
            {"type": "heading", "content": {"text": "Hi", "level": "h1"}}
        )
        assert type(el).__name__ == "HeadingElement"

    def test_routes_table(self):
        from pydantic import TypeAdapter
        from deckforge.ir.elements import ElementUnion

        adapter = TypeAdapter(ElementUnion)
        el = adapter.validate_python(
            {
                "type": "table",
                "content": {"headers": ["A"], "rows": [["1"]]},
            }
        )
        assert type(el).__name__ == "TableElement"

    def test_routes_image(self):
        from pydantic import TypeAdapter
        from deckforge.ir.elements import ElementUnion

        adapter = TypeAdapter(ElementUnion)
        el = adapter.validate_python(
            {"type": "image", "content": {"url": "https://example.com/x.png"}}
        )
        assert type(el).__name__ == "ImageElement"

    def test_routes_container(self):
        from pydantic import TypeAdapter
        from deckforge.ir.elements import ElementUnion

        adapter = TypeAdapter(ElementUnion)
        el = adapter.validate_python(
            {"type": "container", "content": {"children": []}}
        )
        assert type(el).__name__ == "ContainerElement"

    def test_invalid_element_type_raises(self):
        from pydantic import TypeAdapter
        from deckforge.ir.elements import ElementUnion

        adapter = TypeAdapter(ElementUnion)
        with pytest.raises(ValidationError) as exc_info:
            adapter.validate_python({"type": "nonexistent", "content": {}})
        assert "nonexistent" in str(exc_info.value).lower() or "type" in str(exc_info.value).lower()

    def test_missing_required_content_field(self):
        from pydantic import TypeAdapter
        from deckforge.ir.elements import ElementUnion

        adapter = TypeAdapter(ElementUnion)
        with pytest.raises(ValidationError):
            adapter.validate_python({"type": "heading"})
