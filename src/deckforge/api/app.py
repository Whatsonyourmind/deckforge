"""FastAPI application factory.

Creates the app with all routers mounted under the /v1 prefix.
"""

from __future__ import annotations

from fastapi import FastAPI

from deckforge.api.routes.analytics import router as analytics_router
from deckforge.api.routes.auth_google import router as auth_google_router
from deckforge.api.routes.batch import router as batch_router
from deckforge.api.routes.billing import router as billing_router
from deckforge.api.routes.decks import router as decks_router
from deckforge.api.routes.discovery import router as discovery_router
from deckforge.api.routes.estimate import router as estimate_router
from deckforge.api.routes.generate import router as generate_router
from deckforge.api.routes.health import router as health_router
from deckforge.api.routes.jobs import router as jobs_router
from deckforge.api.routes.onboarding import router as onboarding_router
from deckforge.api.routes.pricing import router as pricing_router
from deckforge.api.routes.preview import router as preview_router
from deckforge.api.routes.render import router as render_router
from deckforge.api.routes.webhooks import router as webhooks_router


def create_app(lifespan=None) -> FastAPI:
    """Build the FastAPI application with all routes registered."""
    app = FastAPI(
        title="DeckForge API",
        version="0.1.0",
        description="Executive-ready slides, one API call away.",
        lifespan=lifespan,
    )

    app.include_router(health_router, prefix="/v1")
    app.include_router(discovery_router, prefix="/v1")
    app.include_router(render_router, prefix="/v1")
    app.include_router(generate_router, prefix="/v1")
    app.include_router(preview_router, prefix="/v1")
    app.include_router(jobs_router, prefix="/v1")
    app.include_router(auth_google_router, prefix="/v1")
    app.include_router(decks_router, prefix="/v1")
    app.include_router(estimate_router, prefix="/v1")
    app.include_router(batch_router, prefix="/v1")
    app.include_router(webhooks_router, prefix="/v1")
    app.include_router(billing_router, prefix="/v1")
    app.include_router(pricing_router, prefix="/v1")
    app.include_router(onboarding_router, prefix="/v1")
    app.include_router(analytics_router, prefix="/v1")

    return app
