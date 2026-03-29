"""Returns analysis slide renderer -- IRR/MOIC returns matrix with scenario analysis."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from deckforge.finance.conditional import ConditionalFormatter
from deckforge.ir.elements.base import Position
from deckforge.rendering.slide_renderers.base import (
    BaseFinanceSlideRenderer,
    _infer_format,
)

if TYPE_CHECKING:
    from pptx.slide import Slide

    from deckforge.ir.slides.base import BaseSlide
    from deckforge.themes.types import ResolvedTheme

logger = logging.getLogger(__name__)

# IRR threshold for color-coding (20% = good).
_IRR_THRESHOLD = 0.20


class ReturnsAnalysisRenderer(BaseFinanceSlideRenderer):
    """Renders returns analysis with scenario table and conditional formatting."""

    def render(self, slide: Slide, ir_slide: BaseSlide, theme: ResolvedTheme) -> None:
        elements = ir_slide.elements

        # Title
        title = self._find_heading(elements) or "Returns Analysis"
        title_pos = Position(x=0.75, y=0.4, width=11.8, height=0.8)
        self._add_title(slide, title, theme, title_pos)

        # Find the returns table
        table_elem = self._find_table_element(elements)
        if table_elem is None:
            logger.warning("ReturnsAnalysisRenderer: No table element found")
            return

        content = table_elem.content
        headers = content.headers
        rows = [list(r) for r in content.rows]

        # Infer column formats
        column_formats = [_infer_format(h) for h in headers]

        # Apply conditional coloring for IRR column
        cell_colors: dict[tuple[int, int], str] = {}
        irr_col = None
        for i, h in enumerate(headers):
            if "irr" in h.lower():
                irr_col = i
                break

        if irr_col is not None:
            for row_idx, row in enumerate(rows):
                if irr_col < len(row) and isinstance(row[irr_col], (int, float)):
                    val = row[irr_col]
                    color = ConditionalFormatter.pos_neg_color(
                        val - _IRR_THRESHOLD, theme
                    )
                    # Use lightened version for background
                    from deckforge.finance.conditional import _lighten
                    cell_colors[(row_idx, irr_col)] = _lighten(color, factor=0.75)

        # Render
        table_pos = Position(x=0.75, y=1.5, width=11.8, height=4.0)
        self._add_table(
            slide,
            headers=headers,
            rows=rows,
            theme=theme,
            position=table_pos,
            column_formats=column_formats,
            cell_colors=cell_colors,
        )


__all__ = ["ReturnsAnalysisRenderer"]
