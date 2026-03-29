"""Google Slides rendering package -- batchUpdate request builders and renderer."""

from __future__ import annotations

from deckforge.rendering.gslides.slides_renderer import (
    GoogleSlidesRenderer,
    GoogleSlidesResult,
)
from deckforge.rendering.gslides.oauth import GoogleOAuthHandler

__all__ = [
    "GoogleSlidesRenderer",
    "GoogleSlidesResult",
    "GoogleOAuthHandler",
]
