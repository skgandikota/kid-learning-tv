#!/usr/bin/env python3
"""Install fixed neural models once, verify locally, then enable offline voice."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.voice.models import (
    MODELS, WHISPER_NAME, WHISPER_REPO, WHISPER_REVISION, WHISPER_FILES,
    PIPER_NAME, PIPER_REPO, PIPER_REVISION, PIPER_PREFIX, PIPER_FILES, present,
)


def install_model(destination, name, repo, revision, files, prefix=""):
    target = destination / name
    if present(target, files):
        print(f"Already installed: {name}", flush=True)
        return
    if target.exists():
        raise ValueError(f"Incomplete model at {target}. Move it aside and retry.")
    from huggingface_hub import snapshot_download
    destination.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {repo} at {revision} (first setup only)...", flush=True)
    with tempfile.TemporaryDirectory(prefix=".voice-download-", dir=destination) as directory:
        staging = Path(directory)
        paths = [f"{prefix}/{name}" if prefix else name for name in files]
        snapshot = Path(snapshot_download(
            repo_id=repo, revision=revision, allow_patterns=paths,
            local_dir=staging / "download", max_workers=2, token=False,
        ))
        prepared = staging / "ready"
        prepared.mkdir()
        for relative, filename in zip(paths, files):
            source = snapshot / relative
            if not source.is_file() or source.stat().st_size == 0:
                raise ValueError(f"Model download is missing {relative}.")
            shutil.copyfile(source, prepared / filename)
        (prepared / "SOURCE.txt").write_text(f"{repo}\n{revision}\n", encoding="ascii")
        prepared.rename(target)
    print(f"Installed: {target}", flush=True)


def install_models(destination):
    if shutil.disk_usage(destination if destination.exists() else destination.parent).free < 1024**3:
        raise ValueError("Voice setup needs at least 1 GB free disk space for model downloads.")
    install_model(destination, WHISPER_NAME, WHISPER_REPO, WHISPER_REVISION, WHISPER_FILES)
    install_model(destination, PIPER_NAME, PIPER_REPO, PIPER_REVISION, PIPER_FILES, PIPER_PREFIX)


def verify_and_enable(enable):
    import numpy as np
    from app.database import Database
    from app.voice.stt.offline import OfflineRecognizer
    from app.voice.tts import SpeechOutput
    recognizer = OfflineRecognizer(MODELS / WHISPER_NAME)
    recognizer.load()
    recognizer.speech_present(np.zeros(8000, dtype="float32"))
    speech = SpeechOutput()
    if not speech.wave("Hello! Let's play together.", "en-gb", 145, 70).startswith(b"RIFF"):
        raise ValueError("Natural speech verification did not produce WAV audio.")
    if enable:
        db = Database(Path(os.environ.get("KLT_DATA_DIR", ROOT / "var")) / "kid-learning-tv.sqlite3")
        preferences = db.get("preferences", {})
        preferences.update({"voice_enabled": True, "voice_input_enabled": True})
        db.set("preferences", preferences)
    print("Verified local Whisper CPU INT8, speech detection and Piper British English.", flush=True)


def main():
    from huggingface_hub.errors import HfHubHTTPError
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enable", action="store_true", help="Verify installed models and enable local voice.")
    parser.add_argument("--verify", action="store_true", help="Verify models without changing parent preferences.")
    arguments = parser.parse_args()
    try:
        if arguments.enable or arguments.verify:
            verify_and_enable(arguments.enable)
        else:
            install_models(MODELS)
    except (HfHubHTTPError, OSError, RuntimeError, ValueError) as error:
        parser.exit(1, f"Voice setup failed: {error}\nCheck internet access to Hugging Face, free disk space and memory, then retry.\n")


if __name__ == "__main__":
    main()
