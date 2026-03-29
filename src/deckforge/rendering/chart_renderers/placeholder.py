"""Placeholder chart renderer — visual placeholder for unsupported chart types."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from deckforge.rendering.chart_renderers.base import BaseChartRenderer

if TYPE_CHECKING:
    from pptx.slide import Slide

    from deckforge.ir.elements.base import Position
    from deckforge.themes.types import ResolvedTheme


class PlaceholderChartRenderer(BaseChartRenderer):
    """Renders a rectangle placeholder with text label for unsupported chart types.

    Charts without native python-pptx support (waterfall, heatmap, sankey, gantt,
    sunburst, treemap, tornado, football_field, sensitivity_table, funnel) get
    a visible placeholder that communicates the chart type and deferred status.
    """

    def render(
        self,
        slide: Slide,
        chart_data: object,
        position: Position,
        theme: ResolvedTheme,
    ) -> None:
        chart_type = getattr(chart_data, "chart_type", "unknown")
        title = getattr(chart_data, "title", None)

        x = Inches(position.x or 0)
        y = Inches(position.y or 0)
        w = Inches(position.width or 10)
        h = Inches(position.height or 5)

        shape = slide.shapes.add_shape(
            1,  # MSO_SHAPE.RECTANGLE
            x,
            y,
            w,
            h,
        )

        # Style the rectangle
        fill = shape.fill
        fill.solid()
        surface_color = theme.colors.surface.lstrip("#")
        fill.fore_color.rgb = RGBColor.from_string(surface_color)

        # Border
        line = shape.line
        line.color.rgb = RGBColor.from_string(
            theme.colors.text_muted.lstrip("#")
        )
        line.width = Pt(1)

        # Text content
        label = f"{chart_type} chart (rendering in Phase 5)"
        if title:
            label = f"{title}\n\n{label}"

        tf = shape.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = label
        p.font.name = theme.typography.body_family
        p.font.size = Pt(theme.typography.scale.get("body", 18))
        p.font.color.rgb = RGBColor.from_string(
            theme.colors.text_muted.lstrip("#")
        )
        p.alignment = PP_ALIGN.CENTER
