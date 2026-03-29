"""Tests for BrandKitMerger, ThemeRegistry, and YAML theme loading."""

from __future__ import annotations

import pytest

from deckforge.ir.brand_kit import BrandColors, BrandFonts, BrandKit, LogoConfig, FooterConfig
from deckforge.themes.brand_kit_merger import BrandKitMerger
from deckforge.themes.contrast import validate_theme_contrast
from deckforge.themes.registry import ThemeRegistry
from deckforge.themes.types import (
    ComponentStyle,
    ResolvedTheme,
    SlideMaster,
    ThemeColors,
    ThemeSpacing,
    ThemeTypography,
)


def _make_theme(**overrides) -> ResolvedTheme:
    """Build a minimal ResolvedTheme for testing."""
    defaults = {
        "name": "Test Theme",
        "description": "A test theme",
        "version": "1.0",
        "colors": ThemeColors(
            primary="#000000",
            secondary="#111111",
            accent="#FF0000",
            background="#FFFFFF",
            surface="#F5F5F5",
            text_primary="#1A1A1A",
            text_secondary="#333333",
            text_muted="#555555",
            positive="#00AA00",
            negative="#AA0000",
            warning="#AAAA00",
        ),
        "typography": ThemeTypography(
            heading_family="Arial",
            body_family="Calibri",
            mono_family="Consolas",
            scale={"h1": 44, "h2": 36, "h3": 28, "subtitle": 24, "body": 18, "caption": 14, "footnote": 10},
            weights={"heading": 700, "subtitle": 600, "body": 400, "caption": 400},
            line_height=1.4,
        ),
        "spacing": ThemeSpacing(
            margin_top=0.5, margin_bottom=0.5, margin_left=0.75, margin_right=0.75,
            gutter=0.3, element_gap=0.2, section_gap=0.5,
        ),
        "slide_masters": {
            "title_slide": SlideMaster(
                background="#000000",
                regions={"title": ComponentStyle(font_family="Arial", font_size=44, color="#FFFFFF")},
            ),
        },
        "chart_colors": ["#0000FF", "#FF0000"],
    }
    defaults.update(overrides)
    return ResolvedTheme(**defaults)


# -- BrandKitMerger tests --

class TestBrandKitMergerColors:
    """BrandKitMerger correctly overrides colors."""

    def test_override_primary_color(self):
        theme = _make_theme()
        kit = BrandKit(colors=BrandColors(primary="#AA0000"))
        merged = BrandKitMerger.merge(theme, kit)
        assert merged.colors.primary == "#AA0000"

    def test_override_secondary_color(self):
        theme = _make_theme()
        kit = BrandKit(colors=BrandColors(primary="#000000", secondary="#BB0000"))
        merged = BrandKitMerger.merge(theme, kit)
        assert merged.colors.secondary == "#BB0000"

    def test_override_background(self):
        theme = _make_theme()
        kit = BrandKit(colors=BrandColors(primary="#000000", background="#EEEEEE"))
        merged = BrandKitMerger.merge(theme, kit)
        assert merged.colors.background == "#EEEEEE"

    def test_override_text(self):
        theme = _make_theme()
        kit = BrandKit(colors=BrandColors(primary="#000000", text="#222222"))
        merged = BrandKitMerger.merge(theme, kit)
        assert merged.colors.text_primary == "#222222"

    def test_override_muted(self):
        theme = _make_theme()
        kit = BrandKit(colors=BrandColors(primary="#000000", muted="#999999"))
        merged = BrandKitMerger.merge(theme, kit)
        assert merged.colors.text_muted == "#999999"

    def test_accent_from_accent_list(self):
        theme = _make_theme()
        kit = BrandKit(colors=BrandColors(primary="#000000", accent=["#CC00CC"]))
        merged = BrandKitMerger.merge(theme, kit)
        assert merged.colors.accent == "#CC00CC"


class TestBrandKitMergerFonts:
    """BrandKitMerger correctly overrides fonts."""

    def test_override_heading_font(self):
        theme = _make_theme()
        kit = BrandKit(fonts=BrandFonts(heading="Montserrat"))
        merged = BrandKitMerger.merge(theme, kit)
        assert merged.typography.heading_family == "Montserrat"

    def test_override_body_font(self):
        theme = _make_theme()
        kit = BrandKit(fonts=BrandFonts(body="Inter"))
        merged = BrandKitMerger.merge(theme, kit)
        assert merged.typography.body_family == "Inter"

    def test_override_mono_font(self):
        theme = _make_theme()
        kit = BrandKit(fonts=BrandFonts(mono="Fira Code"))
        merged = BrandKitMerger.merge(theme, kit)
        assert merged.typography.mono_family == "Fira Code"


class TestBrandKitMergerProtection:
    """BrandKitMerger preserves protected keys."""

    def test_spacing_preserved(self):
        theme = _make_theme()
        kit = BrandKit(
            colors=BrandColors(primary="#AA0000"),
            fonts=BrandFonts(heading="Montserrat"),
        )
        merged = BrandKitMerger.merge(theme, kit)
        # Spacing must remain untouched
        assert merged.spacing.margin_top == theme.spacing.margin_top
        assert merged.spacing.gutter == theme.spacing.gutter

    def test_typography_scale_preserved(self):
        theme = _make_theme()
        kit = BrandKit(fonts=BrandFonts(heading="Montserrat"))
        merged = BrandKitMerger.merge(theme, kit)
        # Scale must remain untouched
        assert merged.typography.scale == theme.typography.scale

    def test_typography_line_height_preserved(self):
        theme = _make_theme()
        kit = BrandKit(fonts=BrandFonts(heading="Montserrat"))
        merged = BrandKitMerger.merge(theme, kit)
        assert merged.typography.line_height == theme.typography.line_height


class TestBrandKitMergerImmutability:
    """BrandKitMerger returns new ResolvedTheme (original unchanged)."""

    def test_original_unchanged(self):
        theme = _make_theme()
        original_primary = theme.colors.primary
        original_heading = theme.typography.heading_family
        kit = BrandKit(
            colors=BrandColors(primary="#AA0000"),
            fonts=BrandFonts(heading="Montserrat"),
        )
        merged = BrandKitMerger.merge(theme, kit)
        # Original must be unchanged
        assert theme.colors.primary == original_primary
        assert theme.typography.heading_family == original_heading
        # Merged must be different
        assert merged.colors.primary == "#AA0000"
        assert merged is not theme


class TestBrandKitMergerLogoFooter:
    """BrandKitMerger applies logo and footer from brand kit."""

    def test_override_logo(self):
        theme = _make_theme()
        kit = BrandKit(logo=LogoConfig(url="https://example.com/logo.png", placement="top_right"))
        merged = BrandKitMerger.merge(theme, kit)
        assert merged.logo.placement == "top_right"

    def test_override_footer(self):
        theme = _make_theme()
        kit = BrandKit(footer=FooterConfig(text="Confidential", include_date=True))
        merged = BrandKitMerger.merge(theme, kit)
        assert merged.footer.text == "Confidential"
        assert merged.footer.include_date is True


# -- ThemeRegistry tests --

class TestThemeRegistryLoading:
    """ThemeRegistry loads all 15 themes without error."""

    EXPECTED_THEMES = [
        "arctic-clean",
        "bold-impact",
        "classic-serif",
        "corporate-blue",
        "executive-dark",
        "finance-pro",
        "forest-green",
        "minimal-light",
        "modern-gradient",
        "monochrome",
        "ocean-depth",
        "soft-pastel",
        "sunset-warm",
        "tech-neon",
        "warm-earth",
    ]

    def test_load_all_15_themes(self):
        registry = ThemeRegistry()
        for theme_id in self.EXPECTED_THEMES:
            theme = registry.load_theme(theme_id)
            assert theme.name, f"Theme {theme_id} has no name"
            assert theme.colors.primary, f"Theme {theme_id} has no primary color"
            assert theme.typography.heading_family, f"Theme {theme_id} has no heading_family"
            assert len(theme.slide_masters) >= 10, (
                f"Theme {theme_id} has only {len(theme.slide_masters)} slide masters (need 10+)"
            )

    def test_list_themes_returns_15(self):
        registry = ThemeRegistry()
        themes = registry.list_themes()
        assert len(themes) == 15, f"Expected 15 themes, got {len(themes)}"
        ids = {t["id"] for t in themes}
        for expected in self.EXPECTED_THEMES:
            assert expected in ids, f"Missing theme: {expected}"

    def test_themes_have_chart_colors(self):
        registry = ThemeRegistry()
        for theme_id in self.EXPECTED_THEMES:
            theme = registry.load_theme(theme_id)
            assert len(theme.chart_colors) >= 5, (
                f"Theme {theme_id} has only {len(theme.chart_colors)} chart colors (need 5+)"
            )


class TestThemeRegistryCaching:
    """ThemeRegistry caches loaded themes."""

    def test_cache_returns_same_object(self):
        registry = ThemeRegistry()
        theme1 = registry.load_theme("executive-dark")
        theme2 = registry.load_theme("executive-dark")
        assert theme1 is theme2


class TestThemeRegistryBrandKit:
    """ThemeRegistry.get_theme with brand_kit returns merged result."""

    def test_get_theme_with_brand_kit(self):
        registry = ThemeRegistry()
        kit = BrandKit(
            colors=BrandColors(primary="#FF0000"),
            fonts=BrandFonts(heading="Comic Sans MS"),
        )
        theme = registry.get_theme("corporate-blue", brand_kit=kit)
        assert theme.colors.primary == "#FF0000"
        assert theme.typography.heading_family == "Comic Sans MS"

    def test_get_theme_without_brand_kit(self):
        registry = ThemeRegistry()
        theme = registry.get_theme("corporate-blue")
        assert theme.colors.primary != "#FF0000"


class TestThemeContrastValidation:
    """All 15 themes pass WCAG AA contrast for primary text on background."""

    EXPECTED_THEMES = [
        "arctic-clean",
        "bold-impact",
        "classic-serif",
        "corporate-blue",
        "executive-dark",
        "finance-pro",
        "forest-green",
        "minimal-light",
        "modern-gradient",
        "monochrome",
        "ocean-depth",
        "soft-pastel",
        "sunset-warm",
        "tech-neon",
        "warm-earth",
    ]

    def test_all_themes_pass_contrast(self):
        registry = ThemeRegistry()
        issues = registry.validate_all()
        for theme_id, theme_issues in issues.items():
            assert len(theme_issues) == 0, (
                f"Theme {theme_id} has contrast issues: "
                + "; ".join(f"{i.context} ({i.ratio}:1 < {i.required_ratio}:1)" for i in theme_issues)
            )

    def test_themes_are_visually_distinct(self):
        """Switching themes produces different colors for the same structure."""
        registry = ThemeRegistry()
        primaries = set()
        heading_fonts = set()
        for theme_id in self.EXPECTED_THEMES:
            theme = registry.load_theme(theme_id)
            primaries.add(theme.colors.primary)
            heading_fonts.add(theme.typography.heading_family)
        # At least 10 distinct primary colors and 8 distinct heading fonts
        assert len(primaries) >= 10, f"Only {len(primaries)} distinct primary colors"
        assert len(heading_fonts) >= 8, f"Only {len(heading_fonts)} distinct heading fonts"

    def test_each_theme_has_required_slide_masters(self):
        """Each theme defines the minimum required slide masters."""
        required_masters = {
            "title_slide", "bullet_points", "two_column_text", "chart_slide",
            "table_slide", "section_divider", "quote_slide", "image_with_caption",
            "stats_callout", "thank_you",
        }
        registry = ThemeRegistry()
        for theme_id in self.EXPECTED_THEMES:
            theme = registry.load_theme(theme_id)
            missing = required_masters - set(theme.slide_masters.keys())
            assert not missing, f"Theme {theme_id} missing slide masters: {missing}"
