"""Chart renderer registry — maps chart_type strings to renderer instances.

Usage:
    from deckforge.rendering.chart_renderers import render_chart
    render_chart(slide, chart_data, position, theme)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from deckforge.rendering.chart_renderers.base import BaseChartRenderer
from deckforge.rendering.chart_renderers.category import (
    AreaChartRenderer,
    BarChartRenderer,
    LineChartRenderer,
)
from deckforge.rendering.chart_renderers.combo import ComboChartRenderer
from deckforge.rendering.chart_renderers.placeholder import PlaceholderChartRenderer
from deckforge.rendering.chart_renderers.proportional import (
    DonutChartRenderer,
    PieChartRenderer,
)
from deckforge.rendering.chart_renderers.radar import RadarChartRenderer
from deckforge.rendering.chart_renderers.scatter import (
    BubbleChartRenderer,
    ScatterChartRenderer,
)

if TYPE_CHECKING:
    from pptx.slide import Slide

    from deckforge.ir.elements.base import Position
    from deckforge.themes.types import ResolvedTheme

__all__ = [
    "CHART_RENDERERS",
    "BaseChartRenderer",
    "render_chart",
]

# ── Registry ──────────────────────────────────────────────────────────────────

CHART_RENDERERS: dict[str, BaseChartRenderer] = {
    # Category-based (native editable)
    "bar": BarChartRenderer(),
    "stacked_bar": BarChartRenderer(),
    "grouped_bar": BarChartRenderer(),
    "horizontal_bar": BarChartRenderer(),
    "line": LineChartRenderer(),
    "multi_line": LineChartRenderer(),
    "area": AreaChartRenderer(),
    "stacked_area": AreaChartRenderer(),
    # Proportional (native editable)
    "pie": PieChartRenderer(),
    "donut": DonutChartRenderer(),
    # Scatter/Bubble (native editable)
    "scatter": ScatterChartRenderer(),
    "bubble": BubbleChartRenderer(),
    # Combo (native editable — bar + line overlay)
    "combo": ComboChartRenderer(),
    # Radar (native editable)
    "radar": RadarChartRenderer(),
    # Unsupported — Phase 5 placeholders
    "waterfall": PlaceholderChartRenderer(),
    "funnel": PlaceholderChartRenderer(),
    "treemap": PlaceholderChartRenderer(),
    "tornado": PlaceholderChartRenderer(),
    "football_field": PlaceholderChartRenderer(),
    "sensitivity_table": PlaceholderChartRenderer(),
    "heatmap": PlaceholderChartRenderer(),
    "sankey": PlaceholderChartRenderer(),
    "gantt": PlaceholderChartRenderer(),
    "sunburst": PlaceholderChartRenderer(),
}


def render_chart(
    slide: Slide,
    chart_data: object,
    position: Position,
    theme: ResolvedTheme,
) -> None:
    """Dispatch chart rendering to the appropriate renderer.

    Looks up chart_data.chart_type in CHART_RENDERERS and calls render().
    Falls back to PlaceholderChartRenderer for unknown types.
    """
    chart_type = getattr(chart_data, "chart_type", "unknown")
    renderer = CHART_RENDERERS.get(chart_type, PlaceholderChartRenderer())
    renderer.render(slide, chart_data, position, theme)
