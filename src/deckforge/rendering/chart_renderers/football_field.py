"""Football field chart renderer -- horizontal range bars for valuation ranges."""

from __future__ import annotations

from typing import TYPE_CHECKING

import plotly.graph_objects as go

from deckforge.rendering.chart_renderers.static_base import StaticChartRenderer

if TYPE_CHECKING:
    from deckforge.themes.types import ResolvedTheme


class FootballFieldChartRenderer(StaticChartRenderer):
    """Renders a football field (valuation range) chart using horizontal bars."""

    def _build_figure(
        self, chart_data: object, theme: ResolvedTheme
    ) -> go.Figure:
        categories = chart_data.categories
        low_values = chart_data.low_values
        high_values = chart_data.high_values
        mid_values = chart_data.mid_values

        colors = self._get_chart_colors(theme, len(categories))

        # Range bars: base at low, width is high - low
        widths = [h - l for h, l in zip(high_values, low_values)]

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                y=categories,
                x=widths,
                base=low_values,
                orientation="h",
                marker=dict(color=colors),
                name="Range",
                showlegend=False,
            )
        )

        # Add midpoint markers if provided
        if mid_values:
            fig.add_trace(
                go.Scatter(
                    y=categories,
                    x=mid_values,
                    mode="markers",
                    marker=dict(
                        symbol="diamond",
                        size=12,
                        color=theme.colors.text_primary,
                        line=dict(width=1, color=theme.colors.text_muted),
                    ),
                    name="Midpoint",
                    showlegend=False,
                )
            )

        fig.update_layout(
            xaxis_title="Value",
            bargap=0.3,
        )
        return fig
