"""DeckForge rendering package -- PPTX rendering engine."""

from __future__ import annotations

from deckforge.rendering.pptx_renderer import PptxRenderer
from deckforge.rendering.utils import (
    get_blank_layout,
    hex_to_rgb,
    resolve_font_name,
    set_slide_background,
    set_transition,
)

__all__ = [
    "PptxRenderer",
    "get_blank_layout",
    "hex_to_rgb",
    "resolve_font_name",
    "set_slide_background",
    "set_transition",
]
