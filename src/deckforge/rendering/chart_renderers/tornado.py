"""Tornado chart renderer -- Plotly horizontal bar pairs for sensitivity."""

from __future__ import annotations

from typing import TYPE_CHECKING

import plotly.graph_objects as go

from deckforge.rendering.chart_renderers.static_base import StaticChartRenderer

if TYPE_CHECKING:
    from deckforge.themes.types import ResolvedTheme


class TornadoChartRenderer(StaticChartRenderer):
    """Renders a tornado (butterfly) chart using overlapping horizontal bars."""

    def _build_figure(
        self, chart_data: object, theme: ResolvedTheme
    ) -> go.Figure:
        categories = chart_data.categories
        base_value = chart_data.base_value or 0

        low_offsets = [v - base_value for v in chart_data.low_values]
        high_offsets = [v - base_value for v in chart_data.high_values]

        fig = go.Figure()

        # Low values (extend left -- show as negative for visual centering)
        fig.add_trace(
            go.Bar(
                y=categories,
                x=low_offsets,
                orientation="h",
                name="Low",
                marker_color=theme.colors.negative,
            )
        )

        # High values (extend right)
        fig.add_trace(
            go.Bar(
                y=categories,
                x=high_offsets,
                orientation="h",
                name="High",
                marker_color=theme.colors.positive,
            )
        )

        fig.update_layout(barmode="overlay")
        return fig
