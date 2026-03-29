"""Funnel chart renderer -- Plotly go.Funnel with theme colors."""

from __future__ import annotations

from typing import TYPE_CHECKING

import plotly.graph_objects as go

from deckforge.rendering.chart_renderers.static_base import StaticChartRenderer

if TYPE_CHECKING:
    from deckforge.themes.types import ResolvedTheme


class FunnelChartRenderer(StaticChartRenderer):
    """Renders a funnel chart using Plotly."""

    def _build_figure(
        self, chart_data: object, theme: ResolvedTheme
    ) -> go.Figure:
        colors = self._get_chart_colors(theme, len(chart_data.stages))

        fig = go.Figure(
            data=[
                go.Funnel(
                    y=chart_data.stages,
                    x=chart_data.values,
                    marker=dict(color=colors),
                )
            ]
        )
        return fig
