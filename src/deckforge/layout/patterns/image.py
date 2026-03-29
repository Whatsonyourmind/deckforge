"""Image with caption layout pattern — title, image area (70%), caption."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import kiwisolver

from deckforge.layout.patterns.base import BaseLayoutPattern
from deckforge.layout.types import BoundingBox, LayoutRegion

if TYPE_CHECKING:
    from deckforge.layout.grid import GridSystem
    from deckforge.themes.types import ResolvedTheme


class ImageWithCaptionPattern(BaseLayoutPattern):
    """Layout for image slides: title, large image area, caption below.

    Regions:
        - title: Full width at top.
        - image_area: 70% of remaining content height.
        - caption: Below image area.
    """

    def create_regions(self) -> list[LayoutRegion]:
        return [
            LayoutRegion("title"),
            LayoutRegion("image_area"),
            LayoutRegion("caption"),
        ]

    def create_constraints(
        self,
        regions: list[LayoutRegion],
        grid: GridSystem,
        measurements: dict[str, BoundingBox],
        theme: ResolvedTheme,
    ) -> list[Any]:
        title = self._region_by_name(regions, "title")
        image = self._region_by_name(regions, "image_area")
        caption = self._region_by_name(regions, "caption")
        assert all(r is not None for r in [title, image, caption])

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

        # Image area: full width, 70% of remaining content height
        constraints.extend(self._full_width_constraint(image, grid))
        constraints.append(self._spacing_constraint(title, image, gap))

        remaining_height = grid.content_height - title_meas.height_inches - gap * 2
        image_height = remaining_height * 0.7
        constraints.append(
            (image.height == image_height) | kiwisolver.strength.strong
        )

        # Caption: full width, below image
        constraints.extend(self._full_width_constraint(caption, grid))
        constraints.append(self._spacing_constraint(image, caption, gap))

        caption_meas = measurements.get("caption", BoundingBox(width_inches=10.0, height_inches=0.4))
        constraints.append(
            (caption.height == caption_meas.height_inches) | kiwisolver.strength.medium
        )
        constraints.append(
            (caption.bottom <= grid.content_bottom) | kiwisolver.strength.required
        )

        return constraints
