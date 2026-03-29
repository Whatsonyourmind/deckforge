"""Waterfall chart renderer -- Plotly go.Waterfall with positive/negative coloring."""

from __future__ import annotations

from typing import TYPE_CHECKING

import plotly.graph_objects as go

from deckforge.rendering.chart_renderers.static_base import StaticChartRenderer

if TYPE_CHECKING:
    from deckforge.themes.types import ResolvedTheme


class WaterfallChartRenderer(StaticChartRenderer):
    """Renders a waterfall (bridge) chart using Plotly."""

    def _build_figure(
        self, chart_data: object, theme: ResolvedTheme
    ) -> go.Figure:
        categories = chart_data.categories
        values = chart_data.values
        measures = self._infer_measures(values, categories)

        fig = go.Figure(
            data=[
                go.Waterfall(
                    x=categories,
                    y=values,
                    measure=measures,
                    increasing=dict(marker=dict(color=theme.colors.positive)),
                    decreasing=dict(marker=dict(color=theme.colors.negative)),
                    totals=dict(marker=dict(color=theme.colors.primary)),
                    connector=dict(
                        line=dict(color=theme.colors.text_muted, width=1)
                    ),
                )
            ]
        )
        return fig

    @staticmethod
    def _infer_measures(
        values: list[float | int], categories: list[str]
    ) -> list[str]:
        """Infer measure types: 'total' for last if it looks like a total, else 'relative'."""
        measures = ["relative"] * len(values)
        if categories:
            last = categories[-1].lower()
            if any(kw in last for kw in ("total", "net", "sum")):
                measures[-1] = "total"
        return measures
