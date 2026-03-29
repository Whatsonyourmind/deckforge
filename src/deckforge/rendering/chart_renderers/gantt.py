"""Gantt chart renderer -- Plotly px.timeline for project schedules."""

from __future__ import annotations

from typing import TYPE_CHECKING

import plotly.graph_objects as go

from deckforge.rendering.chart_renderers.static_base import StaticChartRenderer

if TYPE_CHECKING:
    from deckforge.themes.types import ResolvedTheme


class GanttChartRenderer(StaticChartRenderer):
    """Renders a Gantt chart using Plotly timeline."""

    def _build_figure(
        self, chart_data: object, theme: ResolvedTheme
    ) -> go.Figure:
        # Import pandas locally to avoid import-time dependency
        import pandas as pd
        import plotly.express as px

        tasks = chart_data.tasks
        records = [
            {"Task": t.name, "Start": t.start, "Finish": t.end}
            for t in tasks
        ]
        df = pd.DataFrame(records)

        colors = self._get_chart_colors(theme, len(tasks))

        fig = px.timeline(
            df,
            x_start="Start",
            x_end="Finish",
            y="Task",
            color="Task",
            color_discrete_sequence=colors,
        )
        fig.update_yaxes(autorange="reversed")
        return fig
