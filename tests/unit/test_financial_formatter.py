"""Tests for FinancialFormatter — currency, percentage, multiple, basis_points, auto_format."""

from __future__ import annotations

import pytest

from deckforge.finance.formatter import FinancialFormatter, NumberFormat


class TestCurrencyFormatting:
    """Currency formatting with compact and full modes."""

    def test_compact_millions(self) -> None:
        assert FinancialFormatter.currency(1_234_567.89, compact=True) == "$1.2M"

    def test_compact_billions(self) -> None:
        assert FinancialFormatter.currency(2_500_000_000, compact=True) == "$2.5B"

    def test_full_format(self) -> None:
        assert FinancialFormatter.currency(1_234_567.89, compact=False) == "$1,234,567.89"

    def test_negative_compact_parens(self) -> None:
        assert FinancialFormatter.currency(-500_000, compact=True) == "($500.0K)"

    def test_small_value_no_suffix(self) -> None:
        assert FinancialFormatter.currency(750, compact=True) == "$750"

    def test_full_format_precision_default(self) -> None:
        """Full format uses precision parameter (default 1 for compact, 2 for full)."""
        result = FinancialFormatter.currency(1_234_567.89, compact=False, precision=2)
        assert result == "$1,234,567.89"

    def test_negative_full_format_parens(self) -> None:
        result = FinancialFormatter.currency(-1_234.56, compact=False, precision=2)
        assert result == "($1,234.56)"

    def test_negative_full_format_minus_sign(self) -> None:
        result = FinancialFormatter.currency(
            -1_234.56, compact=False, precision=2, negative_parens=False
        )
        assert result == "-$1,234.56"

    def test_zero_value(self) -> None:
        assert FinancialFormatter.currency(0, compact=True) == "$0"

    def test_trillions(self) -> None:
        assert FinancialFormatter.currency(1_500_000_000_000, compact=True) == "$1.5T"

    def test_custom_symbol(self) -> None:
        assert FinancialFormatter.currency(1_000_000, symbol="EUR ", compact=True) == "EUR 1.0M"


class TestPercentageFormatting:
    """Percentage formatting from decimal and raw values."""

    def test_decimal_default_precision(self) -> None:
        assert FinancialFormatter.percentage(0.1523) == "15.2%"

    def test_decimal_precision_2(self) -> None:
        assert FinancialFormatter.percentage(0.1523, precision=2) == "15.23%"

    def test_raw_value_not_decimal(self) -> None:
        assert FinancialFormatter.percentage(15.23, is_decimal=False) == "15.2%"

    def test_zero_percentage(self) -> None:
        assert FinancialFormatter.percentage(0.0) == "0.0%"

    def test_negative_percentage(self) -> None:
        assert FinancialFormatter.percentage(-0.05) == "-5.0%"


class TestMultipleFormatting:
    """Multiple formatting with 'x' suffix."""

    def test_standard_multiple(self) -> None:
        assert FinancialFormatter.multiple(12.456) == "12.5x"

    def test_whole_number_multiple(self) -> None:
        assert FinancialFormatter.multiple(3.0) == "3.0x"

    def test_small_multiple(self) -> None:
        assert FinancialFormatter.multiple(0.5) == "0.5x"


class TestBasisPointsFormatting:
    """Basis points formatting from decimal and raw values."""

    def test_decimal_to_bps(self) -> None:
        assert FinancialFormatter.basis_points(0.0025) == "25bps"

    def test_raw_bps(self) -> None:
        assert FinancialFormatter.basis_points(150, is_decimal=False) == "150bps"

    def test_zero_bps(self) -> None:
        assert FinancialFormatter.basis_points(0.0) == "0bps"


class TestAutoFormat:
    """Auto-format dispatching by format type string/enum."""

    def test_auto_percentage(self) -> None:
        assert FinancialFormatter.auto_format(0.15, "percentage") == "15.0%"

    def test_auto_multiple(self) -> None:
        assert FinancialFormatter.auto_format(12.5, "multiple") == "12.5x"

    def test_auto_currency(self) -> None:
        assert FinancialFormatter.auto_format(1_500_000, "currency") == "$1.5M"

    def test_auto_basis_points(self) -> None:
        assert FinancialFormatter.auto_format(0.005, "basis_points") == "50bps"

    def test_auto_format_enum(self) -> None:
        assert FinancialFormatter.auto_format(0.15, NumberFormat.PERCENTAGE) == "15.0%"

    def test_auto_format_integer(self) -> None:
        assert FinancialFormatter.auto_format(42.7, "integer") == "43"

    def test_auto_format_plain(self) -> None:
        assert FinancialFormatter.auto_format(42.789, "plain") == "42.79"
