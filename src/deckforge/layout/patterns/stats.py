"""Stats callout layout pattern — title and stat cards region."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import kiwisolver

from deckforge.layout.patterns.base import BaseLayoutPattern
from deckforge.layout.types import BoundingBox, LayoutRegion

if TYPE_CHECKING:
    from deckforge.layout.grid import GridSystem
    from deckforge.themes.types import ResolvedTheme


class StatsCalloutPattern(BaseLayoutPattern):
    """Layout for stats/KPI slides: title and stat cards region.

    The stat_cards region is full width below the title. The renderer
    subdivides it internally into individual stat cards.

    Regions:
        - title: Full width at top.
        - stat_cards: Full width below title, fills remaining space.
    """

    def create_regions(self) -> list[LayoutRegion]:
        return [LayoutRegion("title"), LayoutRegion("stat_cards")]

    def create_constraints(
        self,
        regions: list[LayoutRegion],
        grid: GridSystem,
        measurements: dict[str, BoundingBox],
        theme: ResolvedTheme,
    ) -> list[Any]:
        title = self._region_by_name(regions, "title")
        stats = self._region_by_name(regions, "stat_cards")
        assert title is not None and stats is not None

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

        # Stat cards: full width, fills remaining space below title
        constraints.extend(self._full_width_constraint(stats, grid))
        constraints.append(self._spacing_constraint(title, stats, gap))

        stats_meas = measurements.get("stat_cards", BoundingBox(width_inches=10.0, height_inches=4.0))
        constraints.append(
            (stats.height == stats_meas.height_inches) | kiwisolver.strength.medium
        )
        constraints.append(
            (stats.bottom <= grid.content_bottom) | kiwisolver.strength.required
        )

        return constraints
