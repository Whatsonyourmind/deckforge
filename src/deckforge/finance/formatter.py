"""Financial number formatter — currency, percentage, multiple, basis points, and auto-format.

Provides consistent formatting for financial values across all slide renderers.
Compact mode uses magnitude suffixes (K, M, B, T) for readability.
"""

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


# Magnitude thresholds and suffixes for compact currency formatting.
_MAGNITUDES: list[tuple[float, str]] = [
    (1e12, "T"),
    (1e9, "B"),
    (1e6, "M"),
    (1e3, "K"),
]


class FinancialFormatter:
    """Static methods for formatting financial numbers."""

    @staticmethod
    def currency(
        value: float,
        symbol: str = "$",
        precision: int | None = None,
        compact: bool = True,
        negative_parens: bool = True,
    ) -> str:
        """Format a value as currency.

        Args:
            value: The numeric value.
            symbol: Currency symbol prefix (default "$").
            precision: Decimal places (default 1 for compact, 2 for full).
            compact: If True, use magnitude suffixes (K, M, B, T).
            negative_parens: If True, wrap negatives in parentheses; else use minus sign.
        """
        if precision is None:
            precision = 1 if compact else 2

        is_negative = value < 0
        abs_val = abs(value)

        if compact:
            formatted = _compact_number(abs_val, precision)
            inner = f"{symbol}{formatted}"
        else:
            inner = f"{symbol}{abs_val:,.{precision}f}"

        if is_negative:
            if negative_parens:
                return f"({inner})"
            return f"-{inner}"
        return inner

    @staticmethod
    def percentage(value: float, precision: int = 1, is_decimal: bool = True) -> str:
        """Format a value as a percentage.

        Args:
            value: The numeric value (0.15 for 15% if is_decimal=True).
            precision: Decimal places (default 1).
            is_decimal: If True, multiply by 100 first.
        """
        pct = value * 100 if is_decimal else value
        return f"{pct:.{precision}f}%"

    @staticmethod
    def multiple(value: float, precision: int = 1) -> str:
        """Format a value as a multiple (e.g., 12.5x).

        Args:
            value: The numeric value.
            precision: Decimal places (default 1).
        """
        return f"{value:.{precision}f}x"

    @staticmethod
    def basis_points(value: float, is_decimal: bool = True) -> str:
        """Format a value as basis points.

        Args:
            value: The numeric value (0.0025 for 25bps if is_decimal=True).
            is_decimal: If True, multiply by 10000 first.
        """
        bps = value * 10000 if is_decimal else value
        return f"{round(bps)}bps"

    @staticmethod
    def ratio(value: float, precision: int = 2) -> str:
        """Format a value as a plain ratio.

        Args:
            value: The numeric value.
            precision: Decimal places (default 2).
        """
        return f"{value:.{precision}f}"

    @staticmethod
    def auto_format(value: float, format_type: str | NumberFormat) -> str:
        """Dispatch to the correct formatter based on format type.

        Args:
            value: The numeric value.
            format_type: A string name or NumberFormat enum member.
        """
        if isinstance(format_type, NumberFormat):
            key = format_type.value
        else:
            key = format_type.lower()

        dispatch = {
            "currency": lambda v: FinancialFormatter.currency(v, compact=True),
            "currency_full": lambda v: FinancialFormatter.currency(v, compact=False, precision=2),
            "percentage": lambda v: FinancialFormatter.percentage(v),
            "multiple": lambda v: FinancialFormatter.multiple(v),
            "basis_points": lambda v: FinancialFormatter.basis_points(v),
            "ratio": lambda v: FinancialFormatter.ratio(v),
            "integer": lambda v: str(round(v)),
            "plain": lambda v: f"{v:.2f}",
        }

        formatter = dispatch.get(key)
        if formatter is None:
            return str(value)
        return formatter(value)


def _compact_number(abs_val: float, precision: int) -> str:
    """Format a non-negative number with magnitude suffix.

    Returns formatted string without currency symbol.
    """
    for threshold, suffix in _MAGNITUDES:
        if abs_val >= threshold:
            scaled = abs_val / threshold
            return f"{scaled:.{precision}f}{suffix}"
    # Below 1000: no suffix, no decimals for clean small numbers.
    if abs_val == int(abs_val):
        return str(int(abs_val))
    return f"{abs_val:.{precision}f}"
