"""Section divider layout pattern — centered title and subtitle."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import kiwisolver

from deckforge.layout.patterns.base import BaseLayoutPattern
from deckforge.layout.types import BoundingBox, LayoutRegion

if TYPE_CHECKING:
    from deckforge.layout.grid import GridSystem
    from deckforge.themes.types import ResolvedTheme


class SectionDividerPattern(BaseLayoutPattern):
    """Layout for section dividers, key messages, and quote slides.

    Both title and subtitle centered horizontally and vertically in content area.
    Large title (h1 scale), smaller subtitle.

    Regions:
        - title: Centered, large.
        - subtitle: Centered, below title.
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

        title_meas = measurements.get("title", BoundingBox(width_inches=10.0, height_inches=1.2))
        subtitle_meas = measurements.get("subtitle", BoundingBox(width_inches=10.0, height_inches=0.5))

        # Full width for both
        constraints.extend(self._full_width_constraint(title, grid))
        constraints.extend(self._full_width_constraint(subtitle, grid))

        # Heights from measurements
        constraints.append(
            (title.height == title_meas.height_inches) | kiwisolver.strength.strong
        )
        constraints.append(
            (subtitle.height == subtitle_meas.height_inches) | kiwisolver.strength.strong
        )

        # Vertically center the title+subtitle block
        total_block_height = title_meas.height_inches + gap + subtitle_meas.height_inches
        block_top = grid.content_top + (grid.content_height - total_block_height) / 2
        constraints.append(
            (title.top == block_top) | kiwisolver.strength.medium
        )

        # Subtitle below title with section gap
        constraints.append(self._spacing_constraint(title, subtitle, gap))

        return constraints
