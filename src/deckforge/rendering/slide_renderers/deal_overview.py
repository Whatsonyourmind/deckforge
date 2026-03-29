"""Deal overview slide renderer -- one-pager with key metrics and traffic lights."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from deckforge.rendering.slide_renderers.base import BaseFinanceSlideRenderer

if TYPE_CHECKING:
    from pptx.slide import Slide

    from deckforge.ir.slides.base import BaseSlide
    from deckforge.themes.types import ResolvedTheme

logger = logging.getLogger(__name__)


class DealOverviewRenderer(BaseFinanceSlideRenderer):
    """Renders deal overview one-pager with metrics grid and traffic-light indicators.

    Fully implemented in Task 2.
    """

    def render(self, slide: Slide, ir_slide: BaseSlide, theme: ResolvedTheme) -> None:
        # Stub -- full implementation in Task 2
        logger.debug("DealOverviewRenderer: stub render")


__all__ = ["DealOverviewRenderer"]
