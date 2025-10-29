"""Backend integration helpers."""
from __future__ import annotations

from typing import Sequence

from src.conversation.orchestrator import ConversationTurn
from src.utils.http import HttpSession
from src.utils.logging import get_logger

logger = get_logger(__name__)


class BackendClient:
    """Minimal HTTP client to forward recommendations to the backend."""

    def __init__(self, endpoint: str, api_key: str | None = None) -> None:
        self._endpoint = endpoint
        self._api_key = api_key
        self._session = HttpSession()

    def send_turns(self, turns: Sequence[ConversationTurn]) -> None:
        payload = [
            {
                "user_message": turn.user_message,
                "ai_response": turn.ai_response,
                "mood": turn.mood_analysis.mood,
                "confidence": turn.mood_analysis.confidence,
                "rationale": turn.mood_analysis.rationale,
                "recommendations": [
                    {
                        "mood": rec.mood,
                        "rationale": rec.rationale,
                        "tracks": [
                            {
                                "id": track.id,
                                "name": track.name,
                                "artists": track.artists,
                                "preview_url": track.preview_url,
                                "external_url": track.external_url,
                            }
                            for track in rec.tracks
                        ],
                    }
                    for rec in turn.recommendations
                ],
            }
            for turn in turns
        ]
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["X-API-Key"] = self._api_key
        logger.info("Sending %d conversation turns to backend", len(turns))
        response = self._session.request(
            "POST",
            self._endpoint,
            json_body=payload,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
