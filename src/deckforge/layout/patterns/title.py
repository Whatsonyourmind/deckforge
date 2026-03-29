"""Title slide layout pattern — centered title and subtitle."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import kiwisolver

from deckforge.layout.patterns.base import BaseLayoutPattern
from deckforge.layout.types import BoundingBox, LayoutRegion

if TYPE_CHECKING:
    from deckforge.layout.grid import GridSystem
    from deckforge.themes.types import ResolvedTheme


class TitleSlidePattern(BaseLayoutPattern):
    """Layout for title slides: large centered title, subtitle below.

    Regions:
        - title: Centered in top 60% of content area, full width.
        - subtitle: Below title with section_gap spacing, centered.
    """

    def create_regions(self) -> list[LayoutRegion]:
        return [LayoutRegion("title"), LayoutRegion("subtitle")]

    def create_constraints(
        self,
        regions: list[LayoutRegion],
        grid: GridSystem,
        measurements: dict[str, BoundingBox],
        theme: ResolvedTheme,
    ) -> list[Any]:
        title = self._region_by_name(regions, "title")
        subtitle = self._region_by_name(regions, "subtitle")
        assert title is not None and subtitle is not None

        constraints = self._base_constraints(regions, grid)
        gap = theme.spacing.section_gap

        title_meas = measurements.get("title", BoundingBox(width_inches=10.0, height_inches=1.0))
        subtitle_meas = measurements.get("subtitle", BoundingBox(width_inches=10.0, height_inches=0.5))

        # Full width for both
        constraints.extend(self._full_width_constraint(title, grid))
        constraints.extend(self._full_width_constraint(subtitle, grid))

        # Title height from measurement (strong)
        constraints.append(
            (title.height == title_meas.height_inches) | kiwisolver.strength.strong
        )

        # Subtitle height from measurement (strong)
        constraints.append(
            (subtitle.height == subtitle_meas.height_inches) | kiwisolver.strength.strong
        )

        # Title centered vertically in top 60% of content area
        top_zone_height = grid.content_height * 0.6
        title_center_y = grid.content_top + (top_zone_height - title_meas.height_inches) / 2
        constraints.append(
            (title.top == title_center_y) | kiwisolver.strength.medium
        )

        # Subtitle below title with section gap
        constraints.append(self._spacing_constraint(title, subtitle, gap))

        return constraints
