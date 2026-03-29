"""Comp table slide renderer -- comparable companies analysis with financial formatting."""

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


class CompTableRenderer(BaseFinanceSlideRenderer):
    """Renders comp table slides with financial formatting, median row, and conditional coloring."""

    def render(self, slide: Slide, ir_slide: BaseSlide, theme: ResolvedTheme) -> None:
        elements = ir_slide.elements

        # Extract title
        title = self._find_heading(elements) or "Comparable Companies"
        title_pos = Position(x=0.75, y=0.4, width=11.8, height=0.8)
        self._add_title(slide, title, theme, title_pos)

        # Find table data
        table_elem = self._find_table_element(elements)
        if table_elem is None:
            logger.warning("CompTableRenderer: No table element found")
            return

        content = table_elem.content
        headers = content.headers
        rows = [list(row) for row in content.rows]

        # Infer column formats from headers
        column_formats = [_infer_format(h) for h in headers]

        # Sort if requested
        sort_by = getattr(ir_slide, "sort_by", None)
        if sort_by and sort_by in headers:
            sort_idx = headers.index(sort_by)
            rows.sort(
                key=lambda r: r[sort_idx] if isinstance(r[sort_idx], (int, float)) else 0,
                reverse=True,
            )

        # Identify numeric columns for median computation
        numeric_cols = [
            i for i, fmt in enumerate(column_formats) if fmt is not None
        ]

        # Compute median row
        median_row = self._compute_median_row(rows, numeric_cols)

        # Compute conditional cell colors (median highlight)
        cell_colors: dict[tuple[int, int], str] = {}
        if numeric_cols and median_row:
            for row_idx, row in enumerate(rows):
                for col_idx in numeric_cols:
                    if col_idx < len(row) and isinstance(row[col_idx], (int, float)):
                        median_val = median_row[col_idx] if col_idx < len(median_row) else None
                        if isinstance(median_val, (int, float)):
                            color = ConditionalFormatter.median_highlight(
                                row[col_idx], median_val, theme
                            )
                            cell_colors[(row_idx, col_idx)] = color

        # Highlight column if specified
        highlight_column = getattr(ir_slide, "highlight_column", None)
        if highlight_column and highlight_column in headers:
            col_idx = headers.index(highlight_column)
            for row_idx in range(len(rows)):
                cell_colors[(row_idx, col_idx)] = theme.colors.accent

        # Table position
        table_pos = Position(x=0.75, y=1.5, width=11.8, height=5.0)

        self._add_table(
            slide,
            headers=headers,
            rows=rows,
            theme=theme,
            position=table_pos,
            column_formats=column_formats,
            footer_row=median_row,
            cell_colors=cell_colors,
        )


__all__ = ["CompTableRenderer"]
