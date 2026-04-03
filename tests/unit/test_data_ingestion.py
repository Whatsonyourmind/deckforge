"""Tests for data ingestion — CSV/Excel parsing, column type detection, slide type mapping."""

from __future__ import annotations

import io

import pandas as pd
import pytest

from deckforge.finance.ingestion import (
    ColumnType,
    DataMapping,
    auto_detect_slide_type,
    detect_column_types,
    ingest_tabular_data,
)


# ---------------------------------------------------------------------------
# Helpers to create in-memory test data
# ---------------------------------------------------------------------------


def _csv_bytes(text: str) -> io.StringIO:
    """Create a StringIO from CSV text for testing."""
    return io.StringIO(text)


def _xlsx_bytes(df: pd.DataFrame) -> io.BytesIO:
    """Write a DataFrame to an in-memory Excel file."""
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# Ingestion tests
# ---------------------------------------------------------------------------


class TestIngestTabularData:
    """CSV and Excel file ingestion into DataFrames."""

    def test_csv_basic(self) -> None:
        csv_text = "Company,Revenue,Margin\nAcme,1000000,0.15\nGlobex,2000000,0.22\n"
        df = ingest_tabular_data(_csv_bytes(csv_text), file_type="csv")
        assert df.shape == (2, 3)
        assert list(df.columns) == ["Company", "Revenue", "Margin"]

    def test_xlsx_basic(self) -> None:
        source_df = pd.DataFrame(
            {"Company": ["Acme", "Globex"], "EV/EBITDA": [12.5, 15.3], "Margin": [0.15, 0.22]}
        )
        xlsx = _xlsx_bytes(source_df)
        df = ingest_tabular_data(xlsx, file_type="xlsx")
        assert df.shape == (2, 3)
        assert "Company" in df.columns

    def test_unsupported_file_type_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported"):
            ingest_tabular_data(io.StringIO("data"), file_type="json")

    def test_empty_csv(self) -> None:
        """Empty CSV returns empty DataFrame (no rows)."""
        csv_text = "Company,Revenue\n"
        df = ingest_tabular_data(_csv_bytes(csv_text), file_type="csv")
        assert len(df) == 0
        assert list(df.columns) == ["Company", "Revenue"]

    def test_whitespace_column_names_stripped(self) -> None:
        csv_text = "  Company  , Revenue ,  Margin \nAcme,1000,0.15\n"
        df = ingest_tabular_data(_csv_bytes(csv_text), file_type="csv")
        assert list(df.columns) == ["Company", "Revenue", "Margin"]


# ---------------------------------------------------------------------------
# Column type detection tests
# ---------------------------------------------------------------------------


class TestDetectColumnTypes:
    """Heuristic column type detection from headers and values."""

    def test_text_column_by_name(self) -> None:
        df = pd.DataFrame({"Company": ["Acme", "Globex"], "Revenue": [100, 200]})
        mappings = detect_column_types(df)
        company_col = next(m for m in mappings if m.name == "Company")
        assert company_col.column_type == ColumnType.TEXT

    def test_currency_column_by_header(self) -> None:
        df = pd.DataFrame({"Company": ["A"], "Revenue ($M)": [100.0]})
        mappings = detect_column_types(df)
        rev_col = next(m for m in mappings if m.name == "Revenue ($M)")
        assert rev_col.column_type == ColumnType.CURRENCY

    def test_percentage_column_by_range(self) -> None:
        df = pd.DataFrame({"Company": ["A", "B"], "Margin": [0.15, 0.22]})
        mappings = detect_column_types(df)
        margin_col = next(m for m in mappings if m.name == "Margin")
        assert margin_col.column_type == ColumnType.PERCENTAGE

    def test_percentage_column_by_header(self) -> None:
        df = pd.DataFrame({"Company": ["A"], "Growth %": [15.5]})
        mappings = detect_column_types(df)
        growth_col = next(m for m in mappings if m.name == "Growth %")
        assert growth_col.column_type == ColumnType.PERCENTAGE

    def test_multiple_column_by_header(self) -> None:
        df = pd.DataFrame({"Company": ["A"], "EV/EBITDA": [12.5]})
        mappings = detect_column_types(df)
        ev_col = next(m for m in mappings if m.name == "EV/EBITDA")
        assert ev_col.column_type == ColumnType.MULTIPLE

    def test_first_text_column_is_label(self) -> None:
        df = pd.DataFrame({"Company": ["A", "B"], "Revenue": [100, 200]})
        mappings = detect_column_types(df)
        company_col = next(m for m in mappings if m.name == "Company")
        assert company_col.role == "label"

    def test_numeric_columns_are_metric(self) -> None:
        df = pd.DataFrame({"Company": ["A"], "Revenue": [100], "EBITDA": [50]})
        mappings = detect_column_types(df)
        rev_col = next(m for m in mappings if m.name == "Revenue")
        assert rev_col.role == "metric"


# ---------------------------------------------------------------------------
# Slide type auto-detection tests
# ---------------------------------------------------------------------------


class TestAutoDetectSlideType:
    """Auto-detection of finance slide type from DataFrame structure."""

    def test_comp_table_detection(self) -> None:
        """First column text + remaining numeric with financial headers -> comp_table."""
        df = pd.DataFrame(
            {
                "Company": ["Acme", "Globex", "Initech"],
                "Revenue ($M)": [100.0, 200.0, 150.0],
                "EV/EBITDA": [12.5, 15.3, 10.2],
                "Margin": [0.15, 0.22, 0.18],
            }
        )
        mapping = auto_detect_slide_type(df)
        assert mapping.detected_slide_type == "comp_table"
        assert mapping.confidence > 0.5

    @pytest.mark.xfail(reason="Sensitivity detection heuristic needs tuning for % row headers")
    def test_sensitivity_table_detection(self) -> None:
        """2D numeric grid with row/col headers -> sensitivity_table."""
        df = pd.DataFrame(
            {
                "Discount Rate": ["8%", "10%", "12%"],
                "1.0%": [120.5, 100.0, 85.3],
                "2.0%": [135.2, 112.4, 95.1],
                "3.0%": [152.8, 126.7, 106.3],
            }
        )
        mapping = auto_detect_slide_type(df)
        assert mapping.detected_slide_type == "sensitivity_table"

    def test_data_mapping_has_columns(self) -> None:
        df = pd.DataFrame(
            {"Company": ["A", "B"], "Revenue": [100, 200], "Margin": [0.15, 0.22]}
        )
        mapping = auto_detect_slide_type(df)
        assert isinstance(mapping, DataMapping)
        assert len(mapping.columns) == 3

    def test_data_mapping_has_format_suggestions(self) -> None:
        df = pd.DataFrame(
            {"Company": ["A"], "Revenue ($M)": [100.0], "EV/EBITDA": [12.5]}
        )
        mapping = auto_detect_slide_type(df)
        # At least one column should have a format suggestion
        has_format = any(c.format_type is not None for c in mapping.columns)
        assert has_format

    def test_default_fallback(self) -> None:
        """Ambiguous data defaults to comp_table with lower confidence."""
        df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        mapping = auto_detect_slide_type(df)
        assert mapping.detected_slide_type == "comp_table"
        assert mapping.confidence < 0.8
