"""Conversation orchestrator tying Gemini, mood detection and Spotify together."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from src.conversation.gemini_cli import GeminiCLIClient
from src.conversation.mood_detector import MoodAnalysis, MoodDetector
from src.spotify.client import SpotifyClient
from src.spotify.recommendation import RecommendationRequest, RecommendationResult
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ConversationTurn:
    """Represents a single conversation turn."""

    user_message: str
    ai_response: str
    mood_analysis: MoodAnalysis
    recommendations: Sequence[RecommendationResult]


class ConversationOrchestrator:
    """High-level orchestrator for the AI DJ experience."""

    def __init__(
        self,
        gemini_client: GeminiCLIClient,
        mood_detector: MoodDetector,
        spotify_client: SpotifyClient,
        mood_confidence_threshold: float = 0.45,
    ) -> None:
        self._gemini = gemini_client
        self._mood_detector = mood_detector
        self._spotify = spotify_client
        self._confidence_threshold = mood_confidence_threshold
        self._conversation_log: List[ConversationTurn] = []

    def run_interaction(self, initial_messages: Iterable[str]) -> List[ConversationTurn]:
        """Drive an interaction and collect recommendations."""
        ai_response = self._gemini.send_messages(initial_messages)
        mood = self._mood_detector.analyse(ai_response)
        logger.info("Gemini responded with mood %s (%.2f)", mood.mood, mood.confidence)

        recommendations: Sequence[RecommendationResult] = []
        if mood.confidence >= self._confidence_threshold:
            recommendations = self._spotify.recommend_for_mood(
                RecommendationRequest(mood=mood.mood, rationale=mood.rationale)
            )
        else:
            logger.info(
                "Skipping Spotify recommendation due to low confidence (%.2f)",
                mood.confidence,
            )

        turn = ConversationTurn(
            user_message="\n".join(initial_messages),
            ai_response=ai_response,
            mood_analysis=mood,
            recommendations=recommendations,
        )
        self._conversation_log.append(turn)
        return self._conversation_log

    @property
    def conversation_log(self) -> Sequence[ConversationTurn]:
        """Expose the conversation log for downstream systems."""
        return tuple(self._conversation_log)
