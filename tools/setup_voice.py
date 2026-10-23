#!/usr/bin/env python3
"""Install the fixed offline English model, or enable it in local preferences."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import sys
import tempfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
MODEL_NAME = "vosk-model-small-en-us-0.15"
MODEL_URL = f"https://alphacephei.com/vosk/models/{MODEL_NAME}.zip"


def install_model(destination: Path):
    target = destination / MODEL_NAME
    if (target / "am" / "final.mdl").is_file() and (target / "conf" / "model.conf").is_file():
        print(f"Offline English model already installed: {target}")
        return
    if target.exists():
        raise ValueError(f"Incomplete model exists at {target}. Move it aside before retrying.")
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".voice-download-", dir=destination) as directory:
        staging = Path(directory)
        archive = staging / "model.zip"
        print(f"Downloading the approximately 40 MB English model from {MODEL_URL}", flush=True)
        with urllib.request.urlopen(MODEL_URL, timeout=60) as response, archive.open("wb") as output:
            total = 0
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if total > 100 * 1024 * 1024:
                    raise ValueError("Speech model download exceeded its size limit.")
                output.write(chunk)
                print(f"\rDownloaded {total // (1024 * 1024)} MB", end="", flush=True)
        print()
        with zipfile.ZipFile(archive) as bundle:
            if sum(member.file_size for member in bundle.infolist()) > 250 * 1024 * 1024:
                raise ValueError("Expanded speech model exceeded its size limit.")
            for member in bundle.infolist():
                relative = Path(member.filename)
                resolved = (staging / relative).resolve()
                if (
                    not member.filename.startswith(MODEL_NAME + "/")
                    or "\\" in member.filename
                    or not resolved.is_relative_to(staging.resolve())
                    or member.external_attr >> 16 & 0o170000 == 0o120000
                ):
                    raise ValueError("Unsafe speech model archive path.")
            bundle.extractall(staging)
        model = staging / MODEL_NAME
        for required in ("am/final.mdl", "conf/model.conf"):
            if not (model / required).is_file():
                raise ValueError(f"Speech model is missing {required}.")
        shutil.move(str(model), target)
    print(f"Installed offline English model: {target}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enable", action="store_true", help="Enable installed offline voice in the local database.")
    arguments = parser.parse_args()
    if arguments.enable:
        from app.database import Database
        from app.voice.stt.offline import OfflineRecognizer
        recognizer = OfflineRecognizer(ROOT / "models" / MODEL_NAME)
        if not recognizer.available():
            raise ValueError("Install vosk and the English model before enabling voice.")
        recognizer.accept(bytes(320), "setup-check", ["avocado"])
        recognizer.reset()
        db = Database(Path(os.environ.get("KLT_DATA_DIR", ROOT / "var")) / "kid-learning-tv.sqlite3")
        preferences = db.get("preferences", {})
        preferences.update({"voice_enabled": True, "voice_input_enabled": True})
        db.set("preferences", preferences)
        print("Offline voice enabled. Open the laptop TV page and allow its microphone.")
    else:
        install_model(ROOT / "models")


if __name__ == "__main__":
    main()
