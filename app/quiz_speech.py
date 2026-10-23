"""Local WAV synthesis for catalog answers, never audio-device playback.

Call ``audio`` outside the playback/runtime lock. Only pass trusted catalog
labels, not arbitrary HTTP input. ``status`` never loads a neural model.
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import logging
from contextlib import suppress
from pathlib import Path
import shutil
import subprocess
import threading
import uuid
import wave

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "models" / "piper-cori-medium"
MODEL_NAME = "en_GB-cori-medium.onnx"
LOGGER = logging.getLogger(__name__)
_SYNTHESIS_ERRORS = (ImportError, OSError, RuntimeError, ValueError, wave.Error, EOFError)


def _valid_wav(data: bytes) -> bool:
    if not isinstance(data, bytes) or not 44 <= len(data) <= 8 * 1024 * 1024:
        return False
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        return False
    try:
        with wave.open(io.BytesIO(data), "rb") as sound:
            channels, width, rate = (
                sound.getnchannels(), sound.getsampwidth(), sound.getframerate()
            )
            if (sound.getcomptype() != "NONE" or channels not in (1, 2)
                    or width not in (1, 2, 3, 4) or not 8000 <= rate <= 96000):
                return False
            # eSpeak stdout uses streaming (oversized) RIFF frame counts.
            frames = sound.readframes(min(sound.getnframes(), len(data)))
            return (len(frames) >= int(rate * .04) * channels * width
                    and len(frames) % (channels * width) == 0)
    except (EOFError, OSError, ValueError, wave.Error):
        return False


class QuizSpeech:
    """Lazy, serialized synthesis; failures raise RuntimeError with status detail."""

    def __init__(self, data_dir: Path):
        self._cache = Path(data_dir) / "quiz-audio"
        self._lock = threading.Lock()
        self._voice = None
        self._config = None
        self._espeak = shutil.which("espeak-ng")
        self._natural = False
        self._error = None
        model = MODEL_DIR / MODEL_NAME
        if not model.is_file() or not model.with_suffix(".onnx.json").is_file():
            self._error = "Natural voice unavailable: Cori model files are not installed."
        else:
            try:
                self._natural = importlib.util.find_spec("piper") is not None
            except (ImportError, ValueError):
                self._natural = False
            if not self._natural:
                self._error = "Natural voice unavailable: optional piper-tts package is not installed."
        self._engine = "piper" if self._natural else ("espeak-ng" if self._espeak else "none")
        self._available = self._engine != "none"
        if not self._available:
            self._error += " eSpeak NG is not installed; no local speech engine is available."

    def status(self) -> dict:
        """Return discovery/last synthesis state, without initializing Piper."""
        with self._lock:
            return {
                "engine": self._engine,
                "available": self._available,
                "natural_available": self._natural,
                "error": self._error,
            }

    @staticmethod
    def _text(text: str) -> str:
        if (not isinstance(text, str) or not text or len(text) > 120
                or not text.strip()
                or any(not (c.isalnum() or c in " '-’") for c in text)):
            raise ValueError("Speech requires a nonblank catalog label of at most 120 characters.")
        return " ".join(text.split())

    def _cached_or_synthesize(self, text: str) -> bytes:
        key = hashlib.sha256(f"{self._engine}:cori-v1:135:70:{text}".encode()).hexdigest()
        path = self._cache / f"{key}.wav"
        try:
            if not path.is_symlink():
                cached = path.read_bytes()
                if _valid_wav(cached):
                    return cached
        except OSError:
            pass
        if self._engine == "piper":
            buffer = io.BytesIO()
            sound = wave.open(buffer, "wb")
            try:
                self._voice.synthesize_wav(text, sound, syn_config=self._config)
            except BaseException:
                # A failed inference may leave an unwritable WAV header.
                with suppress(wave.Error):
                    sound.close()
                raise
            sound.close()
            data = buffer.getvalue()
        else:
            result = subprocess.run(
                [self._espeak, "--stdout", "-v", "en-gb", "-s", "135", "-a", "70", text],
                capture_output=True, check=True, timeout=10,
            )
            data = result.stdout
        if not _valid_wav(data):
            raise ValueError(f"{self._engine} returned invalid or empty WAV audio.")
        staging = self._cache / f".{key}-{uuid.uuid4().hex}.part"
        try:
            self._cache.mkdir(parents=True, exist_ok=True)
            staging.write_bytes(data)
            staging.replace(path)
        except OSError:
            LOGGER.warning("Could not persist quiz speech cache.", exc_info=True)
        finally:
            with suppress(OSError):
                staging.unlink(missing_ok=True)
        return data

    def audio(self, text: str) -> bytes:
        """Return validated WAV bytes; no network, microphones, or audio hardware."""
        text = self._text(text)
        with self._lock:
            if self._natural:
                try:
                    if self._voice is None:
                        from piper import PiperVoice
                        from piper.config import SynthesisConfig

                        self._voice = PiperVoice.load(str(MODEL_DIR / MODEL_NAME), use_cuda=False)
                        self._config = SynthesisConfig(volume=.7, length_scale=1.0)
                    return self._cached_or_synthesize(text)
                except _SYNTHESIS_ERRORS as error:
                    self._error = f"Natural voice failed ({type(error).__name__}): {error}"
                    LOGGER.warning("%s; trying eSpeak NG.", self._error)
                    self._natural = False
                    self._voice = None
                    self._engine = "espeak-ng" if self._espeak else "none"
            if self._engine == "espeak-ng":
                try:
                    data = self._cached_or_synthesize(text)
                    self._available = True
                    return data
                except (*_SYNTHESIS_ERRORS, subprocess.SubprocessError) as error:
                    self._error = (
                        f"{self._error + ' ' if self._error else ''}"
                        f"eSpeak NG failed ({type(error).__name__}): {error}"
                    )
                    LOGGER.warning("%s", self._error)
            self._available = False
            if not self._espeak and "no local speech engine" not in (self._error or ""):
                self._error = f"{self._error or ''} eSpeak NG is not installed; no local speech engine is available."
            raise RuntimeError(self._error or "No local speech engine is available.")
