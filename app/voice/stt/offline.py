"""Bounded in-memory utterances, neural VAD and CPU INT8 Whisper recognition."""
from __future__ import annotations

import importlib.util
import math
import threading
from pathlib import Path

from app.voice.models import WHISPER_FILES, present


class OfflineRecognizer:
    def __init__(self, model_path: Path):
        self.model_path = model_path
        self.model = None
        self.lock = threading.Lock()
        self.reset()

    def available(self):
        return importlib.util.find_spec("faster_whisper") is not None and present(self.model_path, WHISPER_FILES)

    def reset(self):
        self.turn = None
        self.audio = bytearray()
        self.preroll = b""
        self.silence_samples = 0

    def load(self):
        if not self.available():
            raise ValueError("Neural voice is not installed. Run scripts/setup-voice.sh on the laptop.")
        if self.model is None:
            from faster_whisper import WhisperModel
            self.model = WhisperModel(
                str(self.model_path), device="cpu", compute_type="int8",
                cpu_threads=2, num_workers=1, local_files_only=True,
            )

    def speech_present(self, samples):
        from faster_whisper.vad import VadOptions, get_speech_timestamps
        return bool(get_speech_timestamps(samples, VadOptions(
            threshold=0.35, min_speech_duration_ms=80,
            min_silence_duration_ms=100, speech_pad_ms=30,
        )))

    def accept(self, audio: bytes, turn: str, phrases: list[str]):
        self.load()
        import numpy as np
        if self.turn != turn:
            self.reset()
            self.turn = turn
        samples = np.frombuffer(audio, dtype="<i2").astype(np.float32) / 32768.0
        speech = self.speech_present(samples)
        if not self.audio and not speech:
            self.preroll = audio[-16000:]
            return None
        if not self.audio:
            self.audio.extend(self.preroll)
            self.preroll = b""
        self.audio.extend(audio[:18 * 32000 - len(self.audio)])
        self.silence_samples = 0 if speech else self.silence_samples + len(samples)
        if len(self.audio) < 18 * 32000 and self.silence_samples < 16000 * 1.25:
            return None
        utterance = np.frombuffer(bytes(self.audio), dtype="<i2").astype(np.float32) / 32768.0
        self.audio.clear()
        self.silence_samples = 0
        # Hints are vocabulary, not an answer or a constrained forced-choice grammar.
        hint = ", ".join(dict.fromkeys(phrases))[:500]
        segments, _ = self.model.transcribe(
            utterance, language="en", beam_size=3, condition_on_previous_text=False,
            initial_prompt=f"English children's game vocabulary: {hint}.",
            word_timestamps=True, vad_filter=True,
            vad_parameters={"threshold": 0.35, "min_silence_duration_ms": 700},
        )
        segments = list(segments)
        usable = [
            segment for segment in segments
            if segment.no_speech_prob < 0.6 and segment.avg_logprob > -1.0
            and segment.compression_ratio < 2.4
        ]
        text = " ".join(segment.text.strip() for segment in usable).strip()
        words = [word.probability for segment in usable for word in (segment.words or [])]
        confidence = sum(words) / len(words) if words else 0.0
        if not math.isfinite(confidence):
            confidence = 0.0
        return {"text": text, "confidence": confidence}
