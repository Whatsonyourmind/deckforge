"""Integration tests for OpenAPI schema generation."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_docs_returns_200(async_client: AsyncClient):
    """GET /docs returns the auto-generated Swagger UI."""
    resp = await async_client.get("/docs")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_openapi_schema_generates(app):
    """The OpenAPI schema generates without error."""
    schema = app.openapi()
    assert schema is not None
    assert schema["info"]["title"] == "DeckForge API"
    assert schema["info"]["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_openapi_contains_render_path(app):
    """OpenAPI schema contains the /v1/render path."""
    schema = app.openapi()
    assert "/v1/render" in schema["paths"]


@pytest.mark.asyncio
async def test_openapi_contains_presentation_model(app):
    """OpenAPI schema references the Presentation IR model."""
    schema = app.openapi()
    # The Presentation model should be in the components/schemas
    schemas = schema.get("components", {}).get("schemas", {})
    assert "Presentation" in schemas, (
        f"Presentation model not found in schemas. Available: {list(schemas.keys())}"
    )
