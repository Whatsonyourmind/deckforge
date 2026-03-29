"""Brand kit models — colors, fonts, logo, footer, and tone configuration."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from deckforge.ir.enums import Tone


class BrandColors(BaseModel):
    """Brand color palette."""

    primary: str
    secondary: str | None = None
    accent: list[str] = []
    background: str | None = None
    text: str | None = None
    muted: str | None = None


class BrandFonts(BaseModel):
    """Brand font configuration."""

    heading: str | None = None
    body: str | None = None
    mono: str | None = None
    caption: str | None = None


class LogoConfig(BaseModel):
    """Logo placement and size configuration."""

    url: str
    placement: Literal["top_left", "top_right", "bottom_left", "bottom_right", "center"] = (
        "top_left"
    )
    max_width: float | None = None
    max_height: float | None = None


class FooterConfig(BaseModel):
    """Footer configuration for all slides."""

    text: str | None = None
    include_page_numbers: bool = True
    include_date: bool = False
    include_logo: bool = False


class BrandKit(BaseModel):
    """Complete brand kit overlay applied on top of themes."""

    colors: BrandColors | None = None
    fonts: BrandFonts | None = None
    logo: LogoConfig | None = None
    footer: FooterConfig | None = None
    tone: Tone | None = None
