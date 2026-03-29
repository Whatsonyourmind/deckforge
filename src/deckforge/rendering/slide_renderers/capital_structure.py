"""Capital structure slide renderer -- sources & uses tables side by side."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

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


class CapitalStructureRenderer(BaseFinanceSlideRenderer):
    """Renders capital structure with sources and uses tables side by side."""

    def render(self, slide: Slide, ir_slide: BaseSlide, theme: ResolvedTheme) -> None:
        elements = ir_slide.elements

        # Title
        title = self._find_heading(elements) or "Capital Structure"
        title_pos = Position(x=0.75, y=0.4, width=11.8, height=0.8)
        self._add_title(slide, title, theme, title_pos)

        # Find table elements (expect 2: sources and uses)
        tables = self._find_table_elements(elements)
        if not tables:
            logger.warning("CapitalStructureRenderer: No table elements found")
            return

        # Render tables side by side
        positions = [
            Position(x=0.75, y=1.5, width=5.5, height=4.0),
            Position(x=7.0, y=1.5, width=5.5, height=4.0),
        ]

        for idx, tbl in enumerate(tables[:2]):
            content = tbl.content
            col_formats = [_infer_format(h) for h in content.headers]
            pos = positions[idx] if idx < len(positions) else positions[-1]

            self._add_table(
                slide,
                headers=content.headers,
                rows=[list(r) for r in content.rows],
                theme=theme,
                position=pos,
                column_formats=col_formats,
                footer_row=list(content.footer_row) if content.footer_row else None,
            )


__all__ = ["CapitalStructureRenderer"]
