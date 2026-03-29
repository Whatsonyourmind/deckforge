"""Radar chart renderer — native editable radar/spider charts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches

from deckforge.rendering.chart_renderers.base import BaseChartRenderer

if TYPE_CHECKING:
    from pptx.slide import Slide

    from deckforge.ir.elements.base import Position
    from deckforge.themes.types import ResolvedTheme


class RadarChartRenderer(BaseChartRenderer):
    """Renders native editable RADAR charts.

    Uses CategoryChartData with chart_data.axes as categories and
    each series plotted around the radar axes. The chart is fully
    editable in PowerPoint.
    """

    def render(
        self,
        slide: Slide,
        chart_data: object,
        position: Position,
        theme: ResolvedTheme,
    ) -> None:
        cd = CategoryChartData()
        cd.categories = chart_data.axes  # type: ignore[attr-defined]

        for series in chart_data.series:  # type: ignore[attr-defined]
            values = [v if v is not None else 0 for v in series.values]
            cd.add_series(series.name, values)

        x = Inches(position.x or 0)
        y = Inches(position.y or 0)
        w = Inches(position.width or 10)
        h = Inches(position.height or 5)

        graphic_frame = slide.shapes.add_chart(
            XL_CHART_TYPE.RADAR, x, y, w, h, cd
        )
        chart = graphic_frame.chart

        title = getattr(chart_data, "title", None)
        self._apply_theme_formatting(chart, theme, title=title)
