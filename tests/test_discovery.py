"""Tests for discovery endpoints: /v1/themes, /v1/slide-types, /v1/capabilities."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from deckforge.api.app import create_app
from deckforge.ir.enums import SlideType


@pytest.fixture
async def discovery_app():
    """Create a minimal FastAPI app for discovery endpoint testing.

    Discovery endpoints don't need database or Redis -- they serve static data.
    """
    app = create_app()
    yield app


@pytest.fixture
async def client(discovery_app):
    """Provide an httpx AsyncClient wired to the test app."""
    transport = ASGITransport(app=discovery_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# GET /v1/themes
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_themes_returns_list(client: AsyncClient):
    """GET /v1/themes returns a list with at least 15 themes."""
    resp = await client.get("/v1/themes")
    assert resp.status_code == 200
    data = resp.json()
    assert "themes" in data
    assert len(data["themes"]) >= 15


@pytest.mark.anyio
async def test_theme_has_required_fields(client: AsyncClient):
    """Each theme entry has id, name, description, and colors."""
    resp = await client.get("/v1/themes")
    data = resp.json()
    for theme in data["themes"]:
        assert "id" in theme
        assert "name" in theme
        assert "description" in theme
        assert "colors" in theme


@pytest.mark.anyio
async def test_theme_has_color_preview(client: AsyncClient):
    """Theme response includes color preview with primary, accent, background hex values."""
    resp = await client.get("/v1/themes")
    data = resp.json()
    for theme in data["themes"]:
        colors = theme["colors"]
        assert "primary" in colors
        assert "accent" in colors
        assert "background" in colors
        # Hex color format check
        for key in ("primary", "accent", "background"):
            assert colors[key].startswith("#"), f"Color {key} should be hex: {colors[key]}"


# ---------------------------------------------------------------------------
# GET /v1/slide-types
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_slide_types_returns_32_entries(client: AsyncClient):
    """GET /v1/slide-types returns all 32 slide types."""
    resp = await client.get("/v1/slide-types")
    assert resp.status_code == 200
    data = resp.json()
    assert "slide_types" in data
    assert data["total"] == 32
    assert len(data["slide_types"]) == 32


@pytest.mark.anyio
async def test_slide_type_has_required_fields(client: AsyncClient):
    """Each slide type entry has id, name, category, example_ir."""
    resp = await client.get("/v1/slide-types")
    data = resp.json()
    for st in data["slide_types"]:
        assert "id" in st
        assert "name" in st
        assert "category" in st
        assert "example_ir" in st


@pytest.mark.anyio
async def test_slide_type_category_filter(client: AsyncClient):
    """GET /v1/slide-types?category=finance returns only finance types."""
    resp = await client.get("/v1/slide-types", params={"category": "finance"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["slide_types"]) > 0
    for st in data["slide_types"]:
        assert st["category"] == "finance"


# ---------------------------------------------------------------------------
# SlideTypeRegistry completeness
# ---------------------------------------------------------------------------


def test_slide_type_registry_covers_all_enum_values():
    """SlideTypeRegistry has entries for all slide types in SlideType enum."""
    from deckforge.services.slide_type_registry import SlideTypeRegistry

    registry = SlideTypeRegistry()
    all_types = registry.get_all()
    registry_ids = {st["id"] for st in all_types}
    enum_values = {e.value for e in SlideType}
    assert registry_ids == enum_values, f"Missing: {enum_values - registry_ids}"


def test_slide_type_example_ir_is_valid():
    """Each slide type example_ir passes Pydantic validation."""
    from deckforge.ir.presentation import Presentation
    from deckforge.services.slide_type_registry import SlideTypeRegistry

    registry = SlideTypeRegistry()
    for st in registry.get_all():
        ir = st["example_ir"]
        # Should not raise ValidationError
        Presentation.model_validate(ir)


# ---------------------------------------------------------------------------
# GET /v1/capabilities
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_capabilities(client: AsyncClient):
    """GET /v1/capabilities returns api_version, max_slides_sync, formats, features."""
    resp = await client.get("/v1/capabilities")
    assert resp.status_code == 200
    data = resp.json()
    assert data["api_version"] == "1.0"
    assert data["max_slides_sync"] == 10
    assert "pptx" in data["supported_output_formats"]
    assert data["features"]["streaming"] is True
    assert data["features"]["finance_slides"] is True
    assert "rate_limits" in data
