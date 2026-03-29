"""WCAG AA contrast validation — W3C G18 algorithm for color accessibility."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ContrastIssue:
    """A contrast validation failure."""

    fg_color: str
    bg_color: str
    ratio: float
    required_ratio: float
    context: str


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color string to RGB tuple.

    Handles both '#RRGGBB' and '#RGB' formats, with or without leading '#'.
    """
    color = hex_color.lstrip("#")
    if len(color) == 3:
        color = "".join(c * 2 for c in color)
    return (int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16))


def relative_luminance(r: int, g: int, b: int) -> float:
    """Compute relative luminance per W3C G18 sRGB linearization.

    Uses the piecewise sRGB transfer function with threshold 0.04045.
    Returns value between 0.0 (black) and 1.0 (white).
    """

    def linearize(channel: int) -> float:
        s = channel / 255.0
        if s <= 0.04045:
            return s / 12.92
        return ((s + 0.055) / 1.055) ** 2.4

    r_lin = linearize(r)
    g_lin = linearize(g)
    b_lin = linearize(b)
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def contrast_ratio(
    color1_rgb: tuple[int, int, int], color2_rgb: tuple[int, int, int]
) -> float:
    """Compute WCAG contrast ratio between two RGB colors.

    Returns ratio between 1.0 (identical) and 21.0 (black/white).
    Always puts the lighter color as L1 for consistent results.
    """
    l1 = relative_luminance(*color1_rgb)
    l2 = relative_luminance(*color2_rgb)
    # Ensure L1 is the lighter
    if l1 < l2:
        l1, l2 = l2, l1
    return round((l1 + 0.05) / (l2 + 0.05), 1)


def passes_wcag_aa(
    fg_hex: str, bg_hex: str, *, is_large_text: bool = False
) -> bool:
    """Check if foreground/background color pair passes WCAG AA.

    Thresholds:
      - Normal text: 4.5:1
      - Large text (>=18pt or >=14pt bold): 3.0:1
    """
    fg_rgb = hex_to_rgb(fg_hex)
    bg_rgb = hex_to_rgb(bg_hex)
    ratio = contrast_ratio(fg_rgb, bg_rgb)
    threshold = 3.0 if is_large_text else 4.5
    return ratio >= threshold


def validate_theme_contrast(theme: "ResolvedTheme") -> list[ContrastIssue]:  # noqa: F821
    """Validate all text colors against backgrounds in a ResolvedTheme.

    Checks:
      - text_primary on background (4.5:1)
      - text_primary on surface (4.5:1)
      - text_secondary on background (4.5:1)
      - text_secondary on surface (4.5:1)

    Returns list of ContrastIssue for any failures (empty = all pass).
    """
    issues: list[ContrastIssue] = []
    checks = [
        (theme.colors.text_primary, theme.colors.background, "text_primary on background"),
        (theme.colors.text_primary, theme.colors.surface, "text_primary on surface"),
        (theme.colors.text_secondary, theme.colors.background, "text_secondary on background"),
        (theme.colors.text_secondary, theme.colors.surface, "text_secondary on surface"),
    ]
    for fg, bg, context in checks:
        fg_rgb = hex_to_rgb(fg)
        bg_rgb = hex_to_rgb(bg)
        ratio = contrast_ratio(fg_rgb, bg_rgb)
        if ratio < 4.5:
            issues.append(
                ContrastIssue(
                    fg_color=fg,
                    bg_color=bg,
                    ratio=ratio,
                    required_ratio=4.5,
                    context=context,
                )
            )
    return issues


# Alias for convenience
ContrastChecker = validate_theme_contrast
