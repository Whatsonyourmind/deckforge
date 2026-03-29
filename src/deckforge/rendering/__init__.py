"""DeckForge rendering package -- PPTX and Google Slides rendering engines."""

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

# Google Slides renderer is optional (requires google-api-python-client)
try:
    from deckforge.rendering.gslides import GoogleSlidesRenderer, GoogleSlidesResult

    __all__.extend(["GoogleSlidesRenderer", "GoogleSlidesResult"])
except ImportError:
    pass
