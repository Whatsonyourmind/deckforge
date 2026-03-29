"""Sunburst chart renderer -- Plotly go.Sunburst with theme colors."""

from __future__ import annotations

from typing import TYPE_CHECKING

import plotly.graph_objects as go

from deckforge.rendering.chart_renderers.static_base import StaticChartRenderer

if TYPE_CHECKING:
    from deckforge.themes.types import ResolvedTheme


class SunburstChartRenderer(StaticChartRenderer):
    """Renders a sunburst chart using Plotly."""

    def _build_figure(
        self, chart_data: object, theme: ResolvedTheme
    ) -> go.Figure:
        labels = chart_data.labels
        parents = chart_data.parents
        values = chart_data.values
        colors = self._get_chart_colors(theme, len(labels))

        fig = go.Figure(
            data=[
                go.Sunburst(
                    labels=labels,
                    parents=parents,
                    values=values,
                    marker=dict(colors=colors),
                )
            ]
        )
        return fig
