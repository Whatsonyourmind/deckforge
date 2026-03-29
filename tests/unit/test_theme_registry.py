"""Tests for ThemeResolver — variable resolution with cycle detection."""

from __future__ import annotations

import pytest


class TestThemeResolver:
    """ThemeResolver resolves $variable references in theme dicts."""

    def test_resolve_simple_reference(self):
        """$colors.navy_900 resolves to the hex value."""
        from deckforge.themes.resolver import ThemeResolver

        raw = {
            "colors": {"navy_900": "#0A1E3D"},
            "palette": {"primary": "$colors.navy_900"},
        }
        resolver = ThemeResolver(raw)
        result = resolver.resolve_all()
        assert result["palette"]["primary"] == "#0A1E3D"

    def test_resolve_chained_references(self):
        """$palette.primary -> $colors.navy_900 -> #0A1E3D (two hops)."""
        from deckforge.themes.resolver import ThemeResolver

        raw = {
            "colors": {"navy_900": "#0A1E3D"},
            "palette": {"primary": "$colors.navy_900"},
            "slide_masters": {"title": {"bg": "$palette.primary"}},
        }
        resolver = ThemeResolver(raw)
        result = resolver.resolve_all()
        assert result["slide_masters"]["title"]["bg"] == "#0A1E3D"

    def test_circular_reference_raises(self):
        """Circular $a -> $b -> $a raises ValueError."""
        from deckforge.themes.resolver import ThemeResolver

        raw = {
            "a": {"x": "$b.y"},
            "b": {"y": "$a.x"},
        }
        resolver = ThemeResolver(raw)
        with pytest.raises(ValueError, match="[Cc]ircular"):
            resolver.resolve_all()

    def test_resolve_all_no_references_remaining(self):
        """After resolve_all(), no string starts with $."""
        from deckforge.themes.resolver import ThemeResolver

        raw = {
            "colors": {"blue": "#0000FF", "red": "#FF0000"},
            "palette": {"primary": "$colors.blue", "danger": "$colors.red"},
            "text": {"heading_color": "$palette.primary"},
        }
        resolver = ThemeResolver(raw)
        result = resolver.resolve_all()

        def check_no_refs(d):
            for v in d.values():
                if isinstance(v, dict):
                    check_no_refs(v)
                elif isinstance(v, str):
                    assert not v.startswith("$"), f"Unresolved reference: {v}"

        check_no_refs(result)

    def test_resolve_non_string_values_unchanged(self):
        """Non-string values (ints, floats, lists) pass through unchanged."""
        from deckforge.themes.resolver import ThemeResolver

        raw = {
            "typography": {"scale": {"h1": 44, "body": 18}},
            "spacing": {"margin": 1.0},
            "chart_colors": ["#FF0000", "#00FF00"],
        }
        resolver = ThemeResolver(raw)
        result = resolver.resolve_all()
        assert result["typography"]["scale"]["h1"] == 44
        assert result["spacing"]["margin"] == 1.0
        assert result["chart_colors"] == ["#FF0000", "#00FF00"]

    def test_resolve_list_with_references(self):
        """References inside lists are resolved."""
        from deckforge.themes.resolver import ThemeResolver

        raw = {
            "colors": {"blue": "#0000FF", "red": "#FF0000"},
            "chart_colors": ["$colors.blue", "$colors.red"],
        }
        resolver = ThemeResolver(raw)
        result = resolver.resolve_all()
        assert result["chart_colors"] == ["#0000FF", "#FF0000"]

    def test_self_reference_raises(self):
        """$a.x references itself -> circular."""
        from deckforge.themes.resolver import ThemeResolver

        raw = {"a": {"x": "$a.x"}}
        resolver = ThemeResolver(raw)
        with pytest.raises(ValueError, match="[Cc]ircular"):
            resolver.resolve_all()


class TestResolvedThemeModel:
    """ResolvedTheme Pydantic model validates complete theme structure."""

    def test_valid_resolved_theme(self):
        """ResolvedTheme accepts a complete theme structure."""
        from deckforge.themes.types import (
            ComponentStyle,
            ResolvedTheme,
            SlideMaster,
            ThemeColors,
            ThemeSpacing,
            ThemeTypography,
        )

        theme = ResolvedTheme(
            name="Test Theme",
            description="A test theme",
            version="1.0",
            colors=ThemeColors(
                primary="#000000",
                secondary="#111111",
                accent="#FF0000",
                background="#FFFFFF",
                surface="#F5F5F5",
                text_primary="#000000",
                text_secondary="#333333",
                text_muted="#666666",
                positive="#00AA00",
                negative="#AA0000",
                warning="#AAAA00",
            ),
            typography=ThemeTypography(
                heading_family="Arial",
                body_family="Calibri",
                mono_family="Consolas",
                scale={"h1": 44, "h2": 36, "h3": 28, "subtitle": 24, "body": 18, "caption": 14, "footnote": 10},
                weights={"heading": 700, "subtitle": 600, "body": 400, "caption": 400},
                line_height=1.4,
            ),
            spacing=ThemeSpacing(
                margin_top=0.5,
                margin_bottom=0.5,
                margin_left=0.75,
                margin_right=0.75,
                gutter=0.3,
                element_gap=0.2,
                section_gap=0.5,
            ),
            slide_masters={
                "title_slide": SlideMaster(
                    background="#000000",
                    regions={
                        "title": ComponentStyle(font_family="Arial", font_size=44, color="#FFFFFF"),
                    },
                ),
            },
            chart_colors=["#0000FF", "#FF0000", "#00FF00"],
        )
        assert theme.name == "Test Theme"
        assert theme.colors.primary == "#000000"

    def test_component_style_fields(self):
        """ComponentStyle holds font/color/alignment config."""
        from deckforge.themes.types import ComponentStyle

        style = ComponentStyle(
            font_family="Arial",
            font_size=24,
            font_weight=700,
            color="#FFFFFF",
            alignment="center",
            background="#000000",
            bullet_color="#FF0000",
            indent=0.5,
            columns=2,
            min_height=3.0,
        )
        assert style.font_family == "Arial"
        assert style.font_size == 24
        assert style.font_weight == 700
        assert style.color == "#FFFFFF"
        assert style.alignment == "center"
        assert style.columns == 2
