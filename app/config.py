"""Runtime configuration loaded from environment and local JSON settings."""
from __future__ import annotations

import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load_settings() -> dict:
    defaults = json.loads((ROOT / "config" / "default.json").read_text(encoding="utf-8"))
    custom = os.getenv("KLT_CONFIG")
    if custom:
        candidate = Path(custom)
        if not candidate.is_absolute():
            candidate = ROOT / candidate
        if candidate.is_file():
            defaults.update(json.loads(candidate.read_text(encoding="utf-8")))
    return defaults


SETTINGS = load_settings()
DATA_DIR = Path(os.getenv("KLT_DATA_DIR", str(ROOT / "var"))).expanduser()
CONTENT_DIR = Path(os.getenv("KLT_CONTENT_DIR", str(ROOT / "content"))).expanduser()
HOST = os.getenv("KLT_HOST", str(SETTINGS.get("host", "127.0.0.1")))
PORT = int(os.getenv("KLT_PORT", SETTINGS.get("port", 8765)))
SECURE_COOKIE = os.getenv("KLT_SECURE_COOKIE", "0").lower() in {"1", "true", "yes"}
