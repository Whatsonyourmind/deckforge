"""Health check endpoint.

Returns service health including PostgreSQL and Redis connectivity checks.
No authentication required.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from sqlalchemy import text

from deckforge.api.schemas.responses import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    """Check API health including database and Redis connectivity."""
    checks: dict[str, str] = {}

    # PostgreSQL check
    try:
        from deckforge.db.engine import async_session_factory

        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception:
        checks["postgres"] = "error"

    # Redis check
    try:
        redis = request.app.state.redis
        await redis.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"

    all_ok = all(v == "ok" for v in checks.values())
    return HealthResponse(
        status="healthy" if all_ok else "degraded",
        checks=checks,
        version="0.1.0",
    )
