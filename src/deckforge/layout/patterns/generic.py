"""Generic fallback layout pattern — title and content."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import kiwisolver

from deckforge.layout.patterns.base import BaseLayoutPattern
from deckforge.layout.types import BoundingBox, LayoutRegion

if TYPE_CHECKING:
    from deckforge.layout.grid import GridSystem
    from deckforge.themes.types import ResolvedTheme


class GenericPattern(BaseLayoutPattern):
    """Fallback layout for any slide type without a dedicated pattern.

    Simple two-region layout: title at top, content fills remaining space.

    Regions:
        - title: Full width at top.
        - content: Full width, fills remaining content area.
    """

    def create_regions(self) -> list[LayoutRegion]:
        return [LayoutRegion("title"), LayoutRegion("content")]

    def create_constraints(
        self,
        regions: list[LayoutRegion],
        grid: GridSystem,
        measurements: dict[str, BoundingBox],
        theme: ResolvedTheme,
    ) -> list[Any]:
        title = self._region_by_name(regions, "title")
        content = self._region_by_name(regions, "content")
        assert title is not None and content is not None

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

        # Content: full width, fills remaining space
        constraints.extend(self._full_width_constraint(content, grid))
        constraints.append(self._spacing_constraint(title, content, gap))

        content_meas = measurements.get("content", BoundingBox(width_inches=10.0, height_inches=4.0))
        constraints.append(
            (content.height == content_meas.height_inches) | kiwisolver.strength.medium
        )
        constraints.append(
            (content.bottom <= grid.content_bottom) | kiwisolver.strength.required
        )

        return constraints
