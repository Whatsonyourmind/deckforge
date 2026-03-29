"""Tests for TextMeasurer: Pillow-based text measurement with font caching."""

from __future__ import annotations

import platform

import pytest


def _has_truetype_fonts() -> bool:
    """Check if any TrueType fonts are available on the system."""
    from pathlib import Path

    if platform.system() == "Windows":
        font_dir = Path("C:/Windows/Fonts")
    elif platform.system() == "Darwin":
        font_dir = Path("/System/Library/Fonts")
    else:
        font_dir = Path("/usr/share/fonts")

    if not font_dir.exists():
        return False
    return any(font_dir.rglob("*.ttf"))


has_fonts = _has_truetype_fonts()
skip_no_fonts = pytest.mark.skipif(not has_fonts, reason="No TrueType fonts available")


class TestTextMeasurerBasic:
    """TextMeasurer basic measurement capabilities."""

    @skip_no_fonts
    def test_measure_single_line_returns_nonzero(self):
        from deckforge.layout.text_measurer import TextMeasurer

        tm = TextMeasurer()
        bb = tm.measure_text("Hello World", font_name="Arial", size_pt=14)
        assert bb.width_inches > 0
        assert bb.height_inches > 0

    @skip_no_fonts
    def test_measure_longer_text_wider(self):
        from deckforge.layout.text_measurer import TextMeasurer

        tm = TextMeasurer()
        short = tm.measure_text("Hi", font_name="Arial", size_pt=14)
        long = tm.measure_text("Hello World, this is a longer string", font_name="Arial", size_pt=14)
        assert long.width_inches > short.width_inches

    @skip_no_fonts
    def test_measure_larger_font_taller(self):
        from deckforge.layout.text_measurer import TextMeasurer

        tm = TextMeasurer()
        small = tm.measure_text("Test", font_name="Arial", size_pt=10)
        large = tm.measure_text("Test", font_name="Arial", size_pt=24)
        assert large.height_inches > small.height_inches


class TestTextMeasurerWordWrap:
    """Word wrapping with max_width_inches."""

    @skip_no_fonts
    def test_word_wrap_produces_taller_box(self):
        from deckforge.layout.text_measurer import TextMeasurer

        tm = TextMeasurer()
        text = "This is a relatively long sentence that should wrap to multiple lines"
        no_wrap = tm.measure_text(text, font_name="Arial", size_pt=14)
        wrapped = tm.measure_text(text, font_name="Arial", size_pt=14, max_width_inches=3.0)
        assert wrapped.height_inches > no_wrap.height_inches

    @skip_no_fonts
    def test_word_wrap_respects_max_width(self):
        from deckforge.layout.text_measurer import TextMeasurer

        tm = TextMeasurer()
        text = "This text should be constrained to the given width"
        bb = tm.measure_text(text, font_name="Arial", size_pt=14, max_width_inches=3.0)
        # Width should not exceed max_width + safety margin
        assert bb.width_inches <= 3.0 * 1.10  # allow safety margin + small tolerance


class TestTextMeasurerMultiLine:
    """Multi-line text (explicit newlines)."""

    @skip_no_fonts
    def test_multiline_text_taller_than_single_line(self):
        from deckforge.layout.text_measurer import TextMeasurer

        tm = TextMeasurer()
        single = tm.measure_text("Line one", font_name="Arial", size_pt=14)
        multi = tm.measure_text("Line one\nLine two\nLine three", font_name="Arial", size_pt=14)
        assert multi.height_inches > single.height_inches


class TestTextMeasurerFontCache:
    """Font cache avoids redundant loading."""

    @skip_no_fonts
    def test_font_cache_reuses_objects(self):
        from deckforge.layout.text_measurer import TextMeasurer

        tm = TextMeasurer()
        _ = tm.measure_text("Test", font_name="Arial", size_pt=14)
        cache_size_after_first = len(tm._font_cache)
        _ = tm.measure_text("Different text", font_name="Arial", size_pt=14)
        cache_size_after_second = len(tm._font_cache)
        # Same font/size should not grow cache
        assert cache_size_after_second == cache_size_after_first

    @skip_no_fonts
    def test_font_cache_different_sizes(self):
        from deckforge.layout.text_measurer import TextMeasurer

        tm = TextMeasurer()
        _ = tm.measure_text("Test", font_name="Arial", size_pt=14)
        _ = tm.measure_text("Test", font_name="Arial", size_pt=24)
        assert len(tm._font_cache) >= 2


class TestTextMeasurerDPI:
    """DPI conversion correctness."""

    @skip_no_fonts
    def test_14pt_height_approximately_correct(self):
        """At 72 DPI, 14pt font produces height ~0.194in (within 50% for font metrics)."""
        from deckforge.layout.text_measurer import TextMeasurer

        tm = TextMeasurer()
        bb = tm.measure_text("Ag", font_name="Arial", size_pt=14)
        expected_approx = 14 / 72  # ~0.194 inches
        # Allow wide tolerance for font metrics, ascenders, descenders, safety margin
        assert bb.height_inches > expected_approx * 0.5
        assert bb.height_inches < expected_approx * 3.0


class TestTextMeasurerSafetyMargin:
    """5% safety margin applied to measurements."""

    @skip_no_fonts
    def test_safety_margin_constant(self):
        from deckforge.layout.text_measurer import TextMeasurer

        assert TextMeasurer.SAFETY_MARGIN == 0.05

    @skip_no_fonts
    def test_measurement_dpi_constant(self):
        from deckforge.layout.text_measurer import TextMeasurer

        assert TextMeasurer.MEASUREMENT_DPI == 72


class TestTextMeasurerFallbackFont:
    """Fallback font when requested font not found."""

    @skip_no_fonts
    def test_unknown_font_falls_back(self):
        """Should not raise when font name is not found — uses fallback."""
        from deckforge.layout.text_measurer import TextMeasurer

        tm = TextMeasurer()
        bb = tm.measure_text("Test", font_name="NonExistentFont12345", size_pt=14)
        assert bb.width_inches > 0
        assert bb.height_inches > 0


class TestTextMeasurerBulletList:
    """measure_bullet_list for list items with spacing."""

    @skip_no_fonts
    def test_bullet_list_basic(self):
        from deckforge.layout.text_measurer import TextMeasurer

        tm = TextMeasurer()
        items = ["First bullet point", "Second bullet point", "Third bullet point"]
        bb = tm.measure_bullet_list(items, font_name="Arial", size_pt=14, max_width_inches=5.0)
        assert bb.width_inches > 0
        assert bb.height_inches > 0

    @skip_no_fonts
    def test_bullet_list_taller_than_single_item(self):
        from deckforge.layout.text_measurer import TextMeasurer

        tm = TextMeasurer()
        single = tm.measure_text("First bullet point", font_name="Arial", size_pt=14)
        items = ["First bullet point", "Second bullet point", "Third bullet point"]
        multi = tm.measure_bullet_list(items, font_name="Arial", size_pt=14, max_width_inches=10.0)
        assert multi.height_inches > single.height_inches

    @skip_no_fonts
    def test_bullet_list_empty(self):
        from deckforge.layout.text_measurer import TextMeasurer

        tm = TextMeasurer()
        bb = tm.measure_bullet_list([], font_name="Arial", size_pt=14, max_width_inches=5.0)
        assert bb.width_inches == 0.0
        assert bb.height_inches == 0.0
