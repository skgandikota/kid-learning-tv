"""Lazy, bounded offline recognition. Audio and transcripts are never persisted."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


class OfflineRecognizer:
    def __init__(self, model_path: Path):
        self.model_path = model_path
        self.model = None
        self.decoder = None
        self.turn = None
        self.samples = 0

    def available(self):
        return (
            importlib.util.find_spec("vosk") is not None
            and (self.model_path / "am" / "final.mdl").is_file()
            and (self.model_path / "conf" / "model.conf").is_file()
        )

    def reset(self):
        self.decoder = None
        self.turn = None
        self.samples = 0

    def accept(self, audio: bytes, turn: str, phrases: list[str]):
        if not self.available():
            raise ValueError("Offline voice is not installed. Run scripts/setup-voice.sh on the laptop.")
        from vosk import KaldiRecognizer, Model, SetLogLevel
        if self.model is None:
            SetLogLevel(-1)
            self.model = Model(str(self.model_path))
        if self.turn != turn or self.decoder is None:
            self.turn = turn
            grammar = list(dict.fromkeys([*phrases, "[unk]"]))
            self.decoder = KaldiRecognizer(self.model, 16000, json.dumps(grammar))
            self.decoder.SetWords(True)
            self.samples = 0
        self.samples += len(audio) // 2
        final = self.decoder.AcceptWaveform(audio)
        if not final and self.samples < 16000 * 18:
            return None
        result = json.loads(self.decoder.Result() if final else self.decoder.FinalResult())
        self.decoder = None
        words = result.get("result", [])
        confidence = min((word.get("conf", 0) for word in words), default=0)
        text = result.get("text", "")
        if not text:
            return {"text": "", "confidence": 0}
        return {"text": text, "confidence": confidence}
