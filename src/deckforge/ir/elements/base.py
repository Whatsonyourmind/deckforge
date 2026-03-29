"""Base element model for all IR elements."""

from __future__ import annotations

from pydantic import BaseModel

from deckforge.ir.enums import ElementType


class Position(BaseModel):
    """Element position and dimensions (optional — layout engine fills these)."""

    x: float | None = None
    y: float | None = None
    width: float | None = None
    height: float | None = None


class BaseElement(BaseModel):
    """Base class for all slide elements."""

    type: ElementType
    position: Position | None = None
    style_overrides: dict | None = None
