"""Base slide model for all IR slide types."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

from deckforge.ir.enums import LayoutHint, SlideType, Transition

if TYPE_CHECKING:
    from deckforge.ir.elements import ElementUnion


class BaseSlide(BaseModel):
    """Base class for all slide types."""

    slide_type: SlideType
    elements: list[ElementUnion] = []
    layout_hint: LayoutHint | None = None
    transition: Transition | None = None
    speaker_notes: str | None = None
    build_animations: list[int] | None = None
