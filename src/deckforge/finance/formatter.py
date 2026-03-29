"""Financial number formatter — stub for TDD RED phase."""

from __future__ import annotations

from enum import Enum


class NumberFormat(str, Enum):
    """Supported financial number format types."""

    CURRENCY = "currency"
    CURRENCY_FULL = "currency_full"
    PERCENTAGE = "percentage"
    MULTIPLE = "multiple"
    BASIS_POINTS = "basis_points"
    RATIO = "ratio"
    INTEGER = "integer"
    PLAIN = "plain"


class FinancialFormatter:
    """Financial number formatting — stub."""

    @staticmethod
    def currency(
        value: float,
        symbol: str = "$",
        precision: int = 1,
        compact: bool = True,
        negative_parens: bool = True,
    ) -> str:
        raise NotImplementedError

    @staticmethod
    def percentage(value: float, precision: int = 1, is_decimal: bool = True) -> str:
        raise NotImplementedError

    @staticmethod
    def multiple(value: float, precision: int = 1) -> str:
        raise NotImplementedError

    @staticmethod
    def basis_points(value: float, is_decimal: bool = True) -> str:
        raise NotImplementedError

    @staticmethod
    def ratio(value: float, precision: int = 2) -> str:
        raise NotImplementedError

    @staticmethod
    def auto_format(value: float, format_type: str | NumberFormat) -> str:
        raise NotImplementedError
