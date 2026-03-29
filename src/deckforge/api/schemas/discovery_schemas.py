"""Discovery endpoint response schemas for /v1/themes, /v1/slide-types, /v1/capabilities."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# GET /v1/themes
# ---------------------------------------------------------------------------


class ThemeColorPreview(BaseModel):
    """Subset of theme colors for quick preview in listings."""

    primary: str
    secondary: str
    accent: str
    background: str
    surface: str
    text_primary: str


class ThemeInfo(BaseModel):
    """Single theme entry in the themes list."""

    id: str
    name: str
    description: str
    version: str
    colors: ThemeColorPreview


class ThemeListResponse(BaseModel):
    """GET /v1/themes response."""

    themes: list[ThemeInfo]


# ---------------------------------------------------------------------------
# GET /v1/slide-types
# ---------------------------------------------------------------------------


class SlideTypeInfo(BaseModel):
    """Single slide type entry in the slide-types list."""

    id: str
    name: str
    description: str
    category: str
    required_elements: list[str]
    optional_elements: list[str]
    example_ir: dict[str, Any]


class SlideTypeListResponse(BaseModel):
    """GET /v1/slide-types response."""

    slide_types: list[SlideTypeInfo]
    total: int


# ---------------------------------------------------------------------------
# GET /v1/capabilities
# ---------------------------------------------------------------------------


class RateLimits(BaseModel):
    """Rate limits per billing tier (requests per minute)."""

    starter: int
    pro: int
    enterprise: int


class FeatureFlags(BaseModel):
    """Feature flags indicating which capabilities are enabled."""

    streaming: bool
    webhooks: bool
    batch: bool
    finance_slides: bool
    content_generation: bool


class CapabilitiesResponse(BaseModel):
    """GET /v1/capabilities response."""

    api_version: str
    max_slides_sync: int
    max_slides_async: int
    supported_output_formats: list[str]
    supported_chart_types: list[str]
    rate_limits: RateLimits
    features: FeatureFlags
