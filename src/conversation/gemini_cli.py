"""Wrapper around the Gemini CLI to maintain conversations."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Iterable, List, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


class GeminiCLIError(RuntimeError):
    """Raised when the Gemini CLI fails."""


class GeminiCLIClient:
    """Interact with the Gemini CLI using subprocess calls."""

    def __init__(
        self,
        model: str,
        temperature: float,
        top_p: float,
        prompt_path: Path,
        history_path: Path,
        profile_path: Optional[Path] = None,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.prompt_path = prompt_path
        self.history_path = history_path
        self.profile_path = profile_path

    def _base_command(self) -> List[str]:
        cmd = [
            "gemini",
            "pro",
            "chat",
            "--model",
            self.model,
            "--temperature",
            str(self.temperature),
            "--top-p",
            str(self.top_p),
            "--prompt",
            str(self.prompt_path),
        ]
        if self.profile_path:
            cmd.extend(["--profile", str(self.profile_path)])
        if self.history_path.exists():
            cmd.extend(["--history", str(self.history_path)])
        return cmd

    def start(self) -> None:
        """Initialise the chat session and persist history."""
        logger.info("Starting Gemini CLI session with model %s", self.model)
        command = self._base_command() + ["--output", str(self.history_path)]
        self._run_cli(command, input_text=None)

    def send_messages(self, messages: Iterable[str]) -> str:
        """Send a sequence of messages and return the latest response."""
        response = ""
        for message in messages:
            logger.debug("Sending message to Gemini CLI: %s", message)
            command = self._base_command() + ["--message", message]
            response = self._run_cli(command, input_text=None)
        return response

    def ask(self, message: str) -> str:
        """Send a single message and return the response."""
        return self.send_messages([message])

    def _run_cli(self, command: List[str], input_text: Optional[str]) -> str:
        logger.debug("Executing command: %s", " ".join(command))
        try:
            completed = subprocess.run(
                command,
                input=input_text.encode("utf-8") if input_text else None,
                capture_output=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise GeminiCLIError(
                "Gemini CLI binary not found. Please ensure it is installed and on PATH."
            ) from exc

        if completed.returncode != 0:
            logger.error(
                "Gemini CLI failed with code %s: %s",
                completed.returncode,
                completed.stderr.decode("utf-8", errors="ignore"),
            )
            raise GeminiCLIError("Gemini CLI execution failed")

        raw_output = completed.stdout.decode("utf-8", errors="ignore").strip()
        logger.debug("Gemini raw output: %s", raw_output)
        self._persist_history(raw_output)
        return raw_output

    def _persist_history(self, raw_output: str) -> None:
        """Persist conversation snippets for stateful sessions."""
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            history = json.loads(self.history_path.read_text()) if self.history_path.exists() else []
        except json.JSONDecodeError:
            history = []
        history.append(raw_output)
        self.history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2))


