"""Tests for ConditionalFormatter — pos/neg colors, median highlight, heatmap gradient, traffic light."""

from __future__ import annotations

import pytest

from deckforge.finance.conditional import ConditionalFormatter
from deckforge.themes.types import ResolvedTheme, ThemeColors, ThemeTypography, ThemeSpacing


@pytest.fixture
def theme() -> ResolvedTheme:
    """Minimal resolved theme for conditional formatting tests."""
    return ResolvedTheme(
        name="test",
        description="Test theme",
        colors=ThemeColors(
            primary="#0C1B33",
            secondary="#1A365D",
            accent="#3182CE",
            background="#FFFFFF",
            surface="#F7FAFC",
            text_primary="#1A202C",
            text_secondary="#4A5568",
            text_muted="#A0AEC0",
            positive="#0D6B3D",
            negative="#C53030",
            warning="#B7791F",
        ),
        typography=ThemeTypography(
            heading_family="Calibri",
            body_family="Calibri",
            mono_family="Consolas",
        ),
        spacing=ThemeSpacing(
            margin_top=0.5,
            margin_bottom=0.5,
            margin_left=0.5,
            margin_right=0.5,
            gutter=0.2,
            element_gap=0.15,
            section_gap=0.4,
        ),
    )


class TestPosNegColor:
    """Positive/negative value coloring."""

    def test_positive_value(self, theme: ResolvedTheme) -> None:
        assert ConditionalFormatter.pos_neg_color(10.5, theme) == theme.colors.positive

    def test_negative_value(self, theme: ResolvedTheme) -> None:
        assert ConditionalFormatter.pos_neg_color(-3.2, theme) == theme.colors.negative

    def test_zero_value(self, theme: ResolvedTheme) -> None:
        assert ConditionalFormatter.pos_neg_color(0, theme) == theme.colors.text_muted

    def test_very_small_positive(self, theme: ResolvedTheme) -> None:
        assert ConditionalFormatter.pos_neg_color(0.001, theme) == theme.colors.positive

    def test_very_small_negative(self, theme: ResolvedTheme) -> None:
        assert ConditionalFormatter.pos_neg_color(-0.001, theme) == theme.colors.negative


class TestMedianHighlight:
    """Median-based highlighting with lightened colors."""

    def test_above_median(self, theme: ResolvedTheme) -> None:
        result = ConditionalFormatter.median_highlight(80.0, 50.0, theme)
        # Should be a lightened positive color (not raw positive)
        assert result != theme.colors.positive
        assert result.startswith("#")
        assert len(result) == 7

    def test_below_median(self, theme: ResolvedTheme) -> None:
        result = ConditionalFormatter.median_highlight(20.0, 50.0, theme)
        # Should be a lightened negative color (not raw negative)
        assert result != theme.colors.negative
        assert result.startswith("#")
        assert len(result) == 7

    def test_equal_to_median(self, theme: ResolvedTheme) -> None:
        result = ConditionalFormatter.median_highlight(50.0, 50.0, theme)
        assert result == theme.colors.surface


class TestHeatmapGradient:
    """Heatmap gradient interpolation between min and max."""

    def test_min_value_returns_negative_color(self, theme: ResolvedTheme) -> None:
        result = ConditionalFormatter.heatmap_gradient(0.0, 0.0, 100.0, theme)
        assert result == theme.colors.negative

    def test_max_value_returns_positive_color(self, theme: ResolvedTheme) -> None:
        result = ConditionalFormatter.heatmap_gradient(100.0, 0.0, 100.0, theme)
        assert result == theme.colors.positive

    def test_midpoint_returns_interpolated_color(self, theme: ResolvedTheme) -> None:
        result = ConditionalFormatter.heatmap_gradient(50.0, 0.0, 100.0, theme)
        # Should be between negative and positive, not equal to either
        assert result != theme.colors.negative
        assert result != theme.colors.positive
        assert result.startswith("#")
        assert len(result) == 7

    def test_equal_min_max_returns_positive(self, theme: ResolvedTheme) -> None:
        """When min == max, avoid division by zero."""
        result = ConditionalFormatter.heatmap_gradient(5.0, 5.0, 5.0, theme)
        assert result.startswith("#")


class TestTrafficLight:
    """Traffic light status colors."""

    def test_green(self) -> None:
        assert ConditionalFormatter.traffic_light("green") == "#27AE60"

    def test_yellow(self) -> None:
        assert ConditionalFormatter.traffic_light("yellow") == "#F39C12"

    def test_red(self) -> None:
        assert ConditionalFormatter.traffic_light("red") == "#E74C3C"

    def test_unknown_status(self) -> None:
        """Unknown status returns a neutral gray."""
        result = ConditionalFormatter.traffic_light("unknown")
        assert result.startswith("#")
