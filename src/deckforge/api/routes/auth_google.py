"""Google OAuth endpoints for authorizing Google Drive/Slides/Sheets access.

These endpoints allow users to connect their Google account to DeckForge
so that presentations can be rendered directly to Google Slides.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, status

from deckforge.api.deps import DbSession
from deckforge.api.middleware.auth import CurrentApiKey
from deckforge.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/google", tags=["auth"])


def _get_oauth_handler():
    """Build a GoogleOAuthHandler from settings.

    Raises:
        HTTPException: If Google OAuth is not configured.
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google OAuth is not configured. Set DECKFORGE_GOOGLE_CLIENT_ID "
            "and DECKFORGE_GOOGLE_CLIENT_SECRET environment variables.",
        )

    from deckforge.rendering.gslides.oauth import GoogleOAuthHandler

    return GoogleOAuthHandler(
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )


@router.get("/authorize")
async def authorize(
    api_key: CurrentApiKey,
    state: str = Query(default=""),
) -> dict:
    """Generate a Google OAuth consent URL.

    The user should be redirected to this URL to authorize Google access.

    Returns:
        JSON with authorization_url.
    """
    handler = _get_oauth_handler()
    auth_url = handler.get_authorization_url(state=state or str(api_key.uuid_id))

    return {
        "authorization_url": auth_url,
        "scopes": [
            "presentations",
            "spreadsheets",
            "drive.file",
        ],
    }


@router.get("/callback")
async def callback(
    db: DbSession,
    code: str = Query(...),
    state: str = Query(default=""),
) -> dict:
    """OAuth callback -- exchange authorization code for tokens.

    Google redirects here after the user grants consent. The authorization
    code is exchanged for access + refresh tokens. The refresh token is
    stored with the API key for future use.

    Returns:
        JSON with status and scopes.
    """
    handler = _get_oauth_handler()

    try:
        tokens = handler.exchange_code(code)
    except Exception as e:
        logger.exception("Failed to exchange Google OAuth code")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange authorization code: {e}",
        ) from e

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No refresh token received. Try revoking access at "
            "https://myaccount.google.com/permissions and re-authorizing.",
        )

    # Store refresh token on the API key (identified by state param)
    # For MVP, store as plain text. TODO: Encrypt with Fernet.
    from deckforge.db.repositories import api_key_repo

    try:
        import uuid

        api_key_id = uuid.UUID(state)
        await api_key_repo.update_google_token(db, api_key_id, refresh_token)
        await db.commit()
    except (ValueError, Exception) as e:
        logger.warning("Could not store refresh token for state=%s: %s", state, e)

    return {
        "status": "connected",
        "scopes": [
            "presentations",
            "spreadsheets",
            "drive.file",
        ],
    }


@router.delete("")
async def revoke(
    db: DbSession,
    api_key: CurrentApiKey,
) -> dict:
    """Revoke Google access by deleting the stored refresh token.

    Returns:
        JSON with status.
    """
    from deckforge.db.repositories import api_key_repo

    await api_key_repo.update_google_token(db, api_key.uuid_id, None)
    await db.commit()

    return {"status": "disconnected"}
