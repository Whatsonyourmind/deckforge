"""Chart slide layout pattern — title, chart area with min_height, footnote."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import kiwisolver

from deckforge.layout.patterns.base import BaseLayoutPattern
from deckforge.layout.types import BoundingBox, LayoutRegion

if TYPE_CHECKING:
    from deckforge.layout.grid import GridSystem
    from deckforge.themes.types import ResolvedTheme


class ChartSlidePattern(BaseLayoutPattern):
    """Layout for chart slides: title, full-width chart area, footnote.

    Regions:
        - title: Full width at top.
        - chart_area: Full width, min_height from theme (default 4.0in).
        - footnote: Full width at bottom.
    """

    def create_regions(self) -> list[LayoutRegion]:
        return [
            LayoutRegion("title"),
            LayoutRegion("chart_area"),
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
        chart = self._region_by_name(regions, "chart_area")
        footnote = self._region_by_name(regions, "footnote")
        assert all(r is not None for r in [title, chart, footnote])

        constraints = self._base_constraints(regions, grid)
        gap = theme.spacing.element_gap

        # Title at top, full width
        constraints.extend(self._full_width_constraint(title, grid))
        constraints.append(
            (title.top == grid.content_top) | kiwisolver.strength.required
        )
        title_meas = measurements.get("title", BoundingBox(width_inches=10.0, height_inches=0.6))
        constraints.append(
            (title.height == title_meas.height_inches) | kiwisolver.strength.strong
        )

        # Chart area: full width, below title
        constraints.extend(self._full_width_constraint(chart, grid))
        constraints.append(self._spacing_constraint(title, chart, gap))

        # Min height from theme slide master (default 4.0in)
        min_height = 4.0
        # Try to get min_height from theme's slide master
        default_master = theme.slide_masters.get("default")
        if default_master:
            chart_style = default_master.regions.get("chart_area")
            if chart_style and chart_style.min_height is not None:
                min_height = chart_style.min_height

        chart_meas = measurements.get("chart_area", BoundingBox(width_inches=10.0, height_inches=min_height))
        actual_height = max(chart_meas.height_inches, min_height)
        constraints.append(
            (chart.height >= min_height) | kiwisolver.strength.strong
        )
        constraints.append(
            (chart.height == actual_height) | kiwisolver.strength.medium
        )

        # Footnote: full width at bottom
        constraints.extend(self._full_width_constraint(footnote, grid))
        footnote_meas = measurements.get("footnote", BoundingBox(width_inches=10.0, height_inches=0.3))
        constraints.append(
            (footnote.height == footnote_meas.height_inches) | kiwisolver.strength.strong
        )
        constraints.append(self._spacing_constraint(chart, footnote, gap))
        constraints.append(
            (footnote.bottom <= grid.content_bottom) | kiwisolver.strength.required
        )

        return constraints
