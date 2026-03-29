"""Tests for GridSystem: 12-column grid geometry for 16:9 slides."""

from __future__ import annotations

import pytest


class TestGridSystemDefaults:
    """GridSystem with default 16:9 dimensions (13.333in x 7.5in)."""

    def test_default_slide_dimensions(self):
        from deckforge.layout.grid import GridSystem

        grid = GridSystem()
        assert grid.SLIDE_WIDTH_INCHES == pytest.approx(13.333, abs=0.001)
        assert grid.SLIDE_HEIGHT_INCHES == pytest.approx(7.5)

    def test_default_margins(self):
        from deckforge.layout.grid import GridSystem

        grid = GridSystem()
        assert grid.margin_left == pytest.approx(0.5)
        assert grid.margin_right == pytest.approx(0.5)
        assert grid.margin_top == pytest.approx(0.5)
        assert grid.margin_bottom == pytest.approx(0.5)

    def test_content_width(self):
        """content_width = slide_width - margin_left - margin_right = 13.333 - 1.0 = 12.333."""
        from deckforge.layout.grid import GridSystem

        grid = GridSystem()
        assert grid.content_width == pytest.approx(12.333, abs=0.001)

    def test_content_height(self):
        """content_height = slide_height - margin_top - margin_bottom = 7.5 - 1.0 = 6.5."""
        from deckforge.layout.grid import GridSystem

        grid = GridSystem()
        assert grid.content_height == pytest.approx(6.5)

    def test_content_left_top(self):
        from deckforge.layout.grid import GridSystem

        grid = GridSystem()
        assert grid.content_left == pytest.approx(0.5)
        assert grid.content_top == pytest.approx(0.5)

    def test_content_right_bottom(self):
        from deckforge.layout.grid import GridSystem

        grid = GridSystem()
        assert grid.content_right == pytest.approx(12.833, abs=0.001)
        assert grid.content_bottom == pytest.approx(7.0)

    def test_num_columns(self):
        from deckforge.layout.grid import GridSystem

        grid = GridSystem()
        assert grid.NUM_COLUMNS == 12

    def test_gutter_spacing(self):
        from deckforge.layout.grid import GridSystem

        grid = GridSystem()
        assert grid.gutter == pytest.approx(0.167, abs=0.001)


class TestGridSystemColumnCalculations:
    """Column geometry: widths, positions, spans."""

    def test_column_left_first_column(self):
        """column_left(0) should return margin_left."""
        from deckforge.layout.grid import GridSystem

        grid = GridSystem()
        assert grid.column_left(0) == pytest.approx(0.5)

    def test_column_left_sixth_column(self):
        """column_left(6) accounts for 6 columns + 5 gutters from content_left."""
        from deckforge.layout.grid import GridSystem

        grid = GridSystem()
        # column_width = (content_width - 11*gutter) / 12
        # column_left(6) = content_left + 6*column_width + 6*gutter
        left = grid.column_left(6)
        assert left > grid.content_left
        assert left < grid.content_right

    def test_column_left_last_column(self):
        from deckforge.layout.grid import GridSystem

        grid = GridSystem()
        left = grid.column_left(11)
        assert left < grid.content_right

    def test_column_span_width_half(self):
        """Spanning 6 columns should give approximately half content area minus half a gutter."""
        from deckforge.layout.grid import GridSystem

        grid = GridSystem()
        half_width = grid.column_span_width(0, 6)
        # 6 columns + 5 internal gutters
        expected = 6 * grid.column_width + 5 * grid.gutter
        assert half_width == pytest.approx(expected, abs=0.001)

    def test_column_span_width_full(self):
        """Spanning all 12 columns should give the full content width."""
        from deckforge.layout.grid import GridSystem

        grid = GridSystem()
        full_width = grid.column_span_width(0, 12)
        assert full_width == pytest.approx(grid.content_width, abs=0.001)

    def test_column_span_width_single(self):
        """Spanning 1 column returns just the column width (no gutters)."""
        from deckforge.layout.grid import GridSystem

        grid = GridSystem()
        single = grid.column_span_width(0, 1)
        assert single == pytest.approx(grid.column_width, abs=0.001)

    def test_column_width_positive(self):
        from deckforge.layout.grid import GridSystem

        grid = GridSystem()
        assert grid.column_width > 0


class TestGridSystemThemeSpacing:
    """GridSystem with theme_spacing override."""

    def test_custom_margins(self):
        from deckforge.layout.grid import GridSystem

        grid = GridSystem(
            theme_spacing={
                "margin_left": 1.0,
                "margin_right": 1.0,
                "margin_top": 0.75,
                "margin_bottom": 0.75,
            }
        )
        assert grid.margin_left == pytest.approx(1.0)
        assert grid.margin_right == pytest.approx(1.0)
        assert grid.content_width == pytest.approx(11.333, abs=0.001)

    def test_custom_gutter(self):
        from deckforge.layout.grid import GridSystem

        grid = GridSystem(theme_spacing={"gutter": 0.25})
        assert grid.gutter == pytest.approx(0.25)

    def test_theme_spacing_partial_override(self):
        """Only overriding gutter leaves margins at defaults."""
        from deckforge.layout.grid import GridSystem

        grid = GridSystem(theme_spacing={"gutter": 0.2})
        assert grid.margin_left == pytest.approx(0.5)
        assert grid.gutter == pytest.approx(0.2)
