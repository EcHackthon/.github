"""Entry point for the AI DJ orchestration service."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List

from src.backend.http_client import BackendClient
from src.config import Settings
from src.conversation.mood_detector import MoodDetector
from src.conversation.orchestrator import ConversationOrchestrator
from src.conversation.prompt_loader import PromptLoader
from src.conversation.gemini_cli import GeminiCLIClient
from src.spotify.auth import SpotifyTokenManager
from src.spotify.client import SpotifyClient
from src.utils.env import load_env
from src.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI DJ Conversation Runner")
    parser.add_argument(
        "--message",
        action="append",
        dest="messages",
        help="Seed user message to send to Gemini. Can be provided multiple times.",
    )
    parser.add_argument(
        "--prompt",
        dest="prompt_override",
        help="Optional prompt file to override environment configuration.",
    )
    parser.add_argument(
        "--emit-backend",
        action="store_true",
        help="Whether to forward the conversation turn to the backend service.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Python logging level (DEBUG, INFO, WARNING, ...).",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    load_env()

    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    configure_logging(level=log_level)
    settings = Settings.load()

    if args.prompt_override:
        settings = Settings(
            gemini=settings.gemini.__class__(
                model=settings.gemini.model,
                profile=settings.gemini.profile,
                prompt_path=Path(args.prompt_override).resolve(),
                history_path=settings.gemini.history_path,
                temperature=settings.gemini.temperature,
                top_p=settings.gemini.top_p,
            ),
            spotify=settings.spotify,
            backend=settings.backend,
            environment=settings.environment,
        )

    prompt_loader = PromptLoader(settings.gemini.prompt_path)
    try:
        _ = prompt_loader.load()
    except FileNotFoundError as exc:
        logger.error("Unable to load prompt: %s", exc)
        return 1

    gemini_client = GeminiCLIClient(
        model=settings.gemini.model,
        temperature=settings.gemini.temperature,
        top_p=settings.gemini.top_p,
        prompt_path=settings.gemini.prompt_path,
        history_path=settings.gemini.history_path,
        profile_path=settings.gemini.profile,
    )

    token_manager = SpotifyTokenManager(
        client_id=settings.spotify.client_id,
        client_secret=settings.spotify.client_secret,
        refresh_token=settings.spotify.refresh_token,
    )
    spotify_client = SpotifyClient(
        token_manager=token_manager,
        user_id=settings.spotify.user_id,
        recommended_playlist_id=settings.spotify.recommended_playlist_id,
    )

    orchestrator = ConversationOrchestrator(
        gemini_client=gemini_client,
        mood_detector=MoodDetector(),
        spotify_client=spotify_client,
    )

    user_messages = args.messages or ["안녕! 오늘 기분이 어때?"]

    try:
        turns = orchestrator.run_interaction(user_messages)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to run conversation: %s", exc)
        return 1

    if args.emit_backend and settings.backend.recommendation_endpoint:
        backend_client = BackendClient(
            endpoint=settings.backend.recommendation_endpoint,
            api_key=settings.backend.api_key,
        )
        try:
            backend_client.send_turns(turns)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to send data to backend: %s", exc)
            return 1

    print(json.dumps([
        {
            "user_message": turn.user_message,
            "ai_response": turn.ai_response,
            "mood": turn.mood_analysis.mood,
            "confidence": turn.mood_analysis.confidence,
            "rationale": turn.mood_analysis.rationale,
            "recommendations": [
                {
                    "tracks": [track.__dict__ for track in rec.tracks],
                    "mood": rec.mood,
                    "rationale": rec.rationale,
                }
                for rec in turn.recommendations
            ],
        }
        for turn in turns
    ], ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
