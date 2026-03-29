"""DeckForge Layout Engine — grid system, constraint solver, and text measurement."""

from __future__ import annotations

from deckforge.layout.grid import GridSystem
from deckforge.layout.solver import SlideLayoutSolver
from deckforge.layout.text_measurer import TextMeasurer
from deckforge.layout.types import BoundingBox, LayoutRegion, LayoutResult, ResolvedPosition

__all__ = [
    "BoundingBox",
    "GridSystem",
    "LayoutRegion",
    "LayoutResult",
    "ResolvedPosition",
    "SlideLayoutSolver",
    "TextMeasurer",
]
