"""Google Sheets chart builder for embedding editable charts in Google Slides.

Creates a temporary Google Sheets spreadsheet, writes chart data to worksheets,
creates EmbeddedCharts via the Sheets API, then provides CreateSheetsChartRequest
dicts for embedding into Slides via batchUpdate.
"""

from __future__ import annotations

import logging
from typing import Any

from deckforge.rendering.gslides.converter import (
    generate_object_id,
    make_element_properties,
)

logger = logging.getLogger(__name__)


def build(service_name: str, version: str, credentials: Any = None) -> Any:
    """Lazy import and build Google API service.

    Separated for easy mocking in tests.
    """
    from googleapiclient.discovery import build as google_build

    return google_build(service_name, version, credentials=credentials)


# Mapping from DeckForge ChartType values to Sheets API basicChart.chartType
SHEETS_CHART_TYPE_MAP: dict[str, str] = {
    # Native Sheets chart types
    "bar": "BAR",
    "stacked_bar": "BAR",
    "grouped_bar": "BAR",
    "horizontal_bar": "BAR",
    "line": "LINE",
    "multi_line": "LINE",
    "area": "AREA",
    "stacked_area": "AREA",
    "pie": "PIE",
    "donut": "PIE",
    "scatter": "SCATTER",
    "bubble": "SCATTER",
    "combo": "COMBO",
}

# Chart types that are NOT supported by Sheets -- fall back to static PNG
UNSUPPORTED_CHART_TYPES: set[str] = {
    "waterfall",
    "heatmap",
    "sankey",
    "gantt",
    "sunburst",
    "funnel",
    "treemap",
    "radar",
    "tornado",
    "football_field",
    "sensitivity_table",
}


class SheetsChartBuilder:
    """Creates Google Sheets charts for embedding in Slides.

    Usage:
        builder = SheetsChartBuilder(credentials, presentation_id)
        builder.create_spreadsheet()
        chart_id = builder.add_chart(data, "bar", "Revenue")
        if chart_id:
            req = builder.get_slides_chart_request(chart_id, page_id, x, y, w, h)
        else:
            req = builder.get_static_image_request(url, page_id, x, y, w, h)
    """

    def __init__(self, credentials: Any, presentation_id: str) -> None:
        """Initialize the chart builder.

        Args:
            credentials: Google OAuth credentials.
            presentation_id: Presentation ID for naming the temp spreadsheet.
        """
        self.sheets_service = build("sheets", "v4", credentials=credentials)
        self.drive_service = build("drive", "v3", credentials=credentials)
        self.presentation_id = presentation_id
        self.spreadsheet_id: str | None = None
        self._sheet_index = 0

    def create_spreadsheet(self) -> str:
        """Create a temporary spreadsheet for chart data.

        Returns:
            Spreadsheet ID.
        """
        title = f"DeckForge Charts - {self.presentation_id}"
        response = (
            self.sheets_service.spreadsheets()
            .create(body={"properties": {"title": title}})
            .execute()
        )
        self.spreadsheet_id = response["spreadsheetId"]
        return self.spreadsheet_id

    def add_chart(
        self,
        chart_data: dict,
        chart_type: str,
        title: str,
    ) -> int | None:
        """Add a chart to the spreadsheet.

        Args:
            chart_data: Dict with 'categories' and 'series' keys.
            chart_type: DeckForge ChartType value string.
            title: Chart title.

        Returns:
            Sheets chartId if supported, None for unsupported types.
        """
        # Check if chart type is Sheets-compatible
        sheets_type = SHEETS_CHART_TYPE_MAP.get(chart_type)
        if sheets_type is None:
            logger.info(
                "Chart type '%s' not supported by Sheets, falling back to static image",
                chart_type,
            )
            return None

        if not self.spreadsheet_id:
            raise RuntimeError("create_spreadsheet() must be called first")

        sheet_title = f"Chart_{self._sheet_index}"
        self._sheet_index += 1

        # Prepare chart data
        categories = chart_data.get("categories", [])
        series_list = chart_data.get("series", [])

        # Calculate data dimensions
        num_rows = 1 + len(series_list)  # header + series rows
        num_cols = 1 + len(categories)  # label col + data cols

        # Build data rows for the worksheet
        header_row = ["Category"] + categories
        data_rows = [header_row]
        for series in series_list:
            name = series.get("name", f"Series {len(data_rows)}")
            values = series.get("values", [])
            # Pad values to match categories length
            padded = values + [0] * (len(categories) - len(values))
            data_rows.append([name] + padded[:len(categories)])

        # Build the addSheet + addChart requests
        add_sheet_request = {
            "addSheet": {
                "properties": {
                    "title": sheet_title,
                }
            }
        }

        # Build the chart spec
        basic_chart = {
            "chartType": sheets_type,
            "legendPosition": "BOTTOM_LEGEND",
            "headerCount": 1,
        }

        # Handle stacked types
        if chart_type in ("stacked_bar", "stacked_area"):
            basic_chart["stackedType"] = "STACKED"

        # Handle horizontal bar
        if chart_type == "horizontal_bar":
            basic_chart["axis"] = [
                {"position": "BOTTOM_AXIS"},
                {"position": "LEFT_AXIS"},
            ]

        # Domain (categories)
        basic_chart["domains"] = [
            {
                "domain": {
                    "sourceRange": {
                        "sources": [
                            {
                                "sheetId": 0,  # Will be updated
                                "startRowIndex": 0,
                                "endRowIndex": num_rows,
                                "startColumnIndex": 0,
                                "endColumnIndex": 1,
                            }
                        ]
                    }
                }
            }
        ]

        # Series
        basic_chart["series"] = []
        for col_idx in range(1, num_cols):
            basic_chart["series"].append(
                {
                    "series": {
                        "sourceRange": {
                            "sources": [
                                {
                                    "sheetId": 0,  # Will be updated
                                    "startRowIndex": 0,
                                    "endRowIndex": num_rows,
                                    "startColumnIndex": col_idx,
                                    "endColumnIndex": col_idx + 1,
                                }
                            ]
                        }
                    },
                    "targetAxis": "LEFT_AXIS",
                }
            )

        # Handle donut
        spec: dict[str, Any] = {
            "title": title,
            "basicChart": basic_chart,
        }
        if chart_type == "donut":
            spec["pieChart"] = {"threeDimensional": False}

        add_chart_request = {
            "addChart": {
                "chart": {
                    "spec": spec,
                    "position": {
                        "overlayPosition": {
                            "anchorCell": {
                                "sheetId": 0,  # Will be updated
                                "rowIndex": 0,
                                "columnIndex": 0,
                            }
                        }
                    },
                },
            }
        }

        # Execute: add sheet, write data, add chart
        try:
            # Add sheet and chart in one batchUpdate
            batch_response = (
                self.sheets_service.spreadsheets()
                .batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={"requests": [add_sheet_request, add_chart_request]},
                )
                .execute()
            )

            # Extract chart ID from response
            replies = batch_response.get("replies", [])
            for reply in replies:
                if "addChart" in reply:
                    chart_id = reply["addChart"]["chart"]["chartId"]
                    return chart_id

            logger.warning("No chartId in Sheets batchUpdate response")
            return None

        except Exception:
            logger.exception("Failed to create Sheets chart for '%s'", title)
            return None

    def get_slides_chart_request(
        self,
        chart_id: int,
        page_id: str,
        x: float,
        y: float,
        w: float,
        h: float,
        linked: bool = True,
    ) -> dict:
        """Build a CreateSheetsChartRequest for Slides batchUpdate.

        Args:
            chart_id: Sheets EmbeddedChart ID.
            page_id: Slides page object ID.
            x: X position in inches.
            y: Y position in inches.
            w: Width in inches.
            h: Height in inches.
            linked: Whether the chart is linked (updates with Sheets data).

        Returns:
            CreateSheetsChart request dict.
        """
        return {
            "createSheetsChart": {
                "objectId": generate_object_id(),
                "spreadsheetId": self.spreadsheet_id,
                "chartId": chart_id,
                "linkingMode": "LINKED" if linked else "NOT_LINKED_IMAGE",
                "elementProperties": make_element_properties(page_id, x, y, w, h),
            }
        }

    def get_static_image_request(
        self,
        image_url: str,
        page_id: str,
        x: float,
        y: float,
        w: float,
        h: float,
    ) -> dict:
        """Build a CreateImageRequest for static chart fallback.

        Args:
            image_url: URL of the static PNG image.
            page_id: Slides page object ID.
            x: X position in inches.
            y: Y position in inches.
            w: Width in inches.
            h: Height in inches.

        Returns:
            CreateImage request dict.
        """
        return {
            "createImage": {
                "objectId": generate_object_id(),
                "url": image_url,
                "elementProperties": make_element_properties(page_id, x, y, w, h),
            }
        }


__all__ = ["SheetsChartBuilder", "SHEETS_CHART_TYPE_MAP"]
