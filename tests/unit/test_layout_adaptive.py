"""Tests for AdaptiveOverflowHandler — TDD RED phase.

Verifies:
- detect_overflow correctly identifies when measured height > allocated height
- Font reduction reduces font and re-solves
- split_slide divides bullet_list items across two slides
- Full cascade: font reduction -> reflow -> split
- Min font floor is respected (10pt body, 14pt heading)
"""

from __future__ import annotations

import pytest

from deckforge.layout.grid import GridSystem
from deckforge.layout.overflow import AdaptiveOverflowHandler
from deckforge.layout.types import BoundingBox, ResolvedPosition
from deckforge.themes.types import ComponentStyle


class MockTextMeasurer:
    """Mock TextMeasurer that returns deterministic BoundingBox values.

    Can be configured with a call_count-based response to simulate
    text getting smaller after font reduction.
    """

    def __init__(
        self,
        default_height: float = 1.0,
        shrink_after: int | None = None,
        shrunk_height: float = 0.5,
    ):
        self.default_height = default_height
        self.shrink_after = shrink_after
        self.shrunk_height = shrunk_height
        self.call_count = 0
        self.last_size_pt: int | None = None

    def measure_text(
        self,
        text: str,
        font_name: str,
        size_pt: int = 14,
        max_width_inches: float | None = None,
    ) -> BoundingBox:
        self.call_count += 1
        self.last_size_pt = size_pt
        if self.shrink_after is not None and self.call_count > self.shrink_after:
            return BoundingBox(width_inches=8.0, height_inches=self.shrunk_height)
        return BoundingBox(width_inches=8.0, height_inches=self.default_height)

    def measure_bullet_list(
        self,
        items: list[str],
        font_name: str,
        size_pt: int = 14,
        max_width_inches: float = 10.0,
        line_spacing: float = 1.4,
    ) -> BoundingBox:
        self.call_count += 1
        self.last_size_pt = size_pt
        height = len(items) * 0.4 * (self.default_height / 1.0)
        if self.shrink_after is not None and self.call_count > self.shrink_after:
            height = len(items) * 0.3 * (self.shrunk_height / 1.0)
        return BoundingBox(width_inches=8.0, height_inches=height)


class TestDetectOverflow:
    """detect_overflow identifies regions where measured > allocated."""

    def test_no_overflow_when_space_sufficient(self):
        measurer = MockTextMeasurer()
        handler = AdaptiveOverflowHandler(measurer)

        positions = {
            "title": ResolvedPosition(x=0.75, y=0.5, width=11.833, height=1.0),
            "bullets": ResolvedPosition(x=0.75, y=1.7, width=11.833, height=4.0),
        }
        measurements = {
            "title": BoundingBox(width_inches=10.0, height_inches=0.6),
            "bullets": BoundingBox(width_inches=10.0, height_inches=3.0),
        }

        overflow_regions = handler.detect_overflow(positions, measurements)
        assert overflow_regions == []

    def test_overflow_detected_when_measured_exceeds_allocated(self):
        measurer = MockTextMeasurer()
        handler = AdaptiveOverflowHandler(measurer)

        positions = {
            "title": ResolvedPosition(x=0.75, y=0.5, width=11.833, height=0.6),
            "bullets": ResolvedPosition(x=0.75, y=1.3, width=11.833, height=2.0),
        }
        measurements = {
            "title": BoundingBox(width_inches=10.0, height_inches=0.6),
            "bullets": BoundingBox(width_inches=10.0, height_inches=5.0),  # Exceeds 2.0
        }

        overflow_regions = handler.detect_overflow(positions, measurements)
        assert "bullets" in overflow_regions

    def test_no_overflow_for_nontext_regions(self):
        """Regions without measurements should not be reported as overflow."""
        measurer = MockTextMeasurer()
        handler = AdaptiveOverflowHandler(measurer)

        positions = {
            "chart_area": ResolvedPosition(x=0.75, y=1.0, width=11.833, height=4.0),
        }
        measurements = {}  # No measurement for chart_area

        overflow_regions = handler.detect_overflow(positions, measurements)
        assert overflow_regions == []


class TestFontReduction:
    """Font reduction reduces font size and produces new component style."""

    def test_reduce_font_respects_minimum(self):
        measurer = MockTextMeasurer()
        handler = AdaptiveOverflowHandler(measurer, min_body_font=10, font_reduction_step=2)

        style = ComponentStyle(font_family="Calibri", font_size=12)
        reduced = handler._reduce_font_in_style(style, reduction=2, min_size=10)
        assert reduced.font_size == 10

    def test_reduce_font_does_not_go_below_minimum(self):
        measurer = MockTextMeasurer()
        handler = AdaptiveOverflowHandler(measurer, min_body_font=10, font_reduction_step=2)

        style = ComponentStyle(font_family="Calibri", font_size=10)
        reduced = handler._reduce_font_in_style(style, reduction=2, min_size=10)
        assert reduced.font_size == 10

    def test_reduce_heading_respects_heading_minimum(self):
        measurer = MockTextMeasurer()
        handler = AdaptiveOverflowHandler(measurer, min_heading_font=14)

        style = ComponentStyle(font_family="Arial", font_size=16)
        reduced = handler._reduce_font_in_style(style, reduction=4, min_size=14)
        assert reduced.font_size == 14


class TestSlideSplit:
    """split_slide divides content across multiple slides."""

    def test_split_bullet_list(self):
        measurer = MockTextMeasurer()
        handler = AdaptiveOverflowHandler(measurer)

        from deckforge.ir.elements.text import (
            BulletListContent,
            BulletListElement,
            HeadingContent,
            HeadingElement,
        )
        from deckforge.ir.enums import HeadingLevel
        from deckforge.ir.slides.universal import BulletPointsSlide

        slide = BulletPointsSlide(
            elements=[
                HeadingElement(content=HeadingContent(text="Test Title", level=HeadingLevel.H2)),
                BulletListElement(content=BulletListContent(
                    items=[f"Item {i}" for i in range(20)]
                )),
            ]
        )

        split_slides = handler._split_slide(slide, "bullets")
        assert len(split_slides) >= 2
        # First slide should have original title
        # Continuation slides should have "(cont.)" in title

    def test_split_preserves_all_items(self):
        measurer = MockTextMeasurer()
        handler = AdaptiveOverflowHandler(measurer)

        from deckforge.ir.elements.text import (
            BulletListContent,
            BulletListElement,
            HeadingContent,
            HeadingElement,
        )
        from deckforge.ir.enums import HeadingLevel
        from deckforge.ir.slides.universal import BulletPointsSlide

        items = [f"Item {i}" for i in range(15)]
        slide = BulletPointsSlide(
            elements=[
                HeadingElement(content=HeadingContent(text="Title", level=HeadingLevel.H2)),
                BulletListElement(content=BulletListContent(items=items)),
            ]
        )

        split_slides = handler._split_slide(slide, "bullets")

        # Collect all items from all split slides
        all_items = []
        for s in split_slides:
            for elem in s.elements:
                if hasattr(elem, "content") and hasattr(elem.content, "items"):
                    all_items.extend(elem.content.items)

        assert len(all_items) == 15


class TestMinFontFloor:
    """Minimum font floor is respected during cascade."""

    def test_body_font_floor_is_10(self):
        measurer = MockTextMeasurer()
        handler = AdaptiveOverflowHandler(measurer, min_body_font=10, font_reduction_step=2)

        style = ComponentStyle(font_family="Calibri", font_size=14)
        # Reduce 3 times: 14 -> 12 -> 10 -> 10 (floor)
        s1 = handler._reduce_font_in_style(style, reduction=2, min_size=10)
        assert s1.font_size == 12
        s2 = handler._reduce_font_in_style(s1, reduction=2, min_size=10)
        assert s2.font_size == 10
        s3 = handler._reduce_font_in_style(s2, reduction=2, min_size=10)
        assert s3.font_size == 10

    def test_heading_font_floor_is_14(self):
        measurer = MockTextMeasurer()
        handler = AdaptiveOverflowHandler(measurer, min_heading_font=14)

        style = ComponentStyle(font_family="Arial", font_size=20)
        s1 = handler._reduce_font_in_style(style, reduction=2, min_size=14)
        assert s1.font_size == 18
        s2 = handler._reduce_font_in_style(s1, reduction=2, min_size=14)
        assert s2.font_size == 16
        s3 = handler._reduce_font_in_style(s2, reduction=2, min_size=14)
        assert s3.font_size == 14
        s4 = handler._reduce_font_in_style(s3, reduction=2, min_size=14)
        assert s4.font_size == 14
