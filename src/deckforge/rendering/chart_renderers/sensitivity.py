"""Sensitivity table renderer -- annotated heatmap for sensitivity analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

import plotly.graph_objects as go

from deckforge.rendering.chart_renderers.static_base import StaticChartRenderer

if TYPE_CHECKING:
    from deckforge.themes.types import ResolvedTheme


class SensitivityChartRenderer(StaticChartRenderer):
    """Renders a sensitivity table as an annotated heatmap."""

    def _build_figure(
        self, chart_data: object, theme: ResolvedTheme
    ) -> go.Figure:
        # Format column and row values as strings for axis labels
        col_labels = [str(v) for v in chart_data.col_values]
        row_labels = [str(v) for v in chart_data.row_values]

        fig = go.Figure(
            data=[
                go.Heatmap(
                    z=chart_data.data,
                    x=col_labels,
                    y=row_labels,
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

        fig.update_layout(
            xaxis_title=chart_data.col_header,
            yaxis_title=chart_data.row_header,
        )
        return fig
