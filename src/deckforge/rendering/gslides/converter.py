"""Unit conversion utilities for Google Slides API.

Converts DeckForge internal units (inches, hex colors, point sizes)
to Google Slides API units (EMU, RGB floats, API-style dicts).
"""

from __future__ import annotations

import uuid

# 1 inch = 914400 EMU (English Metric Units)
EMU_PER_INCH: int = 914400

# 1 point = 12700 EMU
EMU_PER_PT: int = 12700


def inches_to_emu(inches: float) -> int:
    """Convert inches to EMU (English Metric Units).

    Args:
        inches: Measurement in inches.

    Returns:
        Integer EMU value, rounded to nearest.
    """
    return round(inches * EMU_PER_INCH)


def hex_to_slides_rgb(hex_color: str) -> dict:
    """Convert hex color string to Slides API RGB float dict.

    Args:
        hex_color: Color string like '#FF0000' or 'FF0000'.

    Returns:
        Dict with 'red', 'green', 'blue' keys as floats 0.0-1.0.
    """
    color = hex_color.lstrip("#")
    r = int(color[0:2], 16) / 255.0
    g = int(color[2:4], 16) / 255.0
    b = int(color[4:6], 16) / 255.0
    return {"red": r, "green": g, "blue": b}


def make_color(hex_color: str) -> dict:
    """Wrap a hex color in the Slides API OpaqueColor structure.

    Args:
        hex_color: Color string like '#FF0000'.

    Returns:
        Slides API color dict with opaqueColor.rgbColor.
    """
    return {"opaqueColor": {"rgbColor": hex_to_slides_rgb(hex_color)}}


def make_size(width_inches: float, height_inches: float) -> dict:
    """Create a Slides API Size object from inch dimensions.

    Args:
        width_inches: Width in inches.
        height_inches: Height in inches.

    Returns:
        Slides API Size dict with EMU magnitude.
    """
    return {
        "width": {"magnitude": inches_to_emu(width_inches), "unit": "EMU"},
        "height": {"magnitude": inches_to_emu(height_inches), "unit": "EMU"},
    }


def make_transform(
    x_inches: float,
    y_inches: float,
    width_inches: float = 0.0,
    height_inches: float = 0.0,
) -> dict:
    """Create a Slides API AffineTransform from position in inches.

    The transform positions an element using translateX/translateY in EMU.
    scaleX and scaleY are set to 1 (no scaling), shear to 0.

    Args:
        x_inches: X position in inches.
        y_inches: Y position in inches.
        width_inches: Unused (kept for API symmetry with make_element_properties).
        height_inches: Unused (kept for API symmetry).

    Returns:
        Slides API AffineTransform dict.
    """
    return {
        "scaleX": 1,
        "scaleY": 1,
        "shearX": 0,
        "shearY": 0,
        "translateX": inches_to_emu(x_inches),
        "translateY": inches_to_emu(y_inches),
        "unit": "EMU",
    }


def make_element_properties(
    page_id: str,
    x: float,
    y: float,
    w: float,
    h: float,
) -> dict:
    """Create elementProperties dict for CreateShape/CreateImage/CreateTable requests.

    Args:
        page_id: The page object ID where the element will be placed.
        x: X position in inches.
        y: Y position in inches.
        w: Width in inches.
        h: Height in inches.

    Returns:
        Slides API elementProperties dict.
    """
    return {
        "pageObjectId": page_id,
        "size": make_size(w, h),
        "transform": make_transform(x, y),
    }


def pt_to_slides_font_size(pt: int) -> dict:
    """Convert point size to Slides API Dimension.

    Args:
        pt: Font size in points.

    Returns:
        Slides API Dimension dict with PT unit.
    """
    return {"magnitude": pt, "unit": "PT"}


def is_bold_weight(weight: int) -> bool:
    """Determine if a font weight should be rendered as bold.

    Args:
        weight: CSS-style font weight (100-900).

    Returns:
        True if weight >= 600 (semibold or bolder).
    """
    return weight >= 600


def generate_object_id() -> str:
    """Generate a unique object ID for Slides API objects.

    Google Slides API requires unique IDs (max 50 chars).

    Returns:
        24-character hex string.
    """
    return uuid.uuid4().hex[:24]
