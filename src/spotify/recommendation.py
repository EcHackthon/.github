"""Data structures for Spotify recommendation requests and responses."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class RecommendationRequest:
    """Represents the information required to request recommendations."""

    mood: str
    rationale: str
    limit: int = 5


@dataclass(frozen=True)
class TrackInfo:
    """Relevant details for a Spotify track."""

    id: str
    name: str
    artists: Sequence[str]
    preview_url: str | None
    external_url: str


@dataclass(frozen=True)
class RecommendationResult:
    """Represents a recommendation response entry."""

    mood: str
    rationale: str
    tracks: Sequence[TrackInfo]
