"""Risk matrix slide renderer -- color-coded probability/impact grid."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from deckforge.finance.conditional import ConditionalFormatter
from deckforge.ir.elements.base import Position
from deckforge.rendering.slide_renderers.base import BaseFinanceSlideRenderer

if TYPE_CHECKING:
    from pptx.slide import Slide

    from deckforge.ir.slides.base import BaseSlide
    from deckforge.themes.types import ResolvedTheme

logger = logging.getLogger(__name__)

# Default axis labels and levels.
_DEFAULT_LEVELS = ["Very Low", "Low", "Medium", "High", "Very High"]
_LEVEL_MAP = {
    "very low": 0, "low": 1, "medium": 2, "high": 3, "very high": 4,
}


class RiskMatrixRenderer(BaseFinanceSlideRenderer):
    """Renders risk matrix as a color-coded grid with impact/likelihood axes."""

    def render(self, slide: Slide, ir_slide: BaseSlide, theme: ResolvedTheme) -> None:
        elements = ir_slide.elements

        # Title
        title = self._find_heading(elements) or "Risk Assessment Matrix"
        title_pos = Position(x=0.75, y=0.4, width=11.8, height=0.8)
        self._add_title(slide, title, theme, title_pos)

        # Axis labels
        axes_labels = getattr(ir_slide, "axes_labels", None) or {}
        x_label = axes_labels.get("x", "Likelihood")
        y_label = axes_labels.get("y", "Impact")

        # Find risk items from a table element
        table_elem = self._find_table_element(elements)
        risk_items: list[tuple[str, int, int]] = []  # (name, likelihood_idx, impact_idx)

        if table_elem:
            content = table_elem.content
            headers_lower = [h.lower() for h in content.headers]

            # Find likelihood and impact columns
            likelihood_col = None
            impact_col = None
            name_col = 0

            for i, h in enumerate(headers_lower):
                if "likelihood" in h or "probability" in h:
                    likelihood_col = i
                elif "impact" in h or "severity" in h:
                    impact_col = i
                elif "risk" in h or "name" in h:
                    name_col = i

            if likelihood_col is not None and impact_col is not None:
                for row in content.rows:
                    name = str(row[name_col]) if name_col < len(row) else ""
                    l_val = str(row[likelihood_col]).lower() if likelihood_col < len(row) else ""
                    i_val = str(row[impact_col]).lower() if impact_col < len(row) else ""
                    l_idx = _LEVEL_MAP.get(l_val, 2)
                    i_idx = _LEVEL_MAP.get(i_val, 2)
                    risk_items.append((name, l_idx, i_idx))

        # Build 5x5 grid
        grid_size = 5
        levels = _DEFAULT_LEVELS
        # Impact rows go from high (top) to low (bottom)
        impact_levels = list(reversed(levels))

        # Grid data: row_idx -> col_idx -> list of risk names
        grid: dict[tuple[int, int], list[str]] = {}
        for name, l_idx, i_idx in risk_items:
            # Row: impact (reversed: 4=VeryHigh at row 0, 0=VeryLow at row 4)
            row = grid_size - 1 - i_idx
            col = l_idx
            grid.setdefault((row, col), []).append(name)

        # Build table headers: empty corner + likelihood levels
        headers = [y_label] + levels  # y_label as corner header
        rows: list[list[str]] = []

        for row_idx in range(grid_size):
            row_data: list[str] = [impact_levels[row_idx]]
            for col_idx in range(grid_size):
                items = grid.get((row_idx, col_idx), [])
                row_data.append("\n".join(items) if items else "")
            rows.append(row_data)

        # Cell colors: higher combined index = higher risk = redder
        max_combined = (grid_size - 1) * 2  # max row + col risk score
        cell_colors: dict[tuple[int, int], str] = {}
        for row_idx in range(grid_size):
            for col_idx in range(grid_size):
                # risk_score: high impact (low row_idx) + high likelihood (high col_idx)
                impact_score = grid_size - 1 - row_idx  # 0 = low impact, 4 = high impact
                likelihood_score = col_idx  # 0 = low likelihood, 4 = high likelihood
                combined = impact_score + likelihood_score
                color = ConditionalFormatter.heatmap_gradient(
                    combined, 0, max_combined, theme
                )
                cell_colors[(row_idx, col_idx + 1)] = color  # +1 for row header offset

        # Render
        table_pos = Position(x=0.75, y=1.5, width=11.8, height=5.0)
        self._add_table(
            slide,
            headers=headers,
            rows=rows,
            theme=theme,
            position=table_pos,
            cell_colors=cell_colors,
        )


__all__ = ["RiskMatrixRenderer"]
