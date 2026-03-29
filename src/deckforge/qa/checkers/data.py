"""Data integrity checker -- chart data validation, table totals, percentage sums."""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

from deckforge.qa.types import QAIssue

if TYPE_CHECKING:
    from deckforge.ir.presentation import Presentation
    from deckforge.layout.types import LayoutResult
    from deckforge.themes.types import ResolvedTheme

logger = logging.getLogger(__name__)

# Tolerance for percentage sum checks (1% of 100)
_PERCENTAGE_TOLERANCE = 1.0


class DataIntegrityChecker:
    """Check data integrity in a presentation.

    Checks:
        - Chart data series values are numeric, no NaN
        - Table elements with "total" row: sum matches
        - Percentage columns/pie charts: values sum to ~100 (within 1% tolerance)
    """

    def check(
        self,
        presentation: Presentation,
        layout_results: list[LayoutResult],
        theme: ResolvedTheme,
    ) -> list[QAIssue]:
        """Run data integrity checks on the presentation."""
        issues: list[QAIssue] = []

        for idx, slide in enumerate(presentation.slides):
            for elem in slide.elements:
                etype = getattr(elem, "type", None)

                if etype == "chart":
                    issues.extend(self._check_chart(idx, elem))
                elif etype == "table":
                    issues.extend(self._check_table(idx, elem))

        return issues

    def _check_chart(self, slide_idx: int, elem) -> list[QAIssue]:
        """Check chart element data integrity."""
        issues: list[QAIssue] = []
        chart_data = getattr(elem, "chart_data", None)
        if chart_data is None:
            return issues

        chart_type = getattr(chart_data, "chart_type", None)

        # Check for NaN in series data
        series_list = getattr(chart_data, "series", None)
        if series_list:
            for series in series_list:
                values = getattr(series, "values", [])
                for i, val in enumerate(values):
                    if val is not None and isinstance(val, float) and math.isnan(val):
                        issues.append(
                            QAIssue(
                                type="nan_data_value",
                                severity="error",
                                slide_index=slide_idx,
                                region=None,
                                message=(
                                    f"NaN value in series '{series.name}' "
                                    f"at index {i}"
                                ),
                                details={
                                    "series_name": series.name,
                                    "value_index": i,
                                },
                            )
                        )

        # Check pie/donut percentage sums
        if chart_type in ("pie", "donut"):
            values = getattr(chart_data, "values", [])
            if values:
                total = sum(v for v in values if v is not None)
                if abs(total - 100) > _PERCENTAGE_TOLERANCE:
                    issues.append(
                        QAIssue(
                            type="percentage_sum_wrong",
                            severity="warning",
                            slide_index=slide_idx,
                            region=None,
                            message=(
                                f"Pie/donut chart values sum to {total}, "
                                f"expected ~100 (tolerance {_PERCENTAGE_TOLERANCE}%)"
                            ),
                            details={
                                "actual_sum": total,
                                "expected": 100,
                                "tolerance": _PERCENTAGE_TOLERANCE,
                            },
                        )
                    )

        return issues

    def _check_table(self, slide_idx: int, elem) -> list[QAIssue]:
        """Check table element data integrity."""
        issues: list[QAIssue] = []
        content = getattr(elem, "content", None)
        if content is None:
            return issues

        headers = getattr(content, "headers", [])
        rows = getattr(content, "rows", [])
        footer_row = getattr(content, "footer_row", None)

        if not rows:
            return issues

        # Check if footer_row has "total" and verify sums
        if footer_row:
            for col_idx, header in enumerate(headers):
                if header.lower() in ("total", "sum", "grand total"):
                    continue
                # Check if the footer value matches the column sum
                if col_idx < len(footer_row):
                    footer_val = footer_row[col_idx]
                    if isinstance(footer_val, (int, float)):
                        col_sum = 0.0
                        all_numeric = True
                        for row in rows:
                            if col_idx < len(row):
                                val = row[col_idx]
                                if isinstance(val, (int, float)):
                                    col_sum += val
                                else:
                                    all_numeric = False
                                    break
                        if all_numeric and abs(col_sum - footer_val) > 0.01:
                            issues.append(
                                QAIssue(
                                    type="table_total_mismatch",
                                    severity="error",
                                    slide_index=slide_idx,
                                    region=None,
                                    message=(
                                        f"Table column '{header}' footer "
                                        f"({footer_val}) does not match "
                                        f"column sum ({col_sum})"
                                    ),
                                    details={
                                        "column": header,
                                        "footer_value": footer_val,
                                        "computed_sum": col_sum,
                                    },
                                )
                            )

        return issues
