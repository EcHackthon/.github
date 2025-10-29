"""Application configuration management."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os


@dataclass(frozen=True)
class GeminiSettings:
    """Settings for the Gemini CLI integration."""

    model: str
    profile: Optional[Path]
    prompt_path: Path
    history_path: Path
    temperature: float
    top_p: float

    @staticmethod
    def from_env(base_path: Path) -> "GeminiSettings":
        """Create settings from environment variables."""
        prompt = os.getenv("GEMINI_PROMPT_PATH", "prompts/primary_prompt.txt")
        history = os.getenv("GEMINI_HISTORY_PATH", "conversation_history.json")
        profile = os.getenv("GEMINI_PROFILE_PATH")
        profile_path = Path(profile).expanduser().resolve() if profile else None

        return GeminiSettings(
            model=os.getenv("GEMINI_MODEL", "gemini-1.5-pro-latest"),
            profile=profile_path,
            prompt_path=(base_path / prompt).resolve(),
            history_path=(base_path / history).resolve(),
            temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.9")),
            top_p=float(os.getenv("GEMINI_TOP_P", "0.95")),
        )


@dataclass(frozen=True)
class SpotifySettings:
    """Settings required for Spotify API access."""

    client_id: str
    client_secret: str
    refresh_token: str
    user_id: str
    recommended_playlist_id: Optional[str]

    @staticmethod
    def from_env() -> "SpotifySettings":
        required = {
            "SPOTIFY_CLIENT_ID": os.getenv("SPOTIFY_CLIENT_ID"),
            "SPOTIFY_CLIENT_SECRET": os.getenv("SPOTIFY_CLIENT_SECRET"),
            "SPOTIFY_REFRESH_TOKEN": os.getenv("SPOTIFY_REFRESH_TOKEN"),
            "SPOTIFY_USER_ID": os.getenv("SPOTIFY_USER_ID"),
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise EnvironmentError(
                "Missing required Spotify settings: " + ", ".join(missing)
            )

        return SpotifySettings(
            client_id=required["SPOTIFY_CLIENT_ID"],
            client_secret=required["SPOTIFY_CLIENT_SECRET"],
            refresh_token=required["SPOTIFY_REFRESH_TOKEN"],
            user_id=required["SPOTIFY_USER_ID"],
            recommended_playlist_id=os.getenv("SPOTIFY_RECOMMENDATION_PLAYLIST_ID"),
        )


@dataclass(frozen=True)
class BackendSettings:
    """Configuration for the backend hand-off."""

    recommendation_endpoint: Optional[str]
    api_key: Optional[str]

    @staticmethod
    def from_env() -> "BackendSettings":
        return BackendSettings(
            recommendation_endpoint=os.getenv("BACKEND_RECOMMENDATION_ENDPOINT"),
            api_key=os.getenv("BACKEND_API_KEY"),
        )


@dataclass(frozen=True)
class Settings:
    """Aggregated application settings."""

    gemini: GeminiSettings
    spotify: SpotifySettings
    backend: BackendSettings
    environment: str

    @staticmethod
    def load() -> "Settings":
        base_path = Path(os.getenv("PROJECT_ROOT", Path.cwd()))
        return Settings(
            gemini=GeminiSettings.from_env(base_path),
            spotify=SpotifySettings.from_env(),
            backend=BackendSettings.from_env(),
            environment=os.getenv("APP_ENV", "development"),
        )
