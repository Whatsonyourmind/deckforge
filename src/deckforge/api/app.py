"""FastAPI application factory.

Creates the app with all routers mounted under the /v1 prefix.
"""

from __future__ import annotations

from fastapi import FastAPI

from deckforge.api.routes.health import router as health_router
from deckforge.api.routes.jobs import router as jobs_router
from deckforge.api.routes.preview import router as preview_router
from deckforge.api.routes.render import router as render_router


def create_app(lifespan=None) -> FastAPI:
    """Build the FastAPI application with all routes registered."""
    app = FastAPI(
        title="DeckForge API",
        version="0.1.0",
        description="Executive-ready slides, one API call away.",
        lifespan=lifespan,
    )

    app.include_router(health_router, prefix="/v1")
    app.include_router(render_router, prefix="/v1")
    app.include_router(preview_router, prefix="/v1")
    app.include_router(jobs_router, prefix="/v1")

    return app
