"""Tests for ContrastChecker — WCAG AA contrast ratio validation."""

from __future__ import annotations

import pytest


class TestHexToRgb:
    """hex_to_rgb converts hex color strings to RGB tuples."""

    def test_six_char_hex(self):
        from deckforge.themes.contrast import hex_to_rgb

        assert hex_to_rgb("#0A1E3D") == (10, 30, 61)

    def test_six_char_no_hash(self):
        from deckforge.themes.contrast import hex_to_rgb

        assert hex_to_rgb("0A1E3D") == (10, 30, 61)

    def test_three_char_hex(self):
        from deckforge.themes.contrast import hex_to_rgb

        # #FFF -> #FFFFFF
        assert hex_to_rgb("#FFF") == (255, 255, 255)

    def test_black(self):
        from deckforge.themes.contrast import hex_to_rgb

        assert hex_to_rgb("#000000") == (0, 0, 0)


class TestRelativeLuminance:
    """relative_luminance follows W3C G18 sRGB algorithm."""

    def test_white_luminance(self):
        from deckforge.themes.contrast import relative_luminance

        lum = relative_luminance(255, 255, 255)
        assert abs(lum - 1.0) < 0.001

    def test_black_luminance(self):
        from deckforge.themes.contrast import relative_luminance

        lum = relative_luminance(0, 0, 0)
        assert lum == 0.0

    def test_mid_gray_luminance(self):
        from deckforge.themes.contrast import relative_luminance

        # sRGB(128, 128, 128) -> approximately 0.216
        lum = relative_luminance(128, 128, 128)
        assert 0.2 < lum < 0.25


class TestContrastRatio:
    """contrast_ratio computes WCAG-defined ratio."""

    def test_black_white_ratio(self):
        from deckforge.themes.contrast import contrast_ratio

        ratio = contrast_ratio((255, 255, 255), (0, 0, 0))
        assert ratio == 21.0

    def test_same_color_ratio(self):
        from deckforge.themes.contrast import contrast_ratio

        ratio = contrast_ratio((128, 128, 128), (128, 128, 128))
        assert ratio == 1.0

    def test_order_independent(self):
        """contrast_ratio returns same value regardless of order."""
        from deckforge.themes.contrast import contrast_ratio

        ratio1 = contrast_ratio((255, 255, 255), (0, 0, 0))
        ratio2 = contrast_ratio((0, 0, 0), (255, 255, 255))
        assert ratio1 == ratio2


class TestPassesWcagAa:
    """passes_wcag_aa checks 4.5:1 for body, 3:1 for large text."""

    def test_white_on_dark_passes(self):
        from deckforge.themes.contrast import passes_wcag_aa

        # White text on dark navy — high contrast
        assert passes_wcag_aa("#FFFFFF", "#0A1E3D", is_large_text=False) is True

    def test_low_contrast_fails(self):
        from deckforge.themes.contrast import passes_wcag_aa

        # Light gray on white — low contrast
        assert passes_wcag_aa("#CCCCCC", "#FFFFFF", is_large_text=False) is False

    def test_large_text_lower_threshold(self):
        from deckforge.themes.contrast import passes_wcag_aa

        # A pair that passes 3:1 but fails 4.5:1
        # Gray (#767676) on white has ratio ~4.54 (passes both for normal)
        # Use lighter gray that's between 3:1 and 4.5:1
        # #959595 on #FFFFFF is about 3.0:1
        # #949494 on #FFFFFF
        # Let's use a known pair: #757575 on #FFFFFF -> 4.6:1 (passes both)
        # #888888 on #FFFFFF -> about 3.5:1 (passes large, fails normal)
        assert passes_wcag_aa("#888888", "#FFFFFF", is_large_text=True) is True
        assert passes_wcag_aa("#888888", "#FFFFFF", is_large_text=False) is False


class TestContrastIssue:
    """ContrastIssue dataclass holds validation failure details."""

    def test_contrast_issue_fields(self):
        from deckforge.themes.contrast import ContrastIssue

        issue = ContrastIssue(
            fg_color="#CCCCCC",
            bg_color="#FFFFFF",
            ratio=1.6,
            required_ratio=4.5,
            context="text_primary on background",
        )
        assert issue.fg_color == "#CCCCCC"
        assert issue.ratio == 1.6
        assert issue.required_ratio == 4.5


class TestValidateThemeContrast:
    """validate_theme_contrast checks all text colors against backgrounds."""

    def test_good_theme_no_issues(self):
        from deckforge.themes.contrast import validate_theme_contrast
        from deckforge.themes.types import (
            ResolvedTheme,
            SlideMaster,
            ThemeColors,
            ThemeSpacing,
            ThemeTypography,
        )

        theme = ResolvedTheme(
            name="Good Theme",
            description="High contrast",
            version="1.0",
            colors=ThemeColors(
                primary="#000000",
                secondary="#111111",
                accent="#FF0000",
                background="#FFFFFF",
                surface="#F5F5F5",
                text_primary="#000000",
                text_secondary="#333333",
                text_muted="#555555",
                positive="#006600",
                negative="#AA0000",
                warning="#665500",
            ),
            typography=ThemeTypography(
                heading_family="Arial",
                body_family="Calibri",
                mono_family="Consolas",
                scale={"h1": 44, "h2": 36, "h3": 28, "subtitle": 24, "body": 18, "caption": 14, "footnote": 10},
                weights={"heading": 700, "subtitle": 600, "body": 400, "caption": 400},
            ),
            spacing=ThemeSpacing(
                margin_top=0.5, margin_bottom=0.5, margin_left=0.75, margin_right=0.75,
                gutter=0.3, element_gap=0.2, section_gap=0.5,
            ),
            slide_masters={},
            chart_colors=["#0000FF"],
        )
        issues = validate_theme_contrast(theme)
        assert len(issues) == 0

    def test_bad_contrast_detected(self):
        from deckforge.themes.contrast import validate_theme_contrast
        from deckforge.themes.types import (
            ResolvedTheme,
            SlideMaster,
            ThemeColors,
            ThemeSpacing,
            ThemeTypography,
        )

        theme = ResolvedTheme(
            name="Bad Theme",
            description="Low contrast",
            version="1.0",
            colors=ThemeColors(
                primary="#EEEEEE",
                secondary="#DDDDDD",
                accent="#CCCCCC",
                background="#FFFFFF",
                surface="#FAFAFA",
                text_primary="#EEEEEE",  # Very low contrast on white
                text_secondary="#DDDDDD",  # Very low contrast on white
                text_muted="#CCCCCC",
                positive="#00FF00",
                negative="#FF0000",
                warning="#FFFF00",
            ),
            typography=ThemeTypography(
                heading_family="Arial",
                body_family="Calibri",
                mono_family="Consolas",
                scale={"h1": 44, "h2": 36, "h3": 28, "subtitle": 24, "body": 18, "caption": 14, "footnote": 10},
                weights={"heading": 700, "subtitle": 600, "body": 400, "caption": 400},
            ),
            spacing=ThemeSpacing(
                margin_top=0.5, margin_bottom=0.5, margin_left=0.75, margin_right=0.75,
                gutter=0.3, element_gap=0.2, section_gap=0.5,
            ),
            slide_masters={},
            chart_colors=["#0000FF"],
        )
        issues = validate_theme_contrast(theme)
        assert len(issues) > 0
        assert any("text_primary" in i.context for i in issues)
