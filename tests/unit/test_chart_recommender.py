"""Tests for chart type recommender -- rule-based chart type suggestion."""

from __future__ import annotations

import pytest

from deckforge.charts.recommender import ChartRecommendation, recommend_chart_type


# ── Single series tests ──────────────────────────────────────────────────────


class TestSingleSeriesRecommendation:
    def test_single_series_few_categories_recommends_pie(self):
        """Single series with <=6 categories recommends 'pie'."""
        result = recommend_chart_type({"series_count": 1, "category_count": 5})
        assert result.chart_type == "pie"

    def test_single_series_many_categories_recommends_bar(self):
        """Single series with >6 categories recommends 'bar'."""
        result = recommend_chart_type({"series_count": 1, "category_count": 10})
        assert result.chart_type == "bar"


# ── Multi series tests ───────────────────────────────────────────────────────


class TestMultiSeriesRecommendation:
    def test_multi_series_with_dates_recommends_line(self):
        """Multiple series with time-like categories recommends 'line'."""
        result = recommend_chart_type(
            {"series_count": 3, "category_count": 12, "has_dates": True}
        )
        assert result.chart_type == "line"

    def test_multi_series_non_time_recommends_grouped_bar(self):
        """Multiple series with non-time categories recommends 'grouped_bar'."""
        result = recommend_chart_type(
            {"series_count": 2, "category_count": 5, "has_dates": False}
        )
        assert result.chart_type == "grouped_bar"


# ── Specialized chart tests ──────────────────────────────────────────────────


class TestSpecializedRecommendation:
    def test_source_target_recommends_sankey(self):
        """Data with source/target/value fields recommends 'sankey'."""
        result = recommend_chart_type({"has_source_target": True})
        assert result.chart_type == "sankey"

    def test_date_ranges_recommends_gantt(self):
        """Data with start/end date fields recommends 'gantt'."""
        result = recommend_chart_type({"has_dates": True, "has_date_ranges": True})
        assert result.chart_type == "gantt"

    def test_low_high_recommends_football_field(self):
        """Data with low/high range fields recommends 'football_field'."""
        result = recommend_chart_type({"has_low_high": True})
        assert result.chart_type == "football_field"

    def test_2d_matrix_recommends_heatmap(self):
        """2D matrix data recommends 'heatmap'."""
        result = recommend_chart_type({"is_2d_matrix": True})
        assert result.chart_type == "heatmap"

    def test_parents_recommends_treemap(self):
        """Data with parents field recommends 'treemap'."""
        result = recommend_chart_type({"has_parents": True})
        assert result.chart_type == "treemap"

    def test_bridge_pattern_recommends_waterfall(self):
        """Data with categories + single values (bridge pattern) recommends 'waterfall'."""
        result = recommend_chart_type({"values_are_bridge": True})
        assert result.chart_type == "waterfall"

    def test_low_high_with_base_value_recommends_tornado(self):
        """Data with low/high and base_value recommends 'tornado'."""
        result = recommend_chart_type({"has_low_high": True, "has_base_value": True})
        assert result.chart_type == "tornado"

    def test_parents_with_prefer_sunburst_recommends_sunburst(self):
        """Data with parents and prefer_sunburst=True recommends 'sunburst'."""
        result = recommend_chart_type(
            {"has_parents": True, "prefer_sunburst": True}
        )
        assert result.chart_type == "sunburst"


# ── Result structure tests ───────────────────────────────────────────────────


class TestChartRecommendationStructure:
    def test_recommendation_has_chart_type(self):
        result = recommend_chart_type({"series_count": 1, "category_count": 3})
        assert isinstance(result.chart_type, str)

    def test_recommendation_has_confidence(self):
        result = recommend_chart_type({"series_count": 1, "category_count": 3})
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0

    def test_recommendation_has_reason(self):
        result = recommend_chart_type({"series_count": 1, "category_count": 3})
        assert isinstance(result.reason, str)
        assert len(result.reason) > 0

    def test_default_recommends_bar(self):
        """Empty or ambiguous data defaults to 'bar'."""
        result = recommend_chart_type({})
        assert result.chart_type == "bar"
