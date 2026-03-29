"""Base element renderer abstract class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pptx.slide import Slide

    from deckforge.ir.elements.base import BaseElement, Position
    from deckforge.themes.types import ResolvedTheme


class BaseElementRenderer(ABC):
    """Abstract base class for all element renderers."""

    @abstractmethod
    def render(
        self,
        slide: Slide,
        element: BaseElement,
        position: Position,
        theme: ResolvedTheme,
    ) -> None:
        """Render an element onto a python-pptx slide at the given position.

        Args:
            slide: The python-pptx Slide to render onto.
            element: The IR element model with content data.
            position: Resolved position (x, y, width, height) in inches.
            theme: Resolved theme for styling (colors, typography, spacing).
        """
