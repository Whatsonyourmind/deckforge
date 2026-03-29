"""Finance data processing layer — formatting, conditional colors, and data ingestion."""

from deckforge.finance.formatter import FinancialFormatter, NumberFormat
from deckforge.finance.conditional import ConditionalFormatter
from deckforge.finance.ingestion import ingest_tabular_data, auto_detect_slide_type, DataMapping

__all__ = [
    "FinancialFormatter",
    "NumberFormat",
    "ConditionalFormatter",
    "ingest_tabular_data",
    "auto_detect_slide_type",
    "DataMapping",
]
