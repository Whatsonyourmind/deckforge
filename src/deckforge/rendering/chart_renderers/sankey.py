"""Sankey diagram renderer -- Plotly go.Sankey with theme node colors."""

from __future__ import annotations

from typing import TYPE_CHECKING

import plotly.graph_objects as go

from deckforge.rendering.chart_renderers.static_base import StaticChartRenderer

if TYPE_CHECKING:
    from deckforge.themes.types import ResolvedTheme


class SankeyChartRenderer(StaticChartRenderer):
    """Renders a Sankey diagram using Plotly."""

    def _build_figure(
        self, chart_data: object, theme: ResolvedTheme
    ) -> go.Figure:
        nodes = chart_data.nodes
        node_index = {name: idx for idx, name in enumerate(nodes)}

        sources = []
        targets = []
        values = []
        for link in chart_data.links:
            sources.append(node_index[link.source])
            targets.append(node_index[link.target])
            values.append(link.value)

        node_colors = self._get_chart_colors(theme, len(nodes))

        fig = go.Figure(
            data=[
                go.Sankey(
                    node=dict(
                        label=nodes,
                        color=node_colors,
                        pad=15,
                        thickness=20,
                    ),
                    link=dict(
                        source=sources,
                        target=targets,
                        value=values,
                    ),
                )
            ]
        )
        return fig
