"""Static chart renderer base -- Plotly-based PNG image charts embedded in PPTX."""

from __future__ import annotations

from abc import abstractmethod
from io import BytesIO
from typing import TYPE_CHECKING

import plotly.graph_objects as go
from pptx.util import Inches

from deckforge.rendering.chart_renderers.base import BaseChartRenderer

if TYPE_CHECKING:
    from pptx.slide import Slide

    from deckforge.ir.elements.base import Position
    from deckforge.themes.types import ResolvedTheme


class StaticChartRenderer(BaseChartRenderer):
    """Base class for Plotly-based static chart renderers.

    Subclasses implement _build_figure() to create a Plotly figure.
    This base class handles image export and PPTX embedding.
    """

    def render(
        self,
        slide: Slide,
        chart_data: object,
        position: Position,
        theme: ResolvedTheme,
    ) -> None:
        """Render chart as a PNG image embedded in the slide."""
        fig = self._build_figure(chart_data, theme)
        self._apply_plotly_theme(fig, theme)

        # Set title if present
        title = getattr(chart_data, "title", None)
        if title:
            fig.update_layout(title_text=title)

        img_bytes = self._render_to_image(fig, position)

        x = Inches(position.x or 0)
        y = Inches(position.y or 0)
        w = Inches(position.width or 10)
        h = Inches(position.height or 5)

        slide.shapes.add_picture(BytesIO(img_bytes), x, y, w, h)

    def _render_to_image(self, fig: go.Figure, position: Position) -> bytes:
        """Export Plotly figure to PNG bytes at high resolution."""
        width_px = int((position.width or 10) * 150)
        height_px = int((position.height or 5) * 150)
        return fig.to_image(format="png", width=width_px, height=height_px, scale=2)

    def _apply_plotly_theme(self, fig: go.Figure, theme: ResolvedTheme) -> None:
        """Apply theme colors and typography to a Plotly figure."""
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(
                family=theme.typography.body_family,
                color=theme.colors.text_primary,
            ),
            margin=dict(l=40, r=20, t=40, b=40),
        )

    @abstractmethod
    def _build_figure(
        self, chart_data: object, theme: ResolvedTheme
    ) -> go.Figure:
        """Build a Plotly figure from chart data and theme. Subclasses implement this."""

    @staticmethod
    def _get_chart_colors(theme: ResolvedTheme, n: int) -> list[str]:
        """Return first n colors from theme.chart_colors, cycling if needed."""
        colors = theme.chart_colors
        if not colors:
            colors = ["#2E86AB", "#A23B72", "#F18F01", "#4CAF50", "#FF9800", "#9C27B0"]
        return [colors[i % len(colors)] for i in range(n)]
