"""Tests for Google Slides request builder."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from deckforge.rendering.gslides.converter import inches_to_emu
from deckforge.rendering.gslides.request_builder import SlideRequestBuilder


def _make_mock_theme():
    """Create a mock ResolvedTheme for testing."""
    theme = MagicMock()
    theme.colors.primary = "#1A73E8"
    theme.colors.secondary = "#5F6368"
    theme.colors.accent = "#E8710A"
    theme.colors.background = "#FFFFFF"
    theme.colors.surface = "#F1F3F4"
    theme.colors.text_primary = "#202124"
    theme.colors.text_secondary = "#5F6368"
    theme.colors.text_muted = "#80868B"
    theme.colors.positive = "#34A853"
    theme.colors.negative = "#EA4335"
    theme.colors.warning = "#FBBC04"
    theme.typography.heading_family = "Roboto"
    theme.typography.body_family = "Roboto"
    theme.typography.mono_family = "Roboto Mono"
    theme.typography.scale = {
        "h1": 44, "h2": 36, "h3": 28,
        "subtitle": 24, "body": 18, "caption": 14, "footnote": 10,
    }
    theme.typography.weights = {
        "heading": 700, "subtitle": 600, "body": 400, "caption": 400,
    }
    theme.typography.line_height = 1.4
    theme.chart_colors = ["#1A73E8", "#E8710A", "#34A853", "#EA4335"]
    theme.slide_masters = {}
    return theme


class TestSlideRequestBuilder:
    def test_init(self):
        builder = SlideRequestBuilder("slide_001", "page_001")
        assert builder.slide_id == "slide_001"
        assert builder.page_id == "page_001"

    def test_build_create_slide(self):
        builder = SlideRequestBuilder("slide_001", "page_001")
        req = builder.build_create_slide(0)
        assert "createSlide" in req
        cs = req["createSlide"]
        assert cs["objectId"] == "page_001"
        assert cs["insertionIndex"] == 0
        assert cs["slideLayoutReference"]["predefinedLayout"] == "BLANK"

    def test_build_background(self):
        builder = SlideRequestBuilder("slide_001", "page_001")
        req = builder.build_background("#FFFFFF")
        assert "updatePageProperties" in req
        upp = req["updatePageProperties"]
        assert upp["objectId"] == "page_001"
        assert "pageBackgroundFill" in upp["pageProperties"]
        assert "fields" in upp

    def test_dispatch_element_text(self):
        builder = SlideRequestBuilder("slide_001", "page_001")
        theme = _make_mock_theme()

        element = MagicMock()
        element.type = "heading"
        element.content = {"text": "Hello World"}
        element.style_overrides = None

        position = MagicMock()
        position.x = 1.0
        position.y = 0.5
        position.width = 10.0
        position.height = 1.0

        requests = builder.dispatch_element(element, position, theme)
        assert isinstance(requests, list)
        assert len(requests) > 0

    def test_dispatch_element_chart_placeholder(self):
        """Chart elements should return placeholder shapes (until 06-02)."""
        builder = SlideRequestBuilder("slide_001", "page_001")
        theme = _make_mock_theme()

        element = MagicMock()
        element.type = "chart"
        element.content = {"chart_type": "bar", "data": {}}
        element.style_overrides = None

        position = MagicMock()
        position.x = 1.0
        position.y = 1.0
        position.width = 8.0
        position.height = 5.0

        requests = builder.dispatch_element(element, position, theme)
        assert isinstance(requests, list)
        # Should have at least a shape for the placeholder
        assert len(requests) >= 1

    def test_dispatch_element_spacer_empty(self):
        """Spacer elements should return empty list."""
        builder = SlideRequestBuilder("slide_001", "page_001")
        theme = _make_mock_theme()

        element = MagicMock()
        element.type = "spacer"
        element.content = {}
        element.style_overrides = None

        position = MagicMock()
        position.x = 0
        position.y = 0
        position.width = 1
        position.height = 1

        requests = builder.dispatch_element(element, position, theme)
        assert requests == []

    def test_dispatch_element_structural_empty(self):
        """Structural elements (container, column, row, grid_cell) return []."""
        builder = SlideRequestBuilder("slide_001", "page_001")
        theme = _make_mock_theme()

        for etype in ["container", "column", "row", "grid_cell", "background"]:
            element = MagicMock()
            element.type = etype
            element.content = {}
            element.style_overrides = None

            position = MagicMock()
            position.x = 0
            position.y = 0
            position.width = 1
            position.height = 1

            requests = builder.dispatch_element(element, position, theme)
            assert requests == [], f"Expected empty list for {etype}"
