"""Lightweight .env loader."""
from __future__ import annotations

import os
from pathlib import Path


def load_env(path: str | None = None) -> None:
    """Load a .env file into the current environment without overriding existing keys."""
    env_path = Path(path or ".env")
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())
