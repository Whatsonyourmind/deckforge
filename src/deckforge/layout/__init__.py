"""DeckForge Layout Engine — grid system, constraint solver, text measurement, patterns, and engine."""

from __future__ import annotations

from deckforge.layout.engine import LayoutEngine
from deckforge.layout.grid import GridSystem
from deckforge.layout.overflow import AdaptiveOverflowHandler
from deckforge.layout.patterns import PATTERN_REGISTRY, get_pattern
from deckforge.layout.solver import SlideLayoutSolver
from deckforge.layout.text_measurer import TextMeasurer
from deckforge.layout.types import BoundingBox, LayoutRegion, LayoutResult, ResolvedPosition

__all__ = [
    "AdaptiveOverflowHandler",
    "BoundingBox",
    "GridSystem",
    "LayoutEngine",
    "LayoutRegion",
    "LayoutResult",
    "PATTERN_REGISTRY",
    "ResolvedPosition",
    "SlideLayoutSolver",
    "TextMeasurer",
    "get_pattern",
]
