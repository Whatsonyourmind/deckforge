"""Visual element models — image, icon, shape, divider, spacer, logo, background."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from deckforge.ir.elements.base import BaseElement


# ── Content Models ─────────────────────────────────────────────────────────────


class ImageContent(BaseModel):
    url: str | None = None
    base64: str | None = None
    alt_text: str = ""
    fit: Literal["contain", "cover", "fill"] = "contain"


class IconContent(BaseModel):
    name: str
    set: str = "default"
    color: str | None = None


class ShapeContent(BaseModel):
    shape: Literal["rectangle", "circle", "rounded_rect", "arrow", "line"]
    fill: str | None = None
    stroke: str | None = None


class LogoContent(BaseModel):
    url: str | None = None
    placement: Literal["top_left", "top_right", "bottom_left", "bottom_right", "center"] = (
        "top_left"
    )


class BackgroundContent(BaseModel):
    color: str | None = None
    image_url: str | None = None
    gradient: dict | None = None


# ── Element Models ─────────────────────────────────────────────────────────────


class ImageElement(BaseElement):
    type: Literal["image"] = "image"
    content: ImageContent


class IconElement(BaseElement):
    type: Literal["icon"] = "icon"
    content: IconContent


class ShapeElement(BaseElement):
    type: Literal["shape"] = "shape"
    content: ShapeContent


class DividerElement(BaseElement):
    type: Literal["divider"] = "divider"


class SpacerElement(BaseElement):
    type: Literal["spacer"] = "spacer"


class LogoElement(BaseElement):
    type: Literal["logo"] = "logo"
    content: LogoContent


class BackgroundElement(BaseElement):
    type: Literal["background"] = "background"
    content: BackgroundContent
