"""Data ingestion — stub for TDD RED phase."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import BinaryIO

import pandas as pd

from deckforge.finance.formatter import NumberFormat


class ColumnType(str, Enum):
    TEXT = "text"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    MULTIPLE = "multiple"
    BASIS_POINTS = "basis_points"
    NUMERIC = "numeric"
    DATE = "date"


@dataclass
class ColumnMapping:
    name: str
    column_type: ColumnType
    format_type: NumberFormat | None = None
    role: str = "metric"


@dataclass
class DataMapping:
    detected_slide_type: str
    columns: list[ColumnMapping] = field(default_factory=list)
    confidence: float = 0.0
    notes: str = ""


def ingest_tabular_data(
    source: str | bytes | BinaryIO, file_type: str = "auto"
) -> pd.DataFrame:
    raise NotImplementedError


def detect_column_types(df: pd.DataFrame) -> list[ColumnMapping]:
    raise NotImplementedError


def auto_detect_slide_type(df: pd.DataFrame) -> DataMapping:
    raise NotImplementedError
