"""Tests for LayoutEngine orchestrator — TDD RED phase.

Verifies:
- layout_slide with a simple title slide returns positions for title and subtitle
- layout_slide with bullet_points returns positions for title, bullets, footnote
- layout_slide with short text returns overflow=False
- layout_slide with very long text triggers adaptive overflow
- layout_presentation processes multiple slides
- Resolved positions are applied to slide elements
"""

from __future__ import annotations

import pytest

from deckforge.layout.engine import LayoutEngine
from deckforge.layout.grid import GridSystem
from deckforge.layout.types import BoundingBox, LayoutResult


class MockTextMeasurer:
    """Mock TextMeasurer returning deterministic sizes based on text length."""

    def __init__(self, height_per_char: float = 0.01, overflow_threshold: int | None = None):
        self.height_per_char = height_per_char
        self.overflow_threshold = overflow_threshold

    def measure_text(
        self,
        text: str,
        font_name: str,
        size_pt: int = 14,
        max_width_inches: float | None = None,
    ) -> BoundingBox:
        # Scale height linearly with text length and font size
        base_height = len(text) * self.height_per_char * (size_pt / 14.0)
        base_height = max(base_height, 0.3)  # Minimum height
        return BoundingBox(width_inches=8.0, height_inches=base_height)

    def measure_bullet_list(
        self,
        items: list[str],
        font_name: str,
        size_pt: int = 14,
        max_width_inches: float = 10.0,
        line_spacing: float = 1.4,
    ) -> BoundingBox:
        height = len(items) * 0.35 * (size_pt / 14.0)
        return BoundingBox(width_inches=8.0, height_inches=height)


class MockThemeRegistry:
    """Mock ThemeRegistry that returns a test theme."""

    def get_theme(self, theme_id: str, brand_kit=None):
        return _make_test_theme()


def _make_test_theme():
    """Create a test ResolvedTheme."""
    from deckforge.themes.types import (
        ComponentStyle,
        ResolvedTheme,
        SlideMaster,
        ThemeColors,
        ThemeSpacing,
        ThemeTypography,
    )

    return ResolvedTheme(
        name="test-theme",
        description="Test theme",
        colors=ThemeColors(
            primary="#0066CC",
            secondary="#004499",
            accent="#FF6600",
            background="#FFFFFF",
            surface="#F5F5F5",
            text_primary="#222222",
            text_secondary="#555555",
            text_muted="#999999",
            positive="#00AA00",
            negative="#CC0000",
            warning="#FFAA00",
        ),
        typography=ThemeTypography(
            heading_family="Arial",
            body_family="Calibri",
            mono_family="Consolas",
            scale={
                "h1": 44,
                "h2": 36,
                "h3": 28,
                "subtitle": 24,
                "body": 18,
                "caption": 14,
                "footnote": 10,
            },
            weights={"heading": 700, "subtitle": 600, "body": 400, "caption": 400},
            line_height=1.4,
        ),
        spacing=ThemeSpacing(
            margin_top=0.5,
            margin_bottom=0.5,
            margin_left=0.75,
            margin_right=0.75,
            gutter=0.3,
            element_gap=0.2,
            section_gap=0.5,
        ),
        slide_masters={
            "default": SlideMaster(
                background="#FFFFFF",
                regions={
                    "title": ComponentStyle(font_family="Arial", font_size=36, font_weight=700),
                    "subtitle": ComponentStyle(font_family="Arial", font_size=24, font_weight=600),
                    "bullets": ComponentStyle(font_family="Calibri", font_size=18, font_weight=400),
                    "content": ComponentStyle(font_family="Calibri", font_size=18, font_weight=400),
                    "footnote": ComponentStyle(font_family="Calibri", font_size=10, font_weight=400),
                    "chart_area": ComponentStyle(min_height=4.0),
                },
            ),
        },
    )


def _make_title_slide():
    from deckforge.ir.elements.text import HeadingContent, HeadingElement, SubheadingContent, SubheadingElement
    from deckforge.ir.enums import HeadingLevel
    from deckforge.ir.slides.universal import TitleSlide

    return TitleSlide(
        elements=[
            HeadingElement(content=HeadingContent(text="Q3 Revenue Analysis", level=HeadingLevel.H1)),
            SubheadingElement(content=SubheadingContent(text="Financial Overview 2026")),
        ]
    )


def _make_bullet_slide(num_items: int = 5):
    from deckforge.ir.elements.text import (
        BulletListContent,
        BulletListElement,
        HeadingContent,
        HeadingElement,
    )
    from deckforge.ir.enums import HeadingLevel
    from deckforge.ir.slides.universal import BulletPointsSlide

    items = [f"Bullet point item {i} with some text content" for i in range(num_items)]
    return BulletPointsSlide(
        elements=[
            HeadingElement(content=HeadingContent(text="Key Findings", level=HeadingLevel.H2)),
            BulletListElement(content=BulletListContent(items=items)),
        ]
    )


# ────────────────────────────────────────────────────────────────────────────────
# Test: layout_slide with title slide
# ────────────────────────────────────────────────────────────────────────────────


class TestLayoutEngineTitle:
    """LayoutEngine.layout_slide with a title slide."""

    def test_title_slide_returns_positions(self):
        measurer = MockTextMeasurer()
        registry = MockThemeRegistry()
        engine = LayoutEngine(measurer, registry)
        theme = _make_test_theme()
        slide = _make_title_slide()

        result = engine.layout_slide(slide, theme)

        assert isinstance(result, LayoutResult)
        assert "title" in result.positions
        assert "subtitle" in result.positions

    def test_title_slide_no_overflow(self):
        measurer = MockTextMeasurer()
        registry = MockThemeRegistry()
        engine = LayoutEngine(measurer, registry)
        theme = _make_test_theme()
        slide = _make_title_slide()

        result = engine.layout_slide(slide, theme)
        assert result.overflow is False


# ────────────────────────────────────────────────────────────────────────────────
# Test: layout_slide with bullet points
# ────────────────────────────────────────────────────────────────────────────────


class TestLayoutEngineBullets:
    """LayoutEngine.layout_slide with bullet point slides."""

    def test_bullet_slide_returns_positions(self):
        measurer = MockTextMeasurer()
        registry = MockThemeRegistry()
        engine = LayoutEngine(measurer, registry)
        theme = _make_test_theme()
        slide = _make_bullet_slide(5)

        result = engine.layout_slide(slide, theme)

        assert isinstance(result, LayoutResult)
        assert "title" in result.positions
        assert "bullets" in result.positions

    def test_short_bullets_no_overflow(self):
        measurer = MockTextMeasurer()
        registry = MockThemeRegistry()
        engine = LayoutEngine(measurer, registry)
        theme = _make_test_theme()
        slide = _make_bullet_slide(3)

        result = engine.layout_slide(slide, theme)
        assert result.overflow is False

    def test_many_bullets_triggers_overflow(self):
        """20+ bullet items should trigger adaptive overflow."""
        # Use a measurer that makes bullets very tall
        measurer = MockTextMeasurer(height_per_char=0.05)
        registry = MockThemeRegistry()
        engine = LayoutEngine(measurer, registry)
        theme = _make_test_theme()
        slide = _make_bullet_slide(25)

        result = engine.layout_slide(slide, theme)
        # Either overflow is True, or split_slides is populated
        assert result.overflow is True or (result.split_slides is not None and len(result.split_slides) > 0)


# ────────────────────────────────────────────────────────────────────────────────
# Test: layout_presentation
# ────────────────────────────────────────────────────────────────────────────────


class TestLayoutPresentation:
    """LayoutEngine.layout_presentation processes multiple slides."""

    def test_layout_presentation_returns_results_per_slide(self):
        from deckforge.ir.metadata import PresentationMetadata
        from deckforge.ir.presentation import Presentation

        measurer = MockTextMeasurer()
        registry = MockThemeRegistry()
        engine = LayoutEngine(measurer, registry)

        presentation = Presentation(
            metadata=PresentationMetadata(title="Test Deck"),
            theme="executive-dark",
            slides=[_make_title_slide(), _make_bullet_slide(3)],
        )

        results = engine.layout_presentation(presentation)
        assert len(results) >= 2
        for r in results:
            assert isinstance(r, LayoutResult)


# ────────────────────────────────────────────────────────────────────────────────
# Test: Positions applied to slide elements
# ────────────────────────────────────────────────────────────────────────────────


class TestPositionsApplied:
    """Resolved positions are applied to slide elements."""

    def test_positions_set_on_elements(self):
        measurer = MockTextMeasurer()
        registry = MockThemeRegistry()
        engine = LayoutEngine(measurer, registry)
        theme = _make_test_theme()
        slide = _make_title_slide()

        result = engine.layout_slide(slide, theme)

        # At least one element should have a non-None position
        has_position = any(
            elem.position is not None and elem.position.x is not None
            for elem in result.slide.elements
        )
        assert has_position, "At least one element should have position set"
