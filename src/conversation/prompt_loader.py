"""Prompt management utilities."""
from __future__ import annotations

from pathlib import Path
from typing import List


class PromptLoader:
    """Utility class for loading prompt templates."""

    def __init__(self, prompt_path: Path):
        self._prompt_path = prompt_path

    def load(self) -> str:
        """Load the base prompt text."""
        if not self._prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {self._prompt_path}")
        return self._prompt_path.read_text(encoding="utf-8")

    def load_examples(self) -> List[str]:
        """Load few-shot examples if present in sibling directory."""
        examples_dir = self._prompt_path.parent / "examples"
        if not examples_dir.exists():
            return []
        return [
            path.read_text(encoding="utf-8")
            for path in sorted(examples_dir.glob("*.txt"))
        ]
