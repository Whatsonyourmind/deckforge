"""Tests for IR chart types + ChartUnion discriminated union."""

from __future__ import annotations

import pytest
from pydantic import ValidationError, TypeAdapter


# ── Individual Chart Types ─────────────────────────────────────────────────────


class TestBarChart:
    def test_valid_bar(self):
        from deckforge.ir.charts.types import BarChartData

        c = BarChartData(
            chart_type="bar",
            categories=["Q1", "Q2"],
            series=[{"name": "Rev", "values": [100, 200]}],
        )
        assert c.chart_type == "bar"
        assert len(c.series) == 1


class TestStackedBarChart:
    def test_valid_stacked_bar(self):
        from deckforge.ir.charts.types import StackedBarChartData

        c = StackedBarChartData(
            chart_type="stacked_bar",
            categories=["A", "B"],
            series=[{"name": "S1", "values": [1, 2]}],
        )
        assert c.chart_type == "stacked_bar"


class TestLineChart:
    def test_valid_line(self):
        from deckforge.ir.charts.types import LineChartData

        c = LineChartData(
            chart_type="line",
            categories=["Jan", "Feb"],
            series=[{"name": "Sales", "values": [50, 60]}],
        )
        assert c.chart_type == "line"


class TestPieChart:
    def test_valid_pie(self):
        from deckforge.ir.charts.types import PieChartData

        c = PieChartData(
            chart_type="pie",
            labels=["Segment A", "Segment B"],
            values=[60, 40],
        )
        assert c.chart_type == "pie"
        assert c.values == [60, 40]


class TestDonutChart:
    def test_valid_donut(self):
        from deckforge.ir.charts.types import DonutChartData

        c = DonutChartData(
            chart_type="donut",
            labels=["X", "Y"],
            values=[70, 30],
        )
        assert c.chart_type == "donut"


class TestScatterChart:
    def test_valid_scatter(self):
        from deckforge.ir.charts.types import ScatterChartData

        c = ScatterChartData(
            chart_type="scatter",
            series=[{"name": "Points", "values": [1.0, 2.0, 3.0]}],
            x_values=[10.0, 20.0, 30.0],
        )
        assert c.chart_type == "scatter"


class TestBubbleChart:
    def test_valid_bubble(self):
        from deckforge.ir.charts.types import BubbleChartData

        c = BubbleChartData(
            chart_type="bubble",
            series=[{"name": "B1", "values": [1.0, 2.0]}],
            x_values=[10.0, 20.0],
            sizes=[5.0, 10.0],
        )
        assert c.chart_type == "bubble"


class TestComboChart:
    def test_valid_combo(self):
        from deckforge.ir.charts.types import ComboChartData

        c = ComboChartData(
            chart_type="combo",
            categories=["A", "B"],
            series=[{"name": "Bar", "values": [1, 2]}],
            line_series=[{"name": "Line", "values": [3, 4]}],
        )
        assert c.chart_type == "combo"


class TestWaterfallChart:
    def test_valid_waterfall(self):
        from deckforge.ir.charts.types import WaterfallChartData

        c = WaterfallChartData(
            chart_type="waterfall",
            categories=["Start", "Change", "End"],
            values=[100, -20, 80],
        )
        assert c.chart_type == "waterfall"


class TestFunnelChart:
    def test_valid_funnel(self):
        from deckforge.ir.charts.types import FunnelChartData

        c = FunnelChartData(
            chart_type="funnel",
            stages=["Leads", "Qualified", "Won"],
            values=[1000, 500, 100],
        )
        assert c.chart_type == "funnel"


class TestRadarChart:
    def test_valid_radar(self):
        from deckforge.ir.charts.types import RadarChartData

        c = RadarChartData(
            chart_type="radar",
            axes=["Speed", "Power", "Range"],
            series=[{"name": "Model A", "values": [8, 6, 7]}],
        )
        assert c.chart_type == "radar"


class TestTreemapChart:
    def test_valid_treemap(self):
        from deckforge.ir.charts.types import TreemapChartData

        c = TreemapChartData(
            chart_type="treemap",
            labels=["A", "B", "C"],
            values=[50, 30, 20],
        )
        assert c.chart_type == "treemap"


class TestTornadoChart:
    def test_valid_tornado(self):
        from deckforge.ir.charts.types import TornadoChartData

        c = TornadoChartData(
            chart_type="tornado",
            categories=["Factor A", "Factor B"],
            low_values=[-10, -20],
            high_values=[15, 25],
        )
        assert c.chart_type == "tornado"


class TestFootballFieldChart:
    def test_valid_football_field(self):
        from deckforge.ir.charts.types import FootballFieldChartData

        c = FootballFieldChartData(
            chart_type="football_field",
            categories=["DCF", "Comps"],
            low_values=[80, 90],
            high_values=[120, 130],
        )
        assert c.chart_type == "football_field"


class TestSensitivityTable:
    def test_valid_sensitivity(self):
        from deckforge.ir.charts.types import SensitivityTableData

        c = SensitivityTableData(
            chart_type="sensitivity_table",
            row_header="WACC",
            col_header="Growth",
            row_values=[8.0, 10.0],
            col_values=[2.0, 3.0],
            data=[[100, 110], [90, 100]],
        )
        assert c.chart_type == "sensitivity_table"


class TestHeatmapChart:
    def test_valid_heatmap(self):
        from deckforge.ir.charts.types import HeatmapChartData

        c = HeatmapChartData(
            chart_type="heatmap",
            x_labels=["A", "B"],
            y_labels=["X", "Y"],
            data=[[1, 2], [3, 4]],
        )
        assert c.chart_type == "heatmap"


class TestSankeyChart:
    def test_valid_sankey(self):
        from deckforge.ir.charts.types import SankeyChartData

        c = SankeyChartData(
            chart_type="sankey",
            nodes=["Source", "Target"],
            links=[{"source": "Source", "target": "Target", "value": 100}],
        )
        assert c.chart_type == "sankey"


class TestGanttChart:
    def test_valid_gantt(self):
        from deckforge.ir.charts.types import GanttChartData

        c = GanttChartData(
            chart_type="gantt",
            tasks=[{"name": "Task 1", "start": "2026-01-01", "end": "2026-03-01"}],
        )
        assert c.chart_type == "gantt"


class TestSunburstChart:
    def test_valid_sunburst(self):
        from deckforge.ir.charts.types import SunburstChartData

        c = SunburstChartData(
            chart_type="sunburst",
            labels=["Root", "A", "B"],
            parents=["", "Root", "Root"],
            values=[100, 60, 40],
        )
        assert c.chart_type == "sunburst"


class TestAreaChart:
    def test_valid_area(self):
        from deckforge.ir.charts.types import AreaChartData

        c = AreaChartData(
            chart_type="area",
            categories=["Jan", "Feb"],
            series=[{"name": "S1", "values": [10, 20]}],
        )
        assert c.chart_type == "area"


class TestStackedAreaChart:
    def test_valid_stacked_area(self):
        from deckforge.ir.charts.types import StackedAreaChartData

        c = StackedAreaChartData(
            chart_type="stacked_area",
            categories=["Jan", "Feb"],
            series=[{"name": "S1", "values": [10, 20]}],
        )
        assert c.chart_type == "stacked_area"


class TestGroupedBarChart:
    def test_valid_grouped_bar(self):
        from deckforge.ir.charts.types import GroupedBarChartData

        c = GroupedBarChartData(
            chart_type="grouped_bar",
            categories=["A", "B"],
            series=[{"name": "S1", "values": [1, 2]}],
        )
        assert c.chart_type == "grouped_bar"


class TestHorizontalBarChart:
    def test_valid_horizontal_bar(self):
        from deckforge.ir.charts.types import HorizontalBarChartData

        c = HorizontalBarChartData(
            chart_type="horizontal_bar",
            categories=["A", "B"],
            series=[{"name": "S1", "values": [1, 2]}],
        )
        assert c.chart_type == "horizontal_bar"


class TestMultiLineChart:
    def test_valid_multi_line(self):
        from deckforge.ir.charts.types import MultiLineChartData

        c = MultiLineChartData(
            chart_type="multi_line",
            categories=["Jan", "Feb"],
            series=[
                {"name": "S1", "values": [1, 2]},
                {"name": "S2", "values": [3, 4]},
            ],
        )
        assert c.chart_type == "multi_line"


# ── ChartUnion Discriminated Union ─────────────────────────────────────────────


class TestChartUnion:
    def test_routes_bar(self):
        from deckforge.ir.charts import ChartUnion

        adapter = TypeAdapter(ChartUnion)
        c = adapter.validate_python(
            {
                "chart_type": "bar",
                "categories": ["A"],
                "series": [{"name": "S", "values": [1]}],
            }
        )
        assert type(c).__name__ == "BarChartData"

    def test_routes_pie(self):
        from deckforge.ir.charts import ChartUnion

        adapter = TypeAdapter(ChartUnion)
        c = adapter.validate_python(
            {"chart_type": "pie", "labels": ["A", "B"], "values": [60, 40]}
        )
        assert type(c).__name__ == "PieChartData"

    def test_routes_waterfall(self):
        from deckforge.ir.charts import ChartUnion

        adapter = TypeAdapter(ChartUnion)
        c = adapter.validate_python(
            {
                "chart_type": "waterfall",
                "categories": ["Start", "End"],
                "values": [100, 80],
            }
        )
        assert type(c).__name__ == "WaterfallChartData"

    def test_routes_gantt(self):
        from deckforge.ir.charts import ChartUnion

        adapter = TypeAdapter(ChartUnion)
        c = adapter.validate_python(
            {
                "chart_type": "gantt",
                "tasks": [{"name": "T1", "start": "2026-01-01", "end": "2026-02-01"}],
            }
        )
        assert type(c).__name__ == "GanttChartData"

    def test_invalid_chart_type_raises(self):
        from deckforge.ir.charts import ChartUnion

        adapter = TypeAdapter(ChartUnion)
        with pytest.raises(ValidationError) as exc_info:
            adapter.validate_python({"chart_type": "nonexistent_chart"})
        error_str = str(exc_info.value).lower()
        assert "nonexistent_chart" in error_str or "chart_type" in error_str
