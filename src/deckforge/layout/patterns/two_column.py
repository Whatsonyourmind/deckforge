"""Two-column layout pattern — title, left column, right column, footnote."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import kiwisolver

from deckforge.layout.patterns.base import BaseLayoutPattern
from deckforge.layout.types import BoundingBox, LayoutRegion

if TYPE_CHECKING:
    from deckforge.layout.grid import GridSystem
    from deckforge.themes.types import ResolvedTheme


class TwoColumnPattern(BaseLayoutPattern):
    """Layout for two-column slides (comparison, side-by-side text).

    Regions:
        - title: Full width at top.
        - left_column: 6 grid columns, left side.
        - right_column: 6 grid columns, right side.
        - footnote: Full width at bottom.
    """

    def create_regions(self) -> list[LayoutRegion]:
        return [
            LayoutRegion("title"),
            LayoutRegion("left_column"),
            LayoutRegion("right_column"),
            LayoutRegion("footnote"),
        ]

    def create_constraints(
        self,
        regions: list[LayoutRegion],
        grid: GridSystem,
        measurements: dict[str, BoundingBox],
        theme: ResolvedTheme,
    ) -> list[Any]:
        title = self._region_by_name(regions, "title")
        left = self._region_by_name(regions, "left_column")
        right = self._region_by_name(regions, "right_column")
        footnote = self._region_by_name(regions, "footnote")
        assert all(r is not None for r in [title, left, right, footnote])

        constraints = self._base_constraints(regions, grid)
        gap = theme.spacing.element_gap
        gutter = theme.spacing.gutter

        # Title: full width at top
        constraints.extend(self._full_width_constraint(title, grid))
        constraints.append(
            (title.top == grid.content_top) | kiwisolver.strength.required
        )
        title_meas = measurements.get("title", BoundingBox(width_inches=10.0, height_inches=0.6))
        constraints.append(
            (title.height == title_meas.height_inches) | kiwisolver.strength.strong
        )

        # Both columns below title
        col_top = title.bottom + gap
        constraints.append(
            (left.top == col_top) | kiwisolver.strength.strong
        )
        constraints.append(
            (right.top == col_top) | kiwisolver.strength.strong
        )

        # Column widths: 6 grid columns each
        left_width = grid.column_span_width(0, 6)
        right_width = grid.column_span_width(6, 6)

        constraints.append(
            (left.left == grid.content_left) | kiwisolver.strength.required
        )
        constraints.append(
            (left.width == left_width) | kiwisolver.strength.strong
        )

        constraints.append(
            (right.left == grid.column_left(6)) | kiwisolver.strength.required
        )
        constraints.append(
            (right.width == right_width) | kiwisolver.strength.strong
        )

        # Equal column heights (strong)
        constraints.append(
            (left.height == right.height) | kiwisolver.strength.medium
        )

        # Column heights from measurements (medium - can flex)
        left_meas = measurements.get("left_column", BoundingBox(width_inches=5.0, height_inches=3.0))
        right_meas = measurements.get("right_column", BoundingBox(width_inches=5.0, height_inches=3.0))
        max_col_height = max(left_meas.height_inches, right_meas.height_inches)
        constraints.append(
            (left.height == max_col_height) | kiwisolver.strength.medium
        )

        # Footnote: full width, below columns
        constraints.extend(self._full_width_constraint(footnote, grid))
        footnote_meas = measurements.get("footnote", BoundingBox(width_inches=10.0, height_inches=0.3))
        constraints.append(
            (footnote.height == footnote_meas.height_inches) | kiwisolver.strength.strong
        )
        constraints.append(
            (footnote.top >= left.bottom + gap) | kiwisolver.strength.strong
        )
        constraints.append(
            (footnote.bottom <= grid.content_bottom) | kiwisolver.strength.required
        )

        return constraints
