"""Tests for layout patterns — TDD RED phase.

Verifies:
- Every SlideType value has a pattern in the registry (no KeyError)
- Each pattern's create_regions returns non-empty list of LayoutRegion
- BulletPointsPattern constraints solve successfully with mock measurements
- TwoColumnPattern produces left_column.right < right_column.left (no overlap)
- Visual hierarchy: title region height > subtitle region height in solved output
"""

from __future__ import annotations

import pytest

from deckforge.ir.enums import SlideType
from deckforge.layout.grid import GridSystem
from deckforge.layout.solver import SlideLayoutSolver
from deckforge.layout.types import BoundingBox, LayoutRegion

# Imports from the patterns module (to be created)
from deckforge.layout.patterns import PATTERN_REGISTRY, get_pattern
from deckforge.layout.patterns.base import BaseLayoutPattern
from deckforge.layout.patterns.title import TitleSlidePattern
from deckforge.layout.patterns.bullets import BulletPointsPattern
from deckforge.layout.patterns.two_column import TwoColumnPattern
from deckforge.layout.patterns.chart import ChartSlidePattern
from deckforge.layout.patterns.table import TableSlidePattern
from deckforge.layout.patterns.section import SectionDividerPattern
from deckforge.layout.patterns.image import ImageWithCaptionPattern
from deckforge.layout.patterns.stats import StatsCalloutPattern
from deckforge.layout.patterns.generic import GenericPattern


def _make_default_theme():
    """Create a minimal ResolvedTheme for testing."""
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
                    "title": ComponentStyle(
                        font_family="Arial", font_size=36, font_weight=700
                    ),
                    "subtitle": ComponentStyle(
                        font_family="Arial", font_size=24, font_weight=600
                    ),
                    "bullets": ComponentStyle(
                        font_family="Calibri", font_size=18, font_weight=400
                    ),
                    "content": ComponentStyle(
                        font_family="Calibri", font_size=18, font_weight=400
                    ),
                    "footnote": ComponentStyle(
                        font_family="Calibri", font_size=10, font_weight=400
                    ),
                    "chart_area": ComponentStyle(min_height=4.0),
                },
            )
        },
    )


def _make_grid():
    """Create a default GridSystem for testing."""
    return GridSystem(
        margin_left=0.75,
        margin_right=0.75,
        margin_top=0.5,
        margin_bottom=0.5,
        gutter=0.3,
    )


# ────────────────────────────────────────────────────────────────────────────────
# Test: Every SlideType has a pattern in the registry
# ────────────────────────────────────────────────────────────────────────────────


class TestPatternRegistry:
    """Verify PATTERN_REGISTRY covers all 32 SlideType values."""

    def test_all_slide_types_registered(self):
        """Every SlideType value should map to a pattern class."""
        for slide_type in SlideType:
            assert slide_type.value in PATTERN_REGISTRY, (
                f"SlideType.{slide_type.name} ({slide_type.value}) "
                f"missing from PATTERN_REGISTRY"
            )

    def test_get_pattern_returns_instance(self):
        """get_pattern() should return an instance of BaseLayoutPattern."""
        for slide_type in SlideType:
            pattern = get_pattern(slide_type.value)
            assert isinstance(pattern, BaseLayoutPattern), (
                f"get_pattern({slide_type.value!r}) returned "
                f"{type(pattern).__name__}, expected BaseLayoutPattern subclass"
            )

    def test_specific_type_mappings(self):
        """Verify specific slide type -> pattern class mappings."""
        assert PATTERN_REGISTRY["title_slide"] is TitleSlidePattern
        assert PATTERN_REGISTRY["bullet_points"] is BulletPointsPattern
        assert PATTERN_REGISTRY["two_column_text"] is TwoColumnPattern
        assert PATTERN_REGISTRY["comparison"] is TwoColumnPattern
        assert PATTERN_REGISTRY["chart_slide"] is ChartSlidePattern
        assert PATTERN_REGISTRY["table_slide"] is TableSlidePattern
        assert PATTERN_REGISTRY["section_divider"] is SectionDividerPattern
        assert PATTERN_REGISTRY["key_message"] is SectionDividerPattern
        assert PATTERN_REGISTRY["image_with_caption"] is ImageWithCaptionPattern
        assert PATTERN_REGISTRY["stats_callout"] is StatsCalloutPattern
        assert PATTERN_REGISTRY["quote_slide"] is SectionDividerPattern

    def test_remaining_types_use_generic(self):
        """Remaining slide types should map to GenericPattern."""
        generic_types = [
            "agenda",
            "timeline",
            "process_flow",
            "org_chart",
            "team_slide",
            "icon_grid",
            "matrix",
            "funnel",
            "map_slide",
            "thank_you",
            "appendix",
            "q_and_a",
            # Finance
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
        for slide_type_val in generic_types:
            assert PATTERN_REGISTRY[slide_type_val] is GenericPattern, (
                f"{slide_type_val} should map to GenericPattern, "
                f"got {PATTERN_REGISTRY[slide_type_val].__name__}"
            )


# ────────────────────────────────────────────────────────────────────────────────
# Test: Each pattern creates non-empty regions
# ────────────────────────────────────────────────────────────────────────────────


class TestPatternRegions:
    """Verify create_regions() returns non-empty list of LayoutRegion."""

    @pytest.mark.parametrize(
        "pattern_cls",
        [
            TitleSlidePattern,
            BulletPointsPattern,
            TwoColumnPattern,
            ChartSlidePattern,
            TableSlidePattern,
            SectionDividerPattern,
            ImageWithCaptionPattern,
            StatsCalloutPattern,
            GenericPattern,
        ],
    )
    def test_create_regions_nonempty(self, pattern_cls):
        pattern = pattern_cls()
        regions = pattern.create_regions()
        assert len(regions) > 0
        for region in regions:
            assert isinstance(region, LayoutRegion)

    def test_title_pattern_has_two_regions(self):
        pattern = TitleSlidePattern()
        regions = pattern.create_regions()
        names = [r.name for r in regions]
        assert "title" in names
        assert "subtitle" in names

    def test_bullets_pattern_has_expected_regions(self):
        pattern = BulletPointsPattern()
        regions = pattern.create_regions()
        names = [r.name for r in regions]
        assert "title" in names
        assert "bullets" in names

    def test_two_column_pattern_has_columns(self):
        pattern = TwoColumnPattern()
        regions = pattern.create_regions()
        names = [r.name for r in regions]
        assert "title" in names
        assert "left_column" in names
        assert "right_column" in names

    def test_chart_pattern_has_chart_area(self):
        pattern = ChartSlidePattern()
        regions = pattern.create_regions()
        names = [r.name for r in regions]
        assert "title" in names
        assert "chart_area" in names

    def test_section_pattern_has_centered_regions(self):
        pattern = SectionDividerPattern()
        regions = pattern.create_regions()
        names = [r.name for r in regions]
        assert "title" in names
        assert "subtitle" in names

    def test_image_pattern_has_image_area(self):
        pattern = ImageWithCaptionPattern()
        regions = pattern.create_regions()
        names = [r.name for r in regions]
        assert "title" in names
        assert "image_area" in names
        assert "caption" in names

    def test_stats_pattern_has_stat_cards(self):
        pattern = StatsCalloutPattern()
        regions = pattern.create_regions()
        names = [r.name for r in regions]
        assert "title" in names
        assert "stat_cards" in names

    def test_generic_pattern_has_title_and_content(self):
        pattern = GenericPattern()
        regions = pattern.create_regions()
        names = [r.name for r in regions]
        assert "title" in names
        assert "content" in names


# ────────────────────────────────────────────────────────────────────────────────
# Test: BulletPointsPattern constraints solve successfully
# ────────────────────────────────────────────────────────────────────────────────


class TestBulletPointsConstraintSolving:
    """BulletPointsPattern constraints solve with mock measurements."""

    def test_constraints_solve_successfully(self):
        theme = _make_default_theme()
        grid = _make_grid()
        pattern = BulletPointsPattern()
        regions = pattern.create_regions()

        # Mock measurements: title=0.6in, bullets=3.0in, footnote=0.3in
        measurements = {
            "title": BoundingBox(width_inches=10.0, height_inches=0.6),
            "subtitle": BoundingBox(width_inches=10.0, height_inches=0.4),
            "bullets": BoundingBox(width_inches=10.0, height_inches=3.0),
            "footnote": BoundingBox(width_inches=10.0, height_inches=0.3),
        }

        constraints = pattern.create_constraints(regions, grid, measurements, theme)
        assert len(constraints) > 0

        solver = SlideLayoutSolver()
        solver.add_constraints(constraints)
        result = solver.solve(regions)

        assert result is not None, "BulletPointsPattern constraints should be satisfiable"
        for region in regions:
            pos = result[region.name]
            assert pos.width >= 0, f"{region.name} width should be >= 0"
            assert pos.height >= 0, f"{region.name} height should be >= 0"

    def test_bullet_positions_are_within_margins(self):
        theme = _make_default_theme()
        grid = _make_grid()
        pattern = BulletPointsPattern()
        regions = pattern.create_regions()

        measurements = {
            "title": BoundingBox(width_inches=10.0, height_inches=0.6),
            "subtitle": BoundingBox(width_inches=10.0, height_inches=0.4),
            "bullets": BoundingBox(width_inches=10.0, height_inches=3.0),
            "footnote": BoundingBox(width_inches=10.0, height_inches=0.3),
        }

        constraints = pattern.create_constraints(regions, grid, measurements, theme)
        solver = SlideLayoutSolver()
        solver.add_constraints(constraints)
        result = solver.solve(regions)
        assert result is not None

        for region in regions:
            pos = result[region.name]
            assert pos.x >= grid.content_left - 0.01, (
                f"{region.name} x={pos.x} < content_left={grid.content_left}"
            )
            assert pos.y >= grid.content_top - 0.01, (
                f"{region.name} y={pos.y} < content_top={grid.content_top}"
            )


# ────────────────────────────────────────────────────────────────────────────────
# Test: TwoColumnPattern columns don't overlap
# ────────────────────────────────────────────────────────────────────────────────


class TestTwoColumnNoOverlap:
    """TwoColumnPattern produces non-overlapping columns."""

    def test_columns_do_not_overlap(self):
        theme = _make_default_theme()
        grid = _make_grid()
        pattern = TwoColumnPattern()
        regions = pattern.create_regions()

        measurements = {
            "title": BoundingBox(width_inches=10.0, height_inches=0.6),
            "left_column": BoundingBox(width_inches=5.0, height_inches=3.0),
            "right_column": BoundingBox(width_inches=5.0, height_inches=3.0),
            "footnote": BoundingBox(width_inches=10.0, height_inches=0.3),
        }

        constraints = pattern.create_constraints(regions, grid, measurements, theme)
        solver = SlideLayoutSolver()
        solver.add_constraints(constraints)
        result = solver.solve(regions)
        assert result is not None

        left_pos = result["left_column"]
        right_pos = result["right_column"]

        # Left column's right edge must be less than right column's left edge
        left_right_edge = left_pos.x + left_pos.width
        assert left_right_edge <= right_pos.x + 0.01, (
            f"Left column right edge ({left_right_edge:.3f}) "
            f"overlaps right column left ({right_pos.x:.3f})"
        )


# ────────────────────────────────────────────────────────────────────────────────
# Test: Visual hierarchy (title region > subtitle region)
# ────────────────────────────────────────────────────────────────────────────────


class TestVisualHierarchy:
    """Visual hierarchy: title region gets larger height with larger text measurement."""

    def test_title_height_greater_than_subtitle(self):
        """Given larger title measurement, solved title height >= subtitle height."""
        theme = _make_default_theme()
        grid = _make_grid()
        pattern = TitleSlidePattern()
        regions = pattern.create_regions()

        # Title measurement larger than subtitle
        measurements = {
            "title": BoundingBox(width_inches=10.0, height_inches=1.2),
            "subtitle": BoundingBox(width_inches=10.0, height_inches=0.5),
        }

        constraints = pattern.create_constraints(regions, grid, measurements, theme)
        solver = SlideLayoutSolver()
        solver.add_constraints(constraints)
        result = solver.solve(regions)
        assert result is not None

        title_pos = result["title"]
        subtitle_pos = result["subtitle"]

        assert title_pos.height >= subtitle_pos.height, (
            f"Title height ({title_pos.height:.3f}) should be >= "
            f"subtitle height ({subtitle_pos.height:.3f})"
        )

    def test_base_constraints_enforce_positive_dimensions(self):
        """_base_constraints should ensure all widths/heights >= 0."""
        theme = _make_default_theme()
        grid = _make_grid()
        pattern = GenericPattern()
        regions = pattern.create_regions()

        measurements = {
            "title": BoundingBox(width_inches=10.0, height_inches=0.6),
            "content": BoundingBox(width_inches=10.0, height_inches=3.0),
        }

        constraints = pattern.create_constraints(regions, grid, measurements, theme)
        solver = SlideLayoutSolver()
        solver.add_constraints(constraints)
        result = solver.solve(regions)
        assert result is not None

        for region in regions:
            pos = result[region.name]
            assert pos.width >= -0.01, f"{region.name} width={pos.width} < 0"
            assert pos.height >= -0.01, f"{region.name} height={pos.height} < 0"
