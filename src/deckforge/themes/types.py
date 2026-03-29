"""Theme type models — Pydantic models for resolved theme structure."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ThemeColors(BaseModel):
    """Complete color palette for a resolved theme."""

    primary: str
    secondary: str
    accent: str
    background: str
    surface: str
    text_primary: str
    text_secondary: str
    text_muted: str
    positive: str
    negative: str
    warning: str


class ThemeTypography(BaseModel):
    """Typography settings — families, scale, weights, line height."""

    heading_family: str
    body_family: str
    mono_family: str
    scale: dict[str, int] = Field(
        default_factory=lambda: {
            "h1": 44,
            "h2": 36,
            "h3": 28,
            "subtitle": 24,
            "body": 18,
            "caption": 14,
            "footnote": 10,
        }
    )
    weights: dict[str, int] = Field(
        default_factory=lambda: {
            "heading": 700,
            "subtitle": 600,
            "body": 400,
            "caption": 400,
        }
    )
    line_height: float = 1.4


class ThemeSpacing(BaseModel):
    """Spacing configuration in inches."""

    margin_top: float
    margin_bottom: float
    margin_left: float
    margin_right: float
    gutter: float
    element_gap: float
    section_gap: float


class ComponentStyle(BaseModel):
    """Per-region styling within a slide master."""

    font_family: str | None = None
    font_size: int | None = None
    font_weight: int | None = None
    color: str | None = None
    alignment: str | None = None
    background: str | None = None
    bullet_color: str | None = None
    indent: float | None = None
    columns: int | None = None
    min_height: float | None = None


class SlideMaster(BaseModel):
    """Slide master — background color and per-region styles."""

    background: str
    regions: dict[str, ComponentStyle] = Field(default_factory=dict)


class LogoDefaults(BaseModel):
    """Default logo placement config within a theme."""

    max_width: float = 1.0
    max_height: float = 0.5
    placement: str = "top_left"
    opacity: float = 1.0


class FooterDefaults(BaseModel):
    """Default footer config within a theme."""

    text: str | None = None
    include_page_numbers: bool = True
    include_date: bool = False
    include_logo: bool = False


class ResolvedTheme(BaseModel):
    """Fully resolved theme with all $references expanded to concrete values."""

    name: str
    description: str
    version: str = "1.0"
    colors: ThemeColors
    typography: ThemeTypography
    spacing: ThemeSpacing
    slide_masters: dict[str, SlideMaster] = Field(default_factory=dict)
    chart_colors: list[str] = Field(default_factory=list)
    logo: LogoDefaults = Field(default_factory=LogoDefaults)
    footer: FooterDefaults = Field(default_factory=FooterDefaults)
    protected_keys: list[str] = Field(default_factory=list)
