"""Heatmap chart renderer -- Plotly go.Heatmap with theme colorscale."""

from __future__ import annotations

from typing import TYPE_CHECKING

import plotly.graph_objects as go

from deckforge.rendering.chart_renderers.static_base import StaticChartRenderer

if TYPE_CHECKING:
    from deckforge.themes.types import ResolvedTheme


class HeatmapChartRenderer(StaticChartRenderer):
    """Renders a heatmap chart using Plotly."""

    def _build_figure(
        self, chart_data: object, theme: ResolvedTheme
    ) -> go.Figure:
        fig = go.Figure(
            data=[
                go.Heatmap(
                    z=chart_data.data,
                    x=chart_data.x_labels,
                    y=chart_data.y_labels,
                    colorscale=[
                        [0, theme.colors.negative],
                        [0.5, theme.colors.surface],
                        [1, theme.colors.positive],
                    ],
                    text=chart_data.data,
                    texttemplate="%{text:.1f}",
                    textfont=dict(size=11),
                )
            ]
        )
        return fig
