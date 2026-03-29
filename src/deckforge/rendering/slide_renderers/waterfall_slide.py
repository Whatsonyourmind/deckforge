"""Waterfall chart slide renderer -- embeds Plotly waterfall image with title."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from deckforge.ir.elements.base import Position
from deckforge.rendering.chart_renderers.waterfall import WaterfallChartRenderer
from deckforge.rendering.slide_renderers.base import BaseFinanceSlideRenderer

if TYPE_CHECKING:
    from pptx.slide import Slide

    from deckforge.ir.slides.base import BaseSlide
    from deckforge.themes.types import ResolvedTheme

logger = logging.getLogger(__name__)

# Singleton chart renderer for delegation.
_waterfall_chart_renderer = WaterfallChartRenderer()


class WaterfallSlideRenderer(BaseFinanceSlideRenderer):
    """Renders a waterfall chart slide by delegating to WaterfallChartRenderer."""

    def render(self, slide: Slide, ir_slide: BaseSlide, theme: ResolvedTheme) -> None:
        elements = ir_slide.elements

        # Title
        title = self._find_heading(elements) or "Waterfall Chart"
        title_pos = Position(x=0.75, y=0.4, width=11.8, height=0.8)
        self._add_title(slide, title, theme, title_pos)

        # Find chart element
        chart_elem = self._find_chart_element(elements, chart_type="waterfall")
        if chart_elem is None:
            # Try any chart element
            chart_elem = self._find_chart_element(elements)

        if chart_elem is None:
            logger.warning("WaterfallSlideRenderer: No chart element found")
            return

        chart_data = chart_elem.chart_data
        chart_pos = Position(x=0.75, y=1.5, width=11.8, height=5.0)

        # Delegate to the static chart renderer
        _waterfall_chart_renderer.render(slide, chart_data, chart_pos, theme)


__all__ = ["WaterfallSlideRenderer"]
