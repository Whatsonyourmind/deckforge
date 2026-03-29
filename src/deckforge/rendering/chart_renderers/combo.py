"""Combo chart renderer — bar series with line overlay via XML manipulation."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from lxml import etree
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches

from deckforge.rendering.chart_renderers.base import BaseChartRenderer

if TYPE_CHECKING:
    from pptx.slide import Slide

    from deckforge.ir.elements.base import Position
    from deckforge.themes.types import ResolvedTheme

logger = logging.getLogger(__name__)

_CHART_NS = "http://schemas.openxmlformats.org/drawingml/2006/chart"


def _nsmap(tag: str) -> str:
    """Create a namespaced tag string for chart XML."""
    return f"{{{_CHART_NS}}}{tag}"


class ComboChartRenderer(BaseChartRenderer):
    """Renders combo (bar + line) charts as native editable charts.

    Strategy: Create a COLUMN_CLUSTERED chart with all bar series, then inject
    a lineChart element into the plotArea XML with line series data. Both plot
    types share the same category axis, creating a true combo chart editable
    in PowerPoint.
    """

    def render(
        self,
        slide: Slide,
        chart_data: object,
        position: Position,
        theme: ResolvedTheme,
    ) -> None:
        categories = chart_data.categories  # type: ignore[attr-defined]
        bar_series_data = chart_data.series  # type: ignore[attr-defined]
        line_series_data = getattr(chart_data, "line_series", [])

        # Build initial bar chart with all bar series
        cd = CategoryChartData()
        cd.categories = categories
        for series in bar_series_data:
            values = [v if v is not None else 0 for v in series.values]
            cd.add_series(series.name, values)

        x = Inches(position.x or 0)
        y = Inches(position.y or 0)
        w = Inches(position.width or 10)
        h = Inches(position.height or 5)

        graphic_frame = slide.shapes.add_chart(
            XL_CHART_TYPE.COLUMN_CLUSTERED, x, y, w, h, cd
        )
        chart = graphic_frame.chart

        # Add line series via XML manipulation
        if line_series_data:
            self._inject_line_chart(chart, categories, bar_series_data, line_series_data)

        title = getattr(chart_data, "title", None)
        self._apply_theme_formatting(chart, theme, title=title)

    def _inject_line_chart(
        self,
        chart: object,
        categories: list[str],
        bar_series_data: list,
        line_series_data: list,
    ) -> None:
        """Inject a lineChart element into the plot area for line overlay series."""
        chart_space = chart._chartSpace  # type: ignore[attr-defined]
        plot_area = chart_space.find(f".//{_nsmap('plotArea')}")
        if plot_area is None:
            logger.warning("Could not find plotArea in chart XML; skipping line overlay")
            return

        # Find the existing axes to reference
        bar_chart = plot_area.find(_nsmap("barChart"))
        if bar_chart is None:
            return

        ax_ids = bar_chart.findall(_nsmap("axId"))
        if len(ax_ids) < 2:
            return

        cat_ax_id = ax_ids[0].get("val")
        val_ax_id = ax_ids[1].get("val")

        # Build lineChart element
        line_chart = etree.SubElement(plot_area, _nsmap("lineChart"))
        grouping = etree.SubElement(line_chart, _nsmap("grouping"))
        grouping.set("val", "standard")

        # Series index starts after bar series
        bar_count = len(bar_series_data)
        for idx, series in enumerate(line_series_data):
            ser_idx = bar_count + idx
            ser_elem = etree.SubElement(line_chart, _nsmap("ser"))

            # Index and order
            idx_elem = etree.SubElement(ser_elem, _nsmap("idx"))
            idx_elem.set("val", str(ser_idx))
            order_elem = etree.SubElement(ser_elem, _nsmap("order"))
            order_elem.set("val", str(ser_idx))

            # Series name (tx)
            tx_elem = etree.SubElement(ser_elem, _nsmap("tx"))
            str_ref = etree.SubElement(tx_elem, _nsmap("strRef"))
            str_cache = etree.SubElement(str_ref, _nsmap("strCache"))
            pt_count = etree.SubElement(str_cache, _nsmap("ptCount"))
            pt_count.set("val", "1")
            pt = etree.SubElement(str_cache, _nsmap("pt"))
            pt.set("idx", "0")
            v = etree.SubElement(pt, _nsmap("v"))
            v.text = series.name

            # Category reference (cat) — inline string cache
            cat_elem = etree.SubElement(ser_elem, _nsmap("cat"))
            cat_str_ref = etree.SubElement(cat_elem, _nsmap("strRef"))
            cat_cache = etree.SubElement(cat_str_ref, _nsmap("strCache"))
            cat_pt_count = etree.SubElement(cat_cache, _nsmap("ptCount"))
            cat_pt_count.set("val", str(len(categories)))
            for ci, cat_name in enumerate(categories):
                cat_pt = etree.SubElement(cat_cache, _nsmap("pt"))
                cat_pt.set("idx", str(ci))
                cat_v = etree.SubElement(cat_pt, _nsmap("v"))
                cat_v.text = str(cat_name)

            # Values (val) — inline number cache
            val_elem = etree.SubElement(ser_elem, _nsmap("val"))
            num_ref = etree.SubElement(val_elem, _nsmap("numRef"))
            num_cache = etree.SubElement(num_ref, _nsmap("numCache"))
            fmt_code = etree.SubElement(num_cache, _nsmap("formatCode"))
            fmt_code.text = "General"
            num_pt_count = etree.SubElement(num_cache, _nsmap("ptCount"))
            values = [v if v is not None else 0 for v in series.values]
            num_pt_count.set("val", str(len(values)))
            for vi, val in enumerate(values):
                num_pt = etree.SubElement(num_cache, _nsmap("pt"))
                num_pt.set("idx", str(vi))
                num_v = etree.SubElement(num_pt, _nsmap("v"))
                num_v.text = str(val)

            # Marker (show markers)
            marker = etree.SubElement(ser_elem, _nsmap("marker"))
            symbol = etree.SubElement(marker, _nsmap("symbol"))
            symbol.set("val", "circle")

        # Reference same axes
        ax_id1 = etree.SubElement(line_chart, _nsmap("axId"))
        ax_id1.set("val", cat_ax_id)
        ax_id2 = etree.SubElement(line_chart, _nsmap("axId"))
        ax_id2.set("val", val_ax_id)
