"""Investment thesis slide renderer -- numbered thesis points with risk/reward."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from deckforge.rendering.slide_renderers.base import BaseFinanceSlideRenderer

if TYPE_CHECKING:
    from pptx.slide import Slide

    from deckforge.ir.slides.base import BaseSlide
    from deckforge.themes.types import ResolvedTheme

logger = logging.getLogger(__name__)


class InvestmentThesisRenderer(BaseFinanceSlideRenderer):
    """Renders investment thesis with numbered points and optional risk table.

    Fully implemented in Task 2.
    """

    def render(self, slide: Slide, ir_slide: BaseSlide, theme: ResolvedTheme) -> None:
        # Stub -- full implementation in Task 2
        logger.debug("InvestmentThesisRenderer: stub render")


__all__ = ["InvestmentThesisRenderer"]
