"""Spotify API client for recommendation retrieval."""
from __future__ import annotations

from typing import Dict, Optional, Sequence

from src.spotify.auth import SpotifyTokenManager
from src.spotify.recommendation import (
    RecommendationRequest,
    RecommendationResult,
    TrackInfo,
)
from src.utils.http import HttpResponse, HttpSession
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SpotifyClient:
    """High-level Spotify client tailored for the AI DJ use case."""

    MOOD_SEEDS: Dict[str, Dict[str, Sequence[str]]] = {
        "positive": {"seed_genres": ["happy", "pop"], "target_valence": 0.8, "target_energy": 0.7},
        "negative": {"seed_genres": ["sad", "acoustic"], "target_valence": 0.2},
        "calm": {"seed_genres": ["chill", "ambient"], "target_energy": 0.3, "target_valence": 0.55},
        "neutral": {"seed_genres": ["indie", "alt"], "target_valence": 0.5},
    }

    def __init__(
        self,
        token_manager: SpotifyTokenManager,
        user_id: str,
        *,
        recommended_playlist_id: str | None = None,
        session: Optional[HttpSession] = None,
    ) -> None:
        self._token_manager = token_manager
        self._user_id = user_id
        self._session = session or HttpSession()
        self._recommended_playlist_id = recommended_playlist_id

    def _request(self, method: str, url: str, *, retry: bool = False, **kwargs) -> HttpResponse:
        token = self._token_manager.get_access_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        headers.setdefault("Content-Type", "application/json")
        response = self._session.request(
            method,
            url,
            headers=headers,
            timeout=10,
            **kwargs,
        )
        if response.status_code == 401 and not retry:
            logger.warning("Received 401 from Spotify, forcing token refresh")
            self._token_manager.invalidate()
            return self._request(method, url, retry=True, headers=headers, **kwargs)
        response.raise_for_status()
        return response

    def recommend_for_mood(
        self, request: RecommendationRequest
    ) -> Sequence[RecommendationResult]:
        logger.info("Requesting Spotify recommendations for mood %s", request.mood)
        params = self._build_recommendation_params(request)
        response = self._request(
            "GET",
            "https://api.spotify.com/v1/recommendations",
            params=params,
        )
        data = response.json()
        tracks = [self._map_track(item) for item in data.get("tracks", [])][: request.limit]
        if not tracks and self._recommended_playlist_id:
            logger.info(
                "No direct recommendations returned; falling back to playlist %s",
                self._recommended_playlist_id,
            )
            tracks = self._fetch_playlist_tracks(limit=request.limit)
        return [
            RecommendationResult(
                mood=request.mood,
                rationale=request.rationale,
                tracks=tracks,
            )
        ]

    def _build_recommendation_params(self, request: RecommendationRequest) -> Dict[str, str]:
        seeds = self.MOOD_SEEDS.get(request.mood, self.MOOD_SEEDS["neutral"])
        params: Dict[str, str] = {
            "limit": str(request.limit),
        }
        for key, value in seeds.items():
            if isinstance(value, Sequence) and not isinstance(value, str):
                params[key] = ",".join(value)
            else:
                params[key] = str(value)
        return params

    def _fetch_playlist_tracks(self, *, limit: int) -> Sequence[TrackInfo]:
        if not self._recommended_playlist_id:
            return []
        response = self._request(
            "GET",
            f"https://api.spotify.com/v1/playlists/{self._recommended_playlist_id}/tracks",
            params={"limit": str(limit)},
        )
        data = response.json()
        tracks: list[TrackInfo] = []
        for item in data.get("items", []):
            track_data = item.get("track") if isinstance(item, dict) else None
            if not isinstance(track_data, dict):
                continue
            tracks.append(self._map_track(track_data))
            if len(tracks) >= limit:
                break
        return tracks

    @staticmethod
    def _map_track(item: Dict[str, object]) -> TrackInfo:
        artists = [artist["name"] for artist in item.get("artists", [])]  # type: ignore[index]
        return TrackInfo(
            id=item.get("id", ""),
            name=item.get("name", ""),
            artists=artists,
            preview_url=item.get("preview_url"),
            external_url=item.get("external_urls", {}).get("spotify", ""),
        )
