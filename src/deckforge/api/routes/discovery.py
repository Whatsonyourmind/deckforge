"""Discovery endpoints — /v1/themes, /v1/slide-types, /v1/capabilities.

These public endpoints enable agents and developers to programmatically
explore DeckForge's available themes, slide types, and API capabilities.
No authentication required.
"""

from __future__ import annotations

import functools
import logging
from typing import Any

from fastapi import APIRouter, Query

from deckforge.api.schemas.discovery_schemas import (
    CapabilitiesResponse,
    FeatureFlags,
    RateLimits,
    SlideTypeInfo,
    SlideTypeListResponse,
    ThemeColorPreview,
    ThemeInfo,
    ThemeListResponse,
)
from deckforge.ir.enums import ChartType
from deckforge.services.slide_type_registry import SlideTypeRegistry
from deckforge.themes.registry import ThemeRegistry

logger = logging.getLogger(__name__)

router = APIRouter(tags=["discovery"])

# ---------------------------------------------------------------------------
# Singleton registries (immutable data, safe to share)
# ---------------------------------------------------------------------------

_theme_registry = ThemeRegistry()
_slide_type_registry = SlideTypeRegistry()


# ---------------------------------------------------------------------------
# GET /v1/themes
# ---------------------------------------------------------------------------


@functools.lru_cache(maxsize=1)
def _build_theme_list() -> list[dict[str, Any]]:
    """Build and cache the theme list with color previews.

    Themes are YAML files loaded from disk -- they rarely change,
    so caching the result avoids repeated file I/O.
    """
    themes: list[dict[str, Any]] = []
    for meta in _theme_registry.list_themes():
        # Load the full theme to extract color preview
        try:
            resolved = _theme_registry.load_theme(meta["id"])
            colors = ThemeColorPreview(
                primary=resolved.colors.primary,
                secondary=resolved.colors.secondary,
                accent=resolved.colors.accent,
                background=resolved.colors.background,
                surface=resolved.colors.surface,
                text_primary=resolved.colors.text_primary,
            )
        except Exception:
            logger.warning("Failed to load theme '%s' for color preview", meta["id"])
            colors = ThemeColorPreview(
                primary="#000000",
                secondary="#333333",
                accent="#666666",
                background="#FFFFFF",
                surface="#F5F5F5",
                text_primary="#000000",
            )
        themes.append({
            "id": meta["id"],
            "name": meta["name"],
            "description": meta["description"],
            "version": meta["version"],
            "colors": colors.model_dump(),
        })
    return themes


@router.get("/themes", response_model=ThemeListResponse)
async def list_themes() -> ThemeListResponse:
    """List all available themes with metadata and color previews."""
    theme_dicts = _build_theme_list()
    return ThemeListResponse(
        themes=[ThemeInfo.model_validate(t) for t in theme_dicts],
    )


# ---------------------------------------------------------------------------
# GET /v1/slide-types
# ---------------------------------------------------------------------------


@router.get("/slide-types", response_model=SlideTypeListResponse)
async def list_slide_types(
    category: str | None = Query(None, description="Filter by category: universal, finance"),
) -> SlideTypeListResponse:
    """List all available slide types with metadata and example IR."""
    if category:
        items = _slide_type_registry.get_by_category(category)
    else:
        items = _slide_type_registry.get_all()
    return SlideTypeListResponse(
        slide_types=[SlideTypeInfo.model_validate(st) for st in items],
        total=len(items),
    )


# ---------------------------------------------------------------------------
# GET /v1/capabilities
# ---------------------------------------------------------------------------


@router.get("/capabilities", response_model=CapabilitiesResponse)
async def get_capabilities() -> CapabilitiesResponse:
    """Return API capabilities, limits, and feature flags."""
    return CapabilitiesResponse(
        api_version="1.0",
        max_slides_sync=10,
        max_slides_async=200,
        supported_output_formats=["pptx"],
        supported_chart_types=[ct.value for ct in ChartType],
        rate_limits=RateLimits(starter=10, pro=60, enterprise=300),
        features=FeatureFlags(
            streaming=True,
            webhooks=True,
            batch=True,
            finance_slides=True,
            content_generation=True,
        ),
    )
