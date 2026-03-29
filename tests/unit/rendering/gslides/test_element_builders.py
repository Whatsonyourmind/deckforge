"""Tests for Google Slides element builder functions."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from deckforge.rendering.gslides.converter import inches_to_emu
from deckforge.rendering.gslides.element_builders import (
    build_bullet_list_requests,
    build_callout_box_requests,
    build_divider_requests,
    build_image_requests,
    build_kpi_card_requests,
    build_numbered_list_requests,
    build_pull_quote_requests,
    build_shape_requests,
    build_table_requests,
    build_text_requests,
)


def _make_mock_theme():
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
    return theme


def _make_position(x=1.0, y=1.0, w=10.0, h=1.5):
    pos = MagicMock()
    pos.x = x
    pos.y = y
    pos.width = w
    pos.height = h
    return pos


class TestBuildTextRequests:
    def test_heading_produces_shape_and_text(self):
        theme = _make_mock_theme()
        element = MagicMock()
        element.type = "heading"
        element.content = {"text": "Hello World"}
        element.style_overrides = None
        pos = _make_position()

        reqs = build_text_requests("page_1", element, pos, theme)
        assert len(reqs) >= 2  # At least CreateShape + InsertText
        assert any("createShape" in r for r in reqs)
        assert any("insertText" in r for r in reqs)

    def test_body_text(self):
        theme = _make_mock_theme()
        element = MagicMock()
        element.type = "body_text"
        element.content = {"text": "Body content"}
        element.style_overrides = None
        pos = _make_position()

        reqs = build_text_requests("page_1", element, pos, theme)
        assert len(reqs) >= 2

    def test_footnote(self):
        theme = _make_mock_theme()
        element = MagicMock()
        element.type = "footnote"
        element.content = {"text": "Source: Data Inc."}
        element.style_overrides = None
        pos = _make_position()

        reqs = build_text_requests("page_1", element, pos, theme)
        assert len(reqs) >= 2

    def test_unique_object_ids(self):
        theme = _make_mock_theme()
        element = MagicMock()
        element.type = "heading"
        element.content = {"text": "Test"}
        element.style_overrides = None
        pos = _make_position()

        reqs1 = build_text_requests("page_1", element, pos, theme)
        reqs2 = build_text_requests("page_1", element, pos, theme)
        # Extract objectIds
        ids1 = [r["createShape"]["objectId"] for r in reqs1 if "createShape" in r]
        ids2 = [r["createShape"]["objectId"] for r in reqs2 if "createShape" in r]
        assert ids1[0] != ids2[0]


class TestBuildBulletListRequests:
    def test_produces_bullets(self):
        theme = _make_mock_theme()
        element = MagicMock()
        element.type = "bullet_list"
        element.content = {"items": ["First", "Second", "Third"]}
        element.style_overrides = None
        pos = _make_position()

        reqs = build_bullet_list_requests("page_1", element, pos, theme)
        assert len(reqs) >= 2
        assert any("createShape" in r for r in reqs)
        # Should have bullet creation request
        assert any("createParagraphBullets" in r for r in reqs)


class TestBuildNumberedListRequests:
    def test_uses_numbered_preset(self):
        theme = _make_mock_theme()
        element = MagicMock()
        element.type = "numbered_list"
        element.content = {"items": ["Step 1", "Step 2"]}
        element.style_overrides = None
        pos = _make_position()

        reqs = build_numbered_list_requests("page_1", element, pos, theme)
        assert len(reqs) >= 2
        bullet_reqs = [r for r in reqs if "createParagraphBullets" in r]
        assert len(bullet_reqs) > 0
        preset = bullet_reqs[0]["createParagraphBullets"]["bulletPreset"]
        assert "NUMBERED" in preset


class TestBuildTableRequests:
    def test_creates_table(self):
        theme = _make_mock_theme()
        element = MagicMock()
        element.type = "table"
        element.content = {
            "headers": ["Name", "Value"],
            "rows": [["Apple", "10"], ["Banana", "20"]],
        }
        element.style_overrides = None
        pos = _make_position()

        reqs = build_table_requests("page_1", element, pos, theme)
        assert any("createTable" in r for r in reqs)


class TestBuildImageRequests:
    def test_creates_image(self):
        theme = _make_mock_theme()
        element = MagicMock()
        element.type = "image"
        element.content = {"url": "https://example.com/image.png"}
        element.style_overrides = None
        pos = _make_position()

        reqs = build_image_requests("page_1", element, pos, theme)
        assert any("createImage" in r for r in reqs)


class TestBuildShapeRequests:
    def test_creates_rectangle(self):
        theme = _make_mock_theme()
        element = MagicMock()
        element.type = "shape"
        element.content = {}
        element.style_overrides = None
        pos = _make_position()

        reqs = build_shape_requests("page_1", element, pos, theme)
        assert any("createShape" in r for r in reqs)


class TestBuildDividerRequests:
    def test_creates_line(self):
        theme = _make_mock_theme()
        element = MagicMock()
        element.type = "divider"
        element.content = {}
        element.style_overrides = None
        pos = _make_position()

        reqs = build_divider_requests("page_1", element, pos, theme)
        assert any("createLine" in r for r in reqs)


class TestBuildKpiCardRequests:
    def test_creates_shapes_and_text(self):
        theme = _make_mock_theme()
        element = MagicMock()
        element.type = "kpi_card"
        element.content = {"value": "$1.2M", "label": "Revenue", "change": "+15%"}
        element.style_overrides = None
        pos = _make_position()

        reqs = build_kpi_card_requests("page_1", element, pos, theme)
        assert len(reqs) >= 2


class TestBuildCalloutBoxRequests:
    def test_creates_shape_with_text(self):
        theme = _make_mock_theme()
        element = MagicMock()
        element.type = "callout_box"
        element.content = {"text": "Important note here"}
        element.style_overrides = None
        pos = _make_position()

        reqs = build_callout_box_requests("page_1", element, pos, theme)
        assert any("createShape" in r for r in reqs)
        assert any("insertText" in r for r in reqs)


class TestBuildPullQuoteRequests:
    def test_creates_quote_with_attribution(self):
        theme = _make_mock_theme()
        element = MagicMock()
        element.type = "pull_quote"
        element.content = {"text": "The best is yet to come.", "attribution": "Author"}
        element.style_overrides = None
        pos = _make_position()

        reqs = build_pull_quote_requests("page_1", element, pos, theme)
        assert any("createShape" in r for r in reqs)
        assert any("insertText" in r for r in reqs)
