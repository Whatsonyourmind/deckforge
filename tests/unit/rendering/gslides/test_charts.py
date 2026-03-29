"""Tests for Google Sheets chart builder."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from deckforge.rendering.gslides.charts import SheetsChartBuilder


def _mock_services():
    """Create mock Sheets, Drive services and credentials."""
    creds = MagicMock()
    sheets_svc = MagicMock()
    drive_svc = MagicMock()
    return creds, sheets_svc, drive_svc


class TestSheetsChartBuilder:
    @patch("deckforge.rendering.gslides.charts.build")
    def test_init(self, mock_build):
        mock_build.return_value = MagicMock()
        builder = SheetsChartBuilder(MagicMock(), "pres_123")
        assert builder.presentation_id == "pres_123"
        assert builder.spreadsheet_id is None

    @patch("deckforge.rendering.gslides.charts.build")
    def test_create_spreadsheet(self, mock_build):
        sheets_svc = MagicMock()
        drive_svc = MagicMock()
        mock_build.side_effect = [sheets_svc, drive_svc]

        sheets_svc.spreadsheets().create().execute.return_value = {
            "spreadsheetId": "sheet_abc"
        }

        builder = SheetsChartBuilder(MagicMock(), "pres_123")
        result = builder.create_spreadsheet()
        assert result == "sheet_abc"
        assert builder.spreadsheet_id == "sheet_abc"

    @patch("deckforge.rendering.gslides.charts.build")
    def test_add_chart_supported_type(self, mock_build):
        sheets_svc = MagicMock()
        drive_svc = MagicMock()
        mock_build.side_effect = [sheets_svc, drive_svc]

        builder = SheetsChartBuilder(MagicMock(), "pres_123")
        builder.spreadsheet_id = "sheet_abc"

        # Mock addSheet response
        sheets_svc.spreadsheets().batchUpdate().execute.return_value = {
            "replies": [
                {"addSheet": {"properties": {"sheetId": 1}}},
                {"addChart": {"chart": {"chartId": 42}}},
            ]
        }

        chart_data = {
            "categories": ["Q1", "Q2", "Q3"],
            "series": [{"name": "Revenue", "values": [100, 200, 300]}],
        }
        chart_id = builder.add_chart(chart_data, "bar", "Revenue by Quarter")
        assert chart_id == 42

    @patch("deckforge.rendering.gslides.charts.build")
    def test_add_chart_unsupported_type_returns_none(self, mock_build):
        sheets_svc = MagicMock()
        drive_svc = MagicMock()
        mock_build.side_effect = [sheets_svc, drive_svc]

        builder = SheetsChartBuilder(MagicMock(), "pres_123")
        builder.spreadsheet_id = "sheet_abc"

        chart_data = {"categories": ["A"], "series": []}
        result = builder.add_chart(chart_data, "waterfall", "Test")
        assert result is None

    @patch("deckforge.rendering.gslides.charts.build")
    def test_add_chart_heatmap_unsupported(self, mock_build):
        mock_build.return_value = MagicMock()
        builder = SheetsChartBuilder(MagicMock(), "pres_123")
        builder.spreadsheet_id = "sheet_abc"

        result = builder.add_chart({}, "heatmap", "Heat")
        assert result is None

    @patch("deckforge.rendering.gslides.charts.build")
    def test_add_chart_sankey_unsupported(self, mock_build):
        mock_build.return_value = MagicMock()
        builder = SheetsChartBuilder(MagicMock(), "pres_123")
        builder.spreadsheet_id = "sheet_abc"

        result = builder.add_chart({}, "sankey", "Flow")
        assert result is None

    @patch("deckforge.rendering.gslides.charts.build")
    def test_chart_type_mapping(self, mock_build):
        mock_build.return_value = MagicMock()
        builder = SheetsChartBuilder(MagicMock(), "pres_123")

        from deckforge.rendering.gslides.charts import SHEETS_CHART_TYPE_MAP

        assert SHEETS_CHART_TYPE_MAP["bar"] == "BAR"
        assert SHEETS_CHART_TYPE_MAP["line"] == "LINE"
        assert SHEETS_CHART_TYPE_MAP["pie"] == "PIE"
        assert SHEETS_CHART_TYPE_MAP["scatter"] == "SCATTER"
        assert SHEETS_CHART_TYPE_MAP["area"] == "AREA"
        assert SHEETS_CHART_TYPE_MAP["combo"] == "COMBO"

    @patch("deckforge.rendering.gslides.charts.build")
    def test_get_slides_chart_request(self, mock_build):
        mock_build.return_value = MagicMock()
        builder = SheetsChartBuilder(MagicMock(), "pres_123")
        builder.spreadsheet_id = "sheet_abc"

        req = builder.get_slides_chart_request(42, "page_1", 1.0, 2.0, 8.0, 5.0)
        assert "createSheetsChart" in req
        csc = req["createSheetsChart"]
        assert csc["spreadsheetId"] == "sheet_abc"
        assert csc["chartId"] == 42
        assert csc["linkingMode"] == "LINKED"
        assert "elementProperties" in csc

    @patch("deckforge.rendering.gslides.charts.build")
    def test_get_static_image_request(self, mock_build):
        mock_build.return_value = MagicMock()
        builder = SheetsChartBuilder(MagicMock(), "pres_123")

        req = builder.get_static_image_request(
            "https://example.com/chart.png", "page_1", 1.0, 2.0, 8.0, 5.0
        )
        assert "createImage" in req
        assert req["createImage"]["url"] == "https://example.com/chart.png"
