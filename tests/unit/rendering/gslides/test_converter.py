"""Tests for Google Slides unit converter functions."""

from __future__ import annotations

import pytest

from deckforge.rendering.gslides.converter import (
    EMU_PER_INCH,
    generate_object_id,
    hex_to_slides_rgb,
    inches_to_emu,
    is_bold_weight,
    make_color,
    make_element_properties,
    make_size,
    make_transform,
    pt_to_slides_font_size,
)


class TestInchesToEmu:
    def test_one_inch(self):
        assert inches_to_emu(1.0) == 914400

    def test_zero(self):
        assert inches_to_emu(0.0) == 0

    def test_widescreen_width(self):
        # 13.333 * 914400 = 12191695.2 -> rounds to 12191695
        result = inches_to_emu(13.333)
        assert result == round(13.333 * 914400)
        # For exact 13+1/3 inches: 13.333333... * 914400 = 12192000
        assert inches_to_emu(13 + 1 / 3) == 12192000

    def test_half_inch(self):
        assert inches_to_emu(0.5) == 457200

    def test_large_value(self):
        assert inches_to_emu(100.0) == 91440000

    def test_returns_int(self):
        result = inches_to_emu(1.5)
        assert isinstance(result, int)


class TestHexToSlidesRgb:
    def test_red(self):
        result = hex_to_slides_rgb("#FF0000")
        assert result == {"red": 1.0, "green": 0.0, "blue": 0.0}

    def test_white(self):
        result = hex_to_slides_rgb("#FFFFFF")
        assert result == {"red": 1.0, "green": 1.0, "blue": 1.0}

    def test_black(self):
        result = hex_to_slides_rgb("#000000")
        assert result == {"red": 0.0, "green": 0.0, "blue": 0.0}

    def test_dark_blue(self):
        result = hex_to_slides_rgb("#0A1E3D")
        assert abs(result["red"] - 10 / 255) < 0.001
        assert abs(result["green"] - 30 / 255) < 0.001
        assert abs(result["blue"] - 61 / 255) < 0.001

    def test_without_hash(self):
        result = hex_to_slides_rgb("FF0000")
        assert result == {"red": 1.0, "green": 0.0, "blue": 0.0}

    def test_lowercase(self):
        result = hex_to_slides_rgb("#ff0000")
        assert result == {"red": 1.0, "green": 0.0, "blue": 0.0}


class TestMakeColor:
    def test_wraps_in_opaque_color(self):
        result = make_color("#FFFFFF")
        assert "opaqueColor" in result
        assert "rgbColor" in result["opaqueColor"]
        rgb = result["opaqueColor"]["rgbColor"]
        assert rgb == {"red": 1.0, "green": 1.0, "blue": 1.0}


class TestMakeSize:
    def test_basic(self):
        result = make_size(2.0, 1.5)
        assert result == {
            "width": {"magnitude": 1828800, "unit": "EMU"},
            "height": {"magnitude": 1371600, "unit": "EMU"},
        }


class TestMakeTransform:
    def test_basic(self):
        result = make_transform(1.0, 2.0, 3.0, 4.0)
        assert result["scaleX"] == 1
        assert result["scaleY"] == 1
        assert result["shearX"] == 0
        assert result["shearY"] == 0
        assert result["translateX"] == inches_to_emu(1.0)
        assert result["translateY"] == inches_to_emu(2.0)
        assert result["unit"] == "EMU"


class TestMakeElementProperties:
    def test_contains_page_id(self):
        result = make_element_properties("page_abc", 1.0, 2.0, 3.0, 4.0)
        assert result["pageObjectId"] == "page_abc"
        assert "size" in result
        assert "transform" in result


class TestPtToSlidesFontSize:
    def test_basic(self):
        assert pt_to_slides_font_size(28) == {"magnitude": 28, "unit": "PT"}

    def test_small(self):
        assert pt_to_slides_font_size(10) == {"magnitude": 10, "unit": "PT"}


class TestIsBoldWeight:
    def test_bold_700(self):
        assert is_bold_weight(700) is True

    def test_semibold_600(self):
        assert is_bold_weight(600) is True

    def test_normal_400(self):
        assert is_bold_weight(400) is False

    def test_light_300(self):
        assert is_bold_weight(300) is False


class TestGenerateObjectId:
    def test_length(self):
        oid = generate_object_id()
        assert len(oid) == 24

    def test_unique(self):
        ids = {generate_object_id() for _ in range(100)}
        assert len(ids) == 100

    def test_is_string(self):
        assert isinstance(generate_object_id(), str)
