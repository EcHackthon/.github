"""Spotify token management."""
from __future__ import annotations

import base64
import time
from dataclasses import dataclass
from typing import Optional

from src.utils.http import HttpSession
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AccessToken:
    """Represents an OAuth access token."""

    token: str
    expires_at: float

    @property
    def is_expired(self) -> bool:
        return time.time() >= self.expires_at - 30


class SpotifyTokenManager:
    """Handles OAuth token refresh using a long-lived refresh token."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        session: Optional[HttpSession] = None,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token
        self._session = session or HttpSession()
        self._cached_token: Optional[AccessToken] = None

    def get_access_token(self) -> str:
        if self._cached_token and not self._cached_token.is_expired:
            return self._cached_token.token

        logger.info("Refreshing Spotify access token")
        auth_header = base64.b64encode(
            f"{self._client_id}:{self._client_secret}".encode("utf-8")
        ).decode("utf-8")

        response = self._session.request(
            "POST",
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
            },
            headers={
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        token = payload["access_token"]
        expires_in = payload.get("expires_in", 3600)
        self._cached_token = AccessToken(token=token, expires_at=time.time() + expires_in)
        return token

    def invalidate(self) -> None:
        """Force the next call to refresh the token."""
        self._cached_token = None
