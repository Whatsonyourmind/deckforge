"""Chart subtype models — all 24 chart types with data schemas."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


# ── Shared ─────────────────────────────────────────────────────────────────────


class ChartDataSeries(BaseModel):
    """A named data series with numeric values."""

    name: str
    values: list[float | int | None]


class SankeyLink(BaseModel):
    """A link between two nodes in a Sankey diagram."""

    source: str
    target: str
    value: float | int


class GanttTask(BaseModel):
    """A task in a Gantt chart."""

    name: str
    start: str
    end: str
    progress: float | None = None
    dependencies: list[str] | None = None


# ── Category-based charts (bar, line, area variants) ──────────────────────────


class BarChartData(BaseModel):
    chart_type: Literal["bar"] = "bar"
    categories: list[str]
    series: list[ChartDataSeries]
    show_values: bool = False
    title: str | None = None


class StackedBarChartData(BaseModel):
    chart_type: Literal["stacked_bar"] = "stacked_bar"
    categories: list[str]
    series: list[ChartDataSeries]
    show_values: bool = False
    title: str | None = None


class GroupedBarChartData(BaseModel):
    chart_type: Literal["grouped_bar"] = "grouped_bar"
    categories: list[str]
    series: list[ChartDataSeries]
    show_values: bool = False
    title: str | None = None


class HorizontalBarChartData(BaseModel):
    chart_type: Literal["horizontal_bar"] = "horizontal_bar"
    categories: list[str]
    series: list[ChartDataSeries]
    show_values: bool = False
    title: str | None = None


class LineChartData(BaseModel):
    chart_type: Literal["line"] = "line"
    categories: list[str]
    series: list[ChartDataSeries]
    show_markers: bool = True
    title: str | None = None


class MultiLineChartData(BaseModel):
    chart_type: Literal["multi_line"] = "multi_line"
    categories: list[str]
    series: list[ChartDataSeries]
    show_markers: bool = True
    title: str | None = None


class AreaChartData(BaseModel):
    chart_type: Literal["area"] = "area"
    categories: list[str]
    series: list[ChartDataSeries]
    title: str | None = None


class StackedAreaChartData(BaseModel):
    chart_type: Literal["stacked_area"] = "stacked_area"
    categories: list[str]
    series: list[ChartDataSeries]
    title: str | None = None


# ── Proportional charts ───────────────────────────────────────────────────────


class PieChartData(BaseModel):
    chart_type: Literal["pie"] = "pie"
    labels: list[str]
    values: list[float | int]
    show_percentages: bool = True
    title: str | None = None


class DonutChartData(BaseModel):
    chart_type: Literal["donut"] = "donut"
    labels: list[str]
    values: list[float | int]
    show_percentages: bool = True
    inner_radius: float = 0.5
    title: str | None = None


# ── Scatter / Bubble ─────────────────────────────────────────────────────────


class ScatterChartData(BaseModel):
    chart_type: Literal["scatter"] = "scatter"
    series: list[ChartDataSeries]
    x_values: list[float | int]
    title: str | None = None


class BubbleChartData(BaseModel):
    chart_type: Literal["bubble"] = "bubble"
    series: list[ChartDataSeries]
    x_values: list[float | int]
    sizes: list[float | int]
    title: str | None = None


# ── Combo ────────────────────────────────────────────────────────────────────


class ComboChartData(BaseModel):
    chart_type: Literal["combo"] = "combo"
    categories: list[str]
    series: list[ChartDataSeries]
    line_series: list[ChartDataSeries] = []
    title: str | None = None


# ── Financial / Specialized ──────────────────────────────────────────────────


class WaterfallChartData(BaseModel):
    chart_type: Literal["waterfall"] = "waterfall"
    categories: list[str]
    values: list[float | int]
    title: str | None = None


class FunnelChartData(BaseModel):
    chart_type: Literal["funnel"] = "funnel"
    stages: list[str]
    values: list[float | int]
    title: str | None = None


class TreemapChartData(BaseModel):
    chart_type: Literal["treemap"] = "treemap"
    labels: list[str]
    values: list[float | int]
    parents: list[str] | None = None
    title: str | None = None


class RadarChartData(BaseModel):
    chart_type: Literal["radar"] = "radar"
    axes: list[str]
    series: list[ChartDataSeries]
    title: str | None = None


class TornadoChartData(BaseModel):
    chart_type: Literal["tornado"] = "tornado"
    categories: list[str]
    low_values: list[float | int]
    high_values: list[float | int]
    base_value: float | None = None
    title: str | None = None


class FootballFieldChartData(BaseModel):
    chart_type: Literal["football_field"] = "football_field"
    categories: list[str]
    low_values: list[float | int]
    high_values: list[float | int]
    mid_values: list[float | int] | None = None
    title: str | None = None


class SensitivityTableData(BaseModel):
    chart_type: Literal["sensitivity_table"] = "sensitivity_table"
    row_header: str
    col_header: str
    row_values: list[float | int]
    col_values: list[float | int]
    data: list[list[float | int]]
    title: str | None = None


# ── Static fallback charts ───────────────────────────────────────────────────


class HeatmapChartData(BaseModel):
    chart_type: Literal["heatmap"] = "heatmap"
    x_labels: list[str]
    y_labels: list[str]
    data: list[list[float | int]]
    title: str | None = None


class SankeyChartData(BaseModel):
    chart_type: Literal["sankey"] = "sankey"
    nodes: list[str]
    links: list[SankeyLink]
    title: str | None = None


class GanttChartData(BaseModel):
    chart_type: Literal["gantt"] = "gantt"
    tasks: list[GanttTask]
    title: str | None = None


class SunburstChartData(BaseModel):
    chart_type: Literal["sunburst"] = "sunburst"
    labels: list[str]
    parents: list[str]
    values: list[float | int]
    title: str | None = None


# ── ChartUnion (discriminated union on chart_type) ───────────────────────────

ChartUnion = Annotated[
    Union[
        BarChartData,
        StackedBarChartData,
        GroupedBarChartData,
        HorizontalBarChartData,
        LineChartData,
        MultiLineChartData,
        AreaChartData,
        StackedAreaChartData,
        PieChartData,
        DonutChartData,
        ScatterChartData,
        BubbleChartData,
        ComboChartData,
        WaterfallChartData,
        FunnelChartData,
        TreemapChartData,
        RadarChartData,
        TornadoChartData,
        FootballFieldChartData,
        SensitivityTableData,
        HeatmapChartData,
        SankeyChartData,
        GanttChartData,
        SunburstChartData,
    ],
    Field(discriminator="chart_type"),
]
