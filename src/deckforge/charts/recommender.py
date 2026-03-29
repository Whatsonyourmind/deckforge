"""Chart type recommender -- rule-based chart type suggestion from data shape.

Given a dict describing the data shape (series count, categories, field presence),
returns a ChartRecommendation with the suggested chart_type, confidence, and reason.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChartRecommendation:
    """Result of a chart type recommendation."""

    chart_type: str
    confidence: float
    reason: str


def recommend_chart_type(data: dict) -> ChartRecommendation:
    """Recommend a chart type based on data shape characteristics.

    Args:
        data: Dict with optional keys describing data shape:
            - series_count: int -- number of data series
            - category_count: int -- number of categories
            - has_dates: bool -- whether categories are time-like
            - has_date_ranges: bool -- whether data has start/end date pairs
            - has_parents: bool -- whether data has hierarchical parent field
            - has_source_target: bool -- whether data has source/target flow fields
            - has_low_high: bool -- whether data has low/high range fields
            - has_base_value: bool -- whether data has a base value for sensitivity
            - is_2d_matrix: bool -- whether data is a 2D numeric matrix
            - values_are_bridge: bool -- whether values represent a waterfall bridge
            - prefer_sunburst: bool -- prefer sunburst over treemap for hierarchy

    Returns:
        ChartRecommendation with chart_type, confidence (0-1), and reason string.
    """
    # 1. Source/target flow -> sankey
    if data.get("has_source_target"):
        return ChartRecommendation(
            chart_type="sankey",
            confidence=0.9,
            reason="Data has source/target flow relationships",
        )

    # 2. Date ranges (start/end) -> gantt
    if data.get("has_dates") and data.get("has_date_ranges"):
        return ChartRecommendation(
            chart_type="gantt",
            confidence=0.9,
            reason="Data has start/end date ranges suitable for timeline",
        )

    # 3. Hierarchical parents -> treemap or sunburst
    if data.get("has_parents"):
        if data.get("prefer_sunburst"):
            return ChartRecommendation(
                chart_type="sunburst",
                confidence=0.85,
                reason="Hierarchical data with sunburst preference",
            )
        return ChartRecommendation(
            chart_type="treemap",
            confidence=0.85,
            reason="Hierarchical data with parent-child relationships",
        )

    # 4. 2D matrix -> heatmap
    if data.get("is_2d_matrix"):
        return ChartRecommendation(
            chart_type="heatmap",
            confidence=0.9,
            reason="2D numeric matrix data suitable for heatmap",
        )

    # 5. Low/high ranges -> football_field or tornado
    if data.get("has_low_high"):
        if data.get("has_base_value"):
            return ChartRecommendation(
                chart_type="tornado",
                confidence=0.85,
                reason="Range data with base value for sensitivity tornado",
            )
        return ChartRecommendation(
            chart_type="football_field",
            confidence=0.85,
            reason="Range data with low/high values for valuation comparison",
        )

    # 6. Bridge pattern -> waterfall
    if data.get("values_are_bridge"):
        return ChartRecommendation(
            chart_type="waterfall",
            confidence=0.85,
            reason="Values follow bridge/waterfall pattern (incremental changes)",
        )

    # 7-10. Standard chart selection based on series/category counts
    series_count = data.get("series_count", 0)
    category_count = data.get("category_count", 0)
    has_dates = data.get("has_dates", False)

    # 7. Single series, few categories -> pie
    if series_count == 1 and category_count <= 6:
        return ChartRecommendation(
            chart_type="pie",
            confidence=0.7,
            reason="Single series with few categories suits proportional display",
        )

    # 8. Single series, many categories -> bar
    if series_count == 1 and category_count > 6:
        return ChartRecommendation(
            chart_type="bar",
            confidence=0.75,
            reason="Single series with many categories suits bar chart",
        )

    # 9. Multiple series with dates -> line
    if series_count > 1 and has_dates:
        return ChartRecommendation(
            chart_type="line",
            confidence=0.8,
            reason="Multiple series with time-based categories suits line chart",
        )

    # 10. Multiple series without dates -> grouped_bar
    if series_count > 1:
        return ChartRecommendation(
            chart_type="grouped_bar",
            confidence=0.75,
            reason="Multiple series with categorical data suits grouped bar",
        )

    # 11. Default fallback -> bar
    return ChartRecommendation(
        chart_type="bar",
        confidence=0.5,
        reason="Default recommendation: bar chart is versatile for most data",
    )
