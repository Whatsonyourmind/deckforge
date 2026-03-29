"""Data element models — table, chart, kpi_card, metric_group, progress_bar, gauge, sparkline."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from deckforge.ir.charts.types import ChartUnion
from deckforge.ir.elements.base import BaseElement


# ── Content Models ─────────────────────────────────────────────────────────────


class TableContent(BaseModel):
    headers: list[str]
    rows: list[list[str | float | int | None]]
    footer_row: list[str | float | int | None] | None = None
    highlight_rows: list[int] | None = None
    sortable: bool = False


class KpiCardContent(BaseModel):
    label: str
    value: str | float
    change: float | None = None
    change_direction: Literal["up", "down", "flat"] | None = None


class MetricGroupContent(BaseModel):
    metrics: list[KpiCardContent]


class ProgressBarContent(BaseModel):
    label: str
    value: float
    max_value: float = 100


class GaugeContent(BaseModel):
    label: str
    value: float
    min_value: float = 0
    max_value: float = 100


class SparklineContent(BaseModel):
    values: list[float]
    label: str | None = None


# ── Element Models ─────────────────────────────────────────────────────────────


class TableElement(BaseElement):
    type: Literal["table"] = "table"
    content: TableContent


class ChartElement(BaseElement):
    type: Literal["chart"] = "chart"
    chart_data: ChartUnion


class KpiCardElement(BaseElement):
    type: Literal["kpi_card"] = "kpi_card"
    content: KpiCardContent


class MetricGroupElement(BaseElement):
    type: Literal["metric_group"] = "metric_group"
    content: MetricGroupContent


class ProgressBarElement(BaseElement):
    type: Literal["progress_bar"] = "progress_bar"
    content: ProgressBarContent


class GaugeElement(BaseElement):
    type: Literal["gauge"] = "gauge"
    content: GaugeContent


class SparklineElement(BaseElement):
    type: Literal["sparkline"] = "sparkline"
    content: SparklineContent
