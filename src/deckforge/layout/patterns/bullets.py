"""Bullet points layout pattern — title, subtitle, bullets, footnote stack."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import kiwisolver

from deckforge.layout.patterns.base import BaseLayoutPattern
from deckforge.layout.types import BoundingBox, LayoutRegion

if TYPE_CHECKING:
    from deckforge.layout.grid import GridSystem
    from deckforge.themes.types import ResolvedTheme


class BulletPointsPattern(BaseLayoutPattern):
    """Layout for bullet point slides: vertical stack.

    Regions:
        - title: At top, full width.
        - subtitle: Below title (optional, gets 0 height if no measurement).
        - bullets: Fill middle space.
        - footnote: Anchored to bottom.
    """

    def create_regions(self) -> list[LayoutRegion]:
        return [
            LayoutRegion("title"),
            LayoutRegion("subtitle"),
            LayoutRegion("bullets"),
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
        subtitle = self._region_by_name(regions, "subtitle")
        bullets = self._region_by_name(regions, "bullets")
        footnote = self._region_by_name(regions, "footnote")
        assert all(r is not None for r in [title, subtitle, bullets, footnote])

        constraints = self._base_constraints(regions, grid)
        gap = theme.spacing.element_gap

        # All full width
        for region in regions:
            constraints.extend(self._full_width_constraint(region, grid))

        # Title at top
        constraints.append(
            (title.top == grid.content_top) | kiwisolver.strength.required
        )

        # Title height from measurement
        title_meas = measurements.get("title", BoundingBox(width_inches=10.0, height_inches=0.6))
        constraints.append(
            (title.height == title_meas.height_inches) | kiwisolver.strength.strong
        )

        # Subtitle below title
        constraints.append(self._spacing_constraint(title, subtitle, gap))

        # Subtitle height
        subtitle_meas = measurements.get("subtitle", BoundingBox(width_inches=10.0, height_inches=0.0))
        constraints.append(
            (subtitle.height == subtitle_meas.height_inches) | kiwisolver.strength.strong
        )

        # Bullets below subtitle
        constraints.append(self._spacing_constraint(subtitle, bullets, gap))

        # Bullets height from measurement (strong, can be overridden for adaptive)
        bullets_meas = measurements.get("bullets", BoundingBox(width_inches=10.0, height_inches=3.0))
        constraints.append(
            (bullets.height == bullets_meas.height_inches) | kiwisolver.strength.strong
        )

        # Footnote below bullets
        constraints.append(self._spacing_constraint(bullets, footnote, gap))

        # Footnote height
        footnote_meas = measurements.get("footnote", BoundingBox(width_inches=10.0, height_inches=0.3))
        constraints.append(
            (footnote.height == footnote_meas.height_inches) | kiwisolver.strength.strong
        )

        # Footnote anchored near bottom (medium, can flex)
        constraints.append(
            (footnote.bottom <= grid.content_bottom) | kiwisolver.strength.required
        )

        return constraints
