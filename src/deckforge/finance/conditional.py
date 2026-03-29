"""Conditional formatting — theme-aware colors for financial data visualization.

Provides positive/negative coloring, median highlight, heatmap gradient, and
traffic light indicators. All color methods return hex strings (#RRGGBB).
"""

from __future__ import annotations

from deckforge.themes.types import ResolvedTheme


# Fixed traffic light colors (not theme-dependent).
_TRAFFIC_COLORS: dict[str, str] = {
    "green": "#27AE60",
    "yellow": "#F39C12",
    "red": "#E74C3C",
}

_DEFAULT_NEUTRAL = "#95A5A6"


class ConditionalFormatter:
    """Static methods for conditional formatting of financial data."""

    @staticmethod
    def pos_neg_color(value: float, theme: ResolvedTheme) -> str:
        """Return theme color based on value sign.

        Positive -> theme.colors.positive (green)
        Negative -> theme.colors.negative (red)
        Zero     -> theme.colors.text_muted (neutral)
        """
        if value > 0:
            return theme.colors.positive
        if value < 0:
            return theme.colors.negative
        return theme.colors.text_muted

    @staticmethod
    def pos_neg_text_color(value: float, theme: ResolvedTheme) -> str:
        """Return a darker text-appropriate color based on value sign.

        Same logic as pos_neg_color but returns colors suitable for text rendering
        (identical mapping; darker variants can be added if needed).
        """
        if value > 0:
            return theme.colors.positive
        if value < 0:
            return theme.colors.negative
        return theme.colors.text_muted

    @staticmethod
    def median_highlight(value: float, median: float, theme: ResolvedTheme) -> str:
        """Return a lightened background color based on relation to median.

        Above median -> lightened positive color
        Below median -> lightened negative color
        Equal        -> theme surface color (neutral)
        """
        if value > median:
            return _lighten(theme.colors.positive, factor=0.85)
        if value < median:
            return _lighten(theme.colors.negative, factor=0.85)
        return theme.colors.surface

    @staticmethod
    def heatmap_gradient(
        value: float, min_val: float, max_val: float, theme: ResolvedTheme
    ) -> str:
        """Return an interpolated color between negative (low) and positive (high).

        Linear interpolation in RGB space. Handles min_val == max_val gracefully.
        """
        if max_val == min_val:
            # All values identical; return midpoint blend.
            return _interpolate_color(theme.colors.negative, theme.colors.positive, 0.5)

        ratio = (value - min_val) / (max_val - min_val)
        ratio = max(0.0, min(1.0, ratio))  # Clamp to [0, 1].
        return _interpolate_color(theme.colors.negative, theme.colors.positive, ratio)

    @staticmethod
    def traffic_light(status: str) -> str:
        """Return a fixed traffic light color for a status string.

        "green"  -> #27AE60
        "yellow" -> #F39C12
        "red"    -> #E74C3C
        Unknown  -> neutral gray (#95A5A6)
        """
        return _TRAFFIC_COLORS.get(status.lower(), _DEFAULT_NEUTRAL)


# ---------------------------------------------------------------------------
# Internal color math helpers
# ---------------------------------------------------------------------------


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert '#RRGGBB' to (R, G, B) tuple."""
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert (R, G, B) tuple to '#RRGGBB' string."""
    return f"#{r:02X}{g:02X}{b:02X}"


def _lighten(hex_color: str, factor: float = 0.85) -> str:
    """Blend a color toward white by *factor* (0.85 = 85% white + 15% color)."""
    r, g, b = _hex_to_rgb(hex_color)
    lr = round(r + (255 - r) * factor)
    lg = round(g + (255 - g) * factor)
    lb = round(b + (255 - b) * factor)
    return _rgb_to_hex(lr, lg, lb)


def _interpolate_color(color1: str, color2: str, ratio: float) -> str:
    """Linearly interpolate between two hex colors. ratio=0 -> color1, ratio=1 -> color2."""
    r1, g1, b1 = _hex_to_rgb(color1)
    r2, g2, b2 = _hex_to_rgb(color2)
    r = round(r1 + (r2 - r1) * ratio)
    g = round(g1 + (g2 - g1) * ratio)
    b = round(b1 + (b2 - b1) * ratio)
    return _rgb_to_hex(r, g, b)
