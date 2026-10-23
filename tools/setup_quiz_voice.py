#!/usr/bin/env python3
"""Opt-in target-laptop model installation; runtime never downloads anything.

Run as the service user (with write access to models and KLT_DATA_DIR).
``--verify`` only synthesizes a WAV, accepting basic offline fallback.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

REPO = "rhasspy/piper-voices"
REVISION = "5041a7a49ae5b3a0f30e6837769eb03fdbb231bd"
REMOTE = "en/en_GB/cori/medium"
FILES = ("en_GB-cori-medium.onnx", "en_GB-cori-medium.onnx.json", "MODEL_CARD")
SOURCE = (
    f"Source: https://huggingface.co/{REPO}/tree/{REVISION}/{REMOTE}\n"
    f"Revision: {REVISION}\nVoice: en_GB Cori medium (public domain)\n"
    "Attribution and license details: MODEL_CARD\n"
)


def _complete(directory: Path) -> bool:
    try:
        paths = [directory / name for name in (*FILES, "SOURCE")]
        if directory.is_symlink() or any(p.is_symlink() or not p.is_file() for p in paths):
            return False
        return (
            (directory / FILES[0]).stat().st_size > 1024
            and isinstance(json.loads((directory / FILES[1]).read_text(encoding="utf-8")), dict)
            and bool((directory / "MODEL_CARD").read_text(encoding="utf-8").strip())
            and (directory / "SOURCE").read_text(encoding="utf-8") == SOURCE
        )
    except (OSError, ValueError):
        return False


def install() -> Path:
    models = ROOT / "models"
    destination = models / "piper-cori-medium"
    if models.is_symlink() or destination.is_symlink():
        raise ValueError("Refusing symlinked model installation paths.")
    if _complete(destination):
        return destination
    if destination.exists():
        raise ValueError(f"Incomplete model directory: {destination}. Remove it before retrying.")
    from huggingface_hub import hf_hub_download

    models.mkdir(parents=True, exist_ok=True)
    stage = models / f".piper-cori-medium-stage-{uuid.uuid4().hex}"
    stage.mkdir()
    try:
        for name in FILES:
            downloaded = Path(hf_hub_download(
                repo_id=REPO, revision=REVISION, filename=f"{REMOTE}/{name}",
                local_dir=str(stage / "download"),
            ))
            if downloaded.is_symlink() or not downloaded.is_file():
                raise ValueError(f"Expected a regular downloaded file: {name}")
            shutil.copyfile(downloaded, stage / name)
        shutil.rmtree(stage / "download")
        (stage / "SOURCE").write_text(SOURCE, encoding="utf-8")
        if not _complete(stage):
            raise ValueError("Downloaded voice files failed validation.")
        stage.rename(destination)
        return destination
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def verify(data_dir: Path) -> int:
    from app.quiz_speech import QuizSpeech

    speech = QuizSpeech(data_dir)
    try:
        audio = speech.audio("Hello little learner")
    except RuntimeError as error:
        print(f"No working local speech engine: {error}", file=sys.stderr)
        return 1
    status = speech.status()
    print(f"Quiz voice verified: {status['engine']} ({len(audio)} WAV bytes; no hardware playback).")
    if not status["natural_available"]:
        print(f"WARNING: Using basic offline fallback. {status['error']}", file=sys.stderr)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="Verify only; never download.")
    parser.add_argument("--data-dir", type=Path,
                        default=Path(os.environ.get("KLT_DATA_DIR", ROOT / "var")))
    args = parser.parse_args(argv)
    if not args.verify:
        try:
            print(f"Installed pinned Cori voice: {install()}")
        except Exception as error:
            print(f"Natural voice setup failed: {error}. Offline eSpeak fallback remains usable; "
                  "run --verify to check it.", file=sys.stderr)
            return 1
    return verify(args.data_dir)


if __name__ == "__main__":
    raise SystemExit(main())
