"""Layout type definitions: regions, bounding boxes, positions, and results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import kiwisolver

if TYPE_CHECKING:
    from deckforge.ir.slides.base import BaseSlide


# Tolerance for alignment checks: 2px at 72 DPI = 2/72 inches
DEFAULT_ALIGNMENT_TOLERANCE_INCHES = 2 / 72  # ~0.0278


@dataclass
class BoundingBox:
    """Measured bounding box in inches."""

    width_inches: float
    height_inches: float
    min_height: float | None = None


@dataclass
class ResolvedPosition:
    """Resolved absolute position in inches after constraint solving."""

    x: float
    y: float
    width: float
    height: float

    def is_aligned_to(
        self,
        other: ResolvedPosition,
        axis: str,
        tolerance_inches: float = DEFAULT_ALIGNMENT_TOLERANCE_INCHES,
    ) -> bool:
        """Check if this position is aligned with another on a given axis.

        Args:
            other: The other position to compare against.
            axis: One of "left", "top", "right", "bottom".
            tolerance_inches: Maximum allowed difference in inches (default 2px at 72 DPI).

        Returns:
            True if aligned within tolerance.
        """
        axis_values = {
            "left": (self.x, other.x),
            "top": (self.y, other.y),
            "right": (self.x + self.width, other.x + other.width),
            "bottom": (self.y + self.height, other.y + other.height),
        }
        if axis not in axis_values:
            raise ValueError(f"Unknown axis: {axis!r}. Must be one of {list(axis_values.keys())}")

        self_val, other_val = axis_values[axis]
        return abs(self_val - other_val) <= tolerance_inches


@dataclass
class LayoutResult:
    """Result of laying out a slide: positions for each element region."""

    slide: Any  # BaseSlide (avoid circular import)
    positions: dict[str, ResolvedPosition] = field(default_factory=dict)
    overflow: bool = False
    split_slides: list[Any] | None = None  # list[BaseSlide] for multi-slide split


class LayoutRegion:
    """Named region that creates kiwisolver Variables for constraint-based layout.

    Creates four kiwisolver Variables (left, top, width, height) and exposes
    derived properties (right, bottom) as kiwisolver expressions.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.left = kiwisolver.Variable(f"{name}_left")
        self.top = kiwisolver.Variable(f"{name}_top")
        self.width = kiwisolver.Variable(f"{name}_width")
        self.height = kiwisolver.Variable(f"{name}_height")

    @property
    def right(self) -> Any:
        """Right edge: left + width (kiwisolver expression)."""
        return self.left + self.width

    @property
    def bottom(self) -> Any:
        """Bottom edge: top + height (kiwisolver expression)."""
        return self.top + self.height

    def __repr__(self) -> str:
        return f"LayoutRegion({self.name!r})"
