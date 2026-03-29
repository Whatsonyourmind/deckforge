"""Data ingestion — CSV/Excel parsing, column type detection, and finance slide type auto-mapping.

Provides utilities to load tabular financial data from CSV/Excel into structured
DataFrames, auto-detect column types (currency, percentage, multiple, etc.), and
suggest the most appropriate finance slide type based on data structure.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import BinaryIO

import pandas as pd

from deckforge.finance.formatter import NumberFormat


class ColumnType(str, Enum):
    """Detected column data type for financial data."""

    TEXT = "text"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    MULTIPLE = "multiple"
    BASIS_POINTS = "basis_points"
    NUMERIC = "numeric"
    DATE = "date"


# Mapping from ColumnType to NumberFormat for format suggestions.
_COLUMN_TO_FORMAT: dict[ColumnType, NumberFormat] = {
    ColumnType.CURRENCY: NumberFormat.CURRENCY,
    ColumnType.PERCENTAGE: NumberFormat.PERCENTAGE,
    ColumnType.MULTIPLE: NumberFormat.MULTIPLE,
    ColumnType.BASIS_POINTS: NumberFormat.BASIS_POINTS,
    ColumnType.NUMERIC: NumberFormat.PLAIN,
}


@dataclass
class ColumnMapping:
    """Detected metadata for a single DataFrame column."""

    name: str
    column_type: ColumnType
    format_type: NumberFormat | None = None
    role: str = "metric"  # "label", "metric", "date", or "ignore"


@dataclass
class DataMapping:
    """Result of auto-detecting the finance slide type from data structure."""

    detected_slide_type: str
    columns: list[ColumnMapping] = field(default_factory=list)
    confidence: float = 0.0
    notes: str = ""


# ---------------------------------------------------------------------------
# Header keyword patterns for heuristic column type detection
# ---------------------------------------------------------------------------

_TEXT_KEYWORDS = re.compile(
    r"(company|name|ticker|symbol|entity|issuer|description|sector|industry)",
    re.IGNORECASE,
)
_MULTIPLE_KEYWORDS = re.compile(
    r"(ev/ebitda|p/e|p/b|ev/revenue|ev/sales|multiple|ratio\b)",
    re.IGNORECASE,
)
_CURRENCY_KEYWORDS = re.compile(
    r"(\$|revenue|market\s*cap|value|price|ebitda|income|earnings|cash\s*flow|debt|equity\s*value)",
    re.IGNORECASE,
)
_PERCENTAGE_KEYWORDS = re.compile(
    r"(%|margin|growth|yield|rate|return|irr|cagr|wacc)",
    re.IGNORECASE,
)
_DATE_KEYWORDS = re.compile(r"(date|year|period|quarter|month)", re.IGNORECASE)

# Sensitivity table: header looks like a number (e.g., "8%", "1.0%", "10.5")
_NUMERIC_HEADER = re.compile(r"^[\d.]+%?$")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def ingest_tabular_data(
    source: str | bytes | BinaryIO,
    file_type: str = "auto",
) -> pd.DataFrame:
    """Parse a tabular data source into a pandas DataFrame.

    Args:
        source: File path (str), raw bytes, BytesIO, or StringIO.
        file_type: One of "csv", "tsv", "xlsx", "auto". If "auto", inferred from path extension.

    Returns:
        DataFrame with whitespace-stripped column names.

    Raises:
        ValueError: If file type is unsupported.
    """
    # Auto-detect from path extension when source is a string path.
    if file_type == "auto" and isinstance(source, str):
        lower = source.lower()
        if lower.endswith(".csv"):
            file_type = "csv"
        elif lower.endswith(".tsv"):
            file_type = "tsv"
        elif lower.endswith((".xlsx", ".xls")):
            file_type = "xlsx"
        else:
            raise ValueError(f"Unsupported file extension for auto-detect: {source}")

    if file_type == "csv":
        df = pd.read_csv(source)
    elif file_type == "tsv":
        df = pd.read_csv(source, sep="\t")
    elif file_type == "xlsx":
        df = pd.read_excel(source, engine="openpyxl")
    else:
        raise ValueError(f"Unsupported file type: '{file_type}'. Use 'csv', 'tsv', or 'xlsx'.")

    # Strip whitespace from column names.
    df.columns = [str(c).strip() for c in df.columns]
    return df


def detect_column_types(df: pd.DataFrame) -> list[ColumnMapping]:
    """Detect column types and roles from headers and values.

    Heuristic priority:
    1. Header keywords (most reliable)
    2. Value inspection (fallback)
    3. First text column -> role="label", others -> role="metric"
    """
    mappings: list[ColumnMapping] = []
    found_label = False

    for col_name in df.columns:
        col_type = _detect_single_column_type(col_name, df[col_name])
        role = "metric"  # Default.

        if col_type == ColumnType.TEXT:
            if not found_label:
                role = "label"
                found_label = True
            else:
                role = "metric"
        elif col_type == ColumnType.DATE:
            role = "date"

        format_type = _COLUMN_TO_FORMAT.get(col_type)

        mappings.append(
            ColumnMapping(
                name=col_name,
                column_type=col_type,
                format_type=format_type,
                role=role,
            )
        )

    return mappings


def auto_detect_slide_type(df: pd.DataFrame) -> DataMapping:
    """Detect the most appropriate finance slide type from DataFrame structure.

    Decision logic (ordered by specificity):
    1. Sensitivity table: first column text headers, remaining columns have numeric headers
    2. Comp table: first column is text + remaining are numeric with financial headers
    3. Sankey: columns include "source"/"from" and "target"/"to" and "value"
    4. Gantt: columns include "start" and "end"/"finish"
    5. Football field: columns include "low"/"min" and "high"/"max"
    6. Default: comp_table with lower confidence
    """
    columns = detect_column_types(df)
    col_names_lower = [c.lower() for c in df.columns]

    # --- Check for sensitivity table ---
    if _is_sensitivity_table(df, columns):
        return DataMapping(
            detected_slide_type="sensitivity_table",
            columns=columns,
            confidence=0.85,
            notes="2D numeric grid with row/column headers detected",
        )

    # --- Check for sankey data ---
    has_source = any(k in col_names_lower for k in ("source", "from"))
    has_target = any(k in col_names_lower for k in ("target", "to"))
    has_value = "value" in col_names_lower
    if has_source and has_target and has_value:
        return DataMapping(
            detected_slide_type="chart:sankey",
            columns=columns,
            confidence=0.80,
            notes="Source/target/value columns detected",
        )

    # --- Check for gantt data ---
    has_start = "start" in col_names_lower
    has_end = any(k in col_names_lower for k in ("end", "finish"))
    if has_start and has_end:
        return DataMapping(
            detected_slide_type="chart:gantt",
            columns=columns,
            confidence=0.75,
            notes="Start/end columns detected",
        )

    # --- Check for football field data ---
    has_low = any(k in col_names_lower for k in ("low", "min"))
    has_high = any(k in col_names_lower for k in ("high", "max"))
    if has_low and has_high:
        return DataMapping(
            detected_slide_type="chart:football_field",
            columns=columns,
            confidence=0.70,
            notes="Low/high range columns detected",
        )

    # --- Check for comp table (most common) ---
    if _is_comp_table(columns):
        return DataMapping(
            detected_slide_type="comp_table",
            columns=columns,
            confidence=0.80,
            notes="First column text labels with numeric financial metrics",
        )

    # --- Default fallback ---
    return DataMapping(
        detected_slide_type="comp_table",
        columns=columns,
        confidence=0.40,
        notes="Ambiguous structure, defaulting to comp_table",
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _detect_single_column_type(name: str, series: pd.Series) -> ColumnType:
    """Detect the type of a single column from its header name and values."""
    # 1. Header keyword matching (highest priority).
    if _TEXT_KEYWORDS.search(name):
        return ColumnType.TEXT
    if _MULTIPLE_KEYWORDS.search(name):
        return ColumnType.MULTIPLE
    if _CURRENCY_KEYWORDS.search(name):
        return ColumnType.CURRENCY
    if _PERCENTAGE_KEYWORDS.search(name):
        return ColumnType.PERCENTAGE
    if _DATE_KEYWORDS.search(name):
        return ColumnType.DATE

    # 2. Value-based detection.
    if series.dtype == object:
        # Check if all non-null values are strings (text column).
        non_null = series.dropna()
        if len(non_null) > 0 and all(isinstance(v, str) for v in non_null):
            return ColumnType.TEXT

    if pd.api.types.is_numeric_dtype(series):
        non_null = series.dropna()
        if len(non_null) > 0:
            # Check for percentage range (0 to 1 exclusive).
            min_val = non_null.min()
            max_val = non_null.max()
            if 0 <= min_val and max_val <= 1 and max_val > 0:
                return ColumnType.PERCENTAGE
            return ColumnType.NUMERIC

    return ColumnType.NUMERIC


def _is_sensitivity_table(df: pd.DataFrame, columns: list[ColumnMapping]) -> bool:
    """Check if the DataFrame looks like a sensitivity/data table.

    Pattern: first column is text (row headers), remaining column names
    look like numeric values (e.g., "1.0%", "2.0%", "8%").
    """
    if len(df.columns) < 3:
        return False

    # First column should be text-like (row headers).
    first_col = columns[0]
    if first_col.column_type not in (ColumnType.TEXT,):
        # Also accept if the first column contains string values even if header isn't text-keyword.
        if df.iloc[:, 0].dtype != object:
            return False

    # Remaining column names should look numeric (e.g., "1.0%", "10.5").
    remaining_headers = list(df.columns[1:])
    numeric_header_count = sum(1 for h in remaining_headers if _NUMERIC_HEADER.match(str(h)))
    return numeric_header_count >= len(remaining_headers) * 0.5


def _is_comp_table(columns: list[ColumnMapping]) -> bool:
    """Check if the columns look like a comp table (first text, rest numeric)."""
    if not columns:
        return False

    has_label = any(c.role == "label" for c in columns)
    has_metrics = sum(1 for c in columns if c.role == "metric") >= 1

    return has_label and has_metrics
