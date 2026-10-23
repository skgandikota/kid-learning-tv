"""Bounded local phoneme synthesis; never substitute spoken letter names."""
from __future__ import annotations

import hashlib
import io
import logging
from pathlib import Path
import shutil
import subprocess
import threading
import uuid
import wave

from app.quiz_speech import _valid_wav
from app.typing_game import get_lesson, sound_step


def audible_wav(data):
    if not _valid_wav(data):
        return False
    with wave.open(io.BytesIO(data), "rb") as sound:
        return any(sound.readframes(len(data)))


class PhonicsSpeech:
    def __init__(self, data_dir):
        self.cache = Path(data_dir) / "phonics-audio"
        self.executable = shutil.which("espeak-ng")
        self.lock = threading.Lock()

    def audio(self, item_id, position, kind):
        item = get_lesson(item_id)
        if kind == "spell" and position == 0:
            text = f"{item['name']}. Let's type. " + ", ".join(item["word"].replace(" ", "")) + "."
        else:
            step = sound_step(item, position)
            phonemes = step.get(kind) if step and kind in {"sound", "blend"} else None
            if not phonemes:
                raise ValueError("This letter group has no sound yet.")
            # Voiced stops need a brief release; the bare eSpeak symbols are silent.
            if kind == "sound":
                phonemes = {"b": "b@-", "d": "d@-", "g": "g@-", "dZ": "dZ@-"}.get(phonemes, phonemes)
            text = f"[[{phonemes}]]"
        key = hashlib.sha256(f"en-gb-phonics-v1:110:70:{text}".encode()).hexdigest()
        with self.lock:
            path = self.cache / f"{key}.wav"
            if path.is_file() and not path.is_symlink():
                data = path.read_bytes()
                if audible_wav(data):
                    return data
            if not self.executable:
                raise RuntimeError("Phonics needs eSpeak NG. Run the update on the laptop; sounds cannot be replaced with letter names.")
            try:
                result = subprocess.run(
                    [self.executable, "--stdout", "-v", "en-gb", "-s", "110", "-a", "70", text],
                    capture_output=True, check=True, timeout=10,
                )
            except (OSError, subprocess.SubprocessError) as error:
                raise RuntimeError(f"Phonics sound failed: {error}") from error
            if not audible_wav(result.stdout):
                raise RuntimeError("Phonics engine returned empty or invalid sound, or silent audio.")
            self.cache.mkdir(parents=True, exist_ok=True)
            staging = self.cache / f".{key}-{uuid.uuid4().hex}.part"
            try:
                staging.write_bytes(result.stdout)
                staging.replace(path)
            except OSError:
                logging.getLogger(__name__).exception("Could not save phonics audio.")
                raise
            finally:
                staging.unlink(missing_ok=True)
            return result.stdout
