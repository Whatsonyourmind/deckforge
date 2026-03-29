"""Capital structure slide renderer -- sources & uses tables side by side."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from deckforge.rendering.slide_renderers.base import BaseFinanceSlideRenderer

if TYPE_CHECKING:
    from pptx.slide import Slide

    from deckforge.ir.slides.base import BaseSlide
    from deckforge.themes.types import ResolvedTheme

logger = logging.getLogger(__name__)


class CapitalStructureRenderer(BaseFinanceSlideRenderer):
    """Renders capital structure with sources and uses tables.

    Fully implemented in Task 2.
    """

    def render(self, slide: Slide, ir_slide: BaseSlide, theme: ResolvedTheme) -> None:
        # Stub -- full implementation in Task 2
        logger.debug("CapitalStructureRenderer: stub render")


__all__ = ["CapitalStructureRenderer"]
