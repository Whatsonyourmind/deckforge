"""Base layout pattern ABC — defines the contract for all slide layout patterns."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import kiwisolver

from deckforge.layout.types import BoundingBox, LayoutRegion

if TYPE_CHECKING:
    from deckforge.layout.grid import GridSystem
    from deckforge.themes.types import ResolvedTheme


class BaseLayoutPattern(ABC):
    """Abstract base for slide layout patterns.

    Each pattern defines:
    - Which regions exist on the slide (create_regions)
    - What constraints govern their positions (create_constraints)

    Constraints are kiwisolver constraint objects that the SlideLayoutSolver
    will solve to produce ResolvedPosition values.
    """

    @abstractmethod
    def create_regions(self) -> list[LayoutRegion]:
        """Create the named regions for this layout pattern.

        Returns:
            List of LayoutRegion, each with kiwisolver variables.
        """

    @abstractmethod
    def create_constraints(
        self,
        regions: list[LayoutRegion],
        grid: GridSystem,
        measurements: dict[str, BoundingBox],
        theme: ResolvedTheme,
    ) -> list[Any]:
        """Create kiwisolver constraints for the given regions.

        Args:
            regions: Regions created by create_regions().
            grid: GridSystem providing content area geometry.
            measurements: Measured BoundingBox for each region name.
            theme: ResolvedTheme with spacing, typography.

        Returns:
            List of kiwisolver constraint objects.
        """

    def _region_by_name(self, regions: list[LayoutRegion], name: str) -> LayoutRegion | None:
        """Find a region by name, or None."""
        for r in regions:
            if r.name == name:
                return r
        return None

    def _base_constraints(
        self,
        regions: list[LayoutRegion],
        grid: GridSystem,
    ) -> list[Any]:
        """Common constraints for all patterns.

        - All regions within content area margins.
        - All widths >= 0.
        - All heights >= 0.
        """
        constraints: list[Any] = []

        for region in regions:
            # Width and height non-negative (required)
            constraints.append(
                (region.width >= 0) | kiwisolver.strength.required
            )
            constraints.append(
                (region.height >= 0) | kiwisolver.strength.required
            )

            # Within content area (required)
            constraints.append(
                (region.left >= grid.content_left) | kiwisolver.strength.required
            )
            constraints.append(
                (region.top >= grid.content_top) | kiwisolver.strength.required
            )
            constraints.append(
                (region.right <= grid.content_right) | kiwisolver.strength.required
            )
            constraints.append(
                (region.bottom <= grid.content_bottom) | kiwisolver.strength.required
            )

        return constraints

    def _spacing_constraint(
        self,
        upper: LayoutRegion,
        lower: LayoutRegion,
        gap: float,
        strength: float = kiwisolver.strength.strong,
    ) -> Any:
        """Constraint: lower.top == upper.bottom + gap."""
        return (lower.top == upper.bottom + gap) | strength

    def _full_width_constraint(
        self,
        region: LayoutRegion,
        grid: GridSystem,
    ) -> list[Any]:
        """Constrain region to full content width."""
        return [
            (region.left == grid.content_left) | kiwisolver.strength.strong,
            (region.width == grid.content_width) | kiwisolver.strength.strong,
        ]
