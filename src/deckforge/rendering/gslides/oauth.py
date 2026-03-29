"""Google OAuth credential handler for Google Slides/Sheets/Drive access.

Provides authorization URL generation, code exchange, credential building,
and token refresh for the Google Slides rendering pipeline.
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)

# Google OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

# Required scopes for Slides + Sheets + Drive
REQUIRED_SCOPES = [
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]


class GoogleOAuthHandler:
    """Handles Google OAuth2 flow for accessing Slides/Sheets/Drive APIs.

    Generates authorization URLs, exchanges authorization codes for tokens,
    and builds credential objects for API access.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ) -> None:
        """Initialize the OAuth handler.

        Args:
            client_id: Google OAuth client ID.
            client_secret: Google OAuth client secret.
            redirect_uri: OAuth redirect URI.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_authorization_url(self, state: str = "") -> str:
        """Generate the Google OAuth consent URL.

        Args:
            state: Optional state parameter for CSRF protection.

        Returns:
            Full authorization URL for the user to visit.
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(REQUIRED_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
        }
        if state:
            params["state"] = state

        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    def exchange_code(self, code: str) -> dict:
        """Exchange an authorization code for tokens.

        Args:
            code: Authorization code from Google OAuth callback.

        Returns:
            Dict with access_token, refresh_token, expires_in, token_type.

        Raises:
            httpx.HTTPStatusError: If the token exchange fails.
        """
        with httpx.Client() as client:
            response = client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            response.raise_for_status()
            return response.json()

    def build_credentials(
        self,
        access_token: str,
        refresh_token: str,
    ) -> Any:
        """Build Google OAuth credentials from stored tokens.

        Args:
            access_token: Current access token.
            refresh_token: Refresh token for renewal.

        Returns:
            google.oauth2.credentials.Credentials object.

        Raises:
            ImportError: If google-auth is not installed.
        """
        from google.oauth2.credentials import Credentials

        return Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri=GOOGLE_TOKEN_URL,
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=REQUIRED_SCOPES,
        )

    def refresh_if_needed(self, credentials: Any) -> Any:
        """Refresh credentials if they are expired or about to expire.

        Args:
            credentials: Google OAuth credentials object.

        Returns:
            Refreshed credentials.
        """
        from google.auth.transport.requests import Request

        if credentials.expired or not credentials.valid:
            credentials.refresh(Request())

        return credentials


def build_credentials(
    access_token: str,
    refresh_token: str,
    client_id: str,
    client_secret: str,
) -> Any:
    """Module-level helper to build Google OAuth credentials from stored tokens.

    Args:
        access_token: Current access token.
        refresh_token: Refresh token for renewal.
        client_id: Google OAuth client ID.
        client_secret: Google OAuth client secret.

    Returns:
        google.oauth2.credentials.Credentials object.
    """
    from google.oauth2.credentials import Credentials

    return Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri=GOOGLE_TOKEN_URL,
        client_id=client_id,
        client_secret=client_secret,
        scopes=REQUIRED_SCOPES,
    )


__all__ = ["GoogleOAuthHandler", "build_credentials"]
