"""Heuristics to derive user mood from conversation text."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MoodAnalysis:
    """Represents the outcome of a mood analysis."""

    mood: str
    confidence: float
    rationale: str


class MoodDetector:
    """Very small lexical heuristic mood detector."""

    POSITIVE_WORDS = {
        "happy",
        "great",
        "awesome",
        "fantastic",
        "joy",
        "excited",
        "love",
        "energetic",
    }
    NEGATIVE_WORDS = {
        "sad",
        "bad",
        "down",
        "tired",
        "angry",
        "upset",
        "anxious",
        "worried",
    }
    CALM_WORDS = {"calm", "relaxed", "chill", "peaceful"}

    def analyse(self, transcript: str) -> MoodAnalysis:
        """Analyse the mood of a transcript."""
        words = re.findall(r"[a-zA-Z']+", transcript.lower())
        counts: Dict[str, int] = {"positive": 0, "negative": 0, "calm": 0}

        for word in words:
            if word in self.POSITIVE_WORDS:
                counts["positive"] += 1
            elif word in self.NEGATIVE_WORDS:
                counts["negative"] += 1
            elif word in self.CALM_WORDS:
                counts["calm"] += 1

        logger.debug("Mood keyword counts: %s", counts)

        if all(value == 0 for value in counts.values()):
            return MoodAnalysis(mood="neutral", confidence=0.2, rationale="No strong mood keywords detected.")

        mood = max(counts, key=counts.get)
        total_hits = sum(counts.values())
        confidence = counts[mood] / total_hits if total_hits else 0.0
        rationale = f"Detected {counts[mood]} {mood} words out of {total_hits} mood keywords."
        return MoodAnalysis(mood=mood, confidence=confidence, rationale=rationale)
