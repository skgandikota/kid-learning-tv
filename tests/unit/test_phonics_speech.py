import io
import subprocess
from types import SimpleNamespace
import wave

import pytest

from app import phonics_speech


def wav_bytes():
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as sound:
        sound.setnchannels(1)
        sound.setsampwidth(2)
        sound.setframerate(22050)
        sound.writeframes(b"\x01\x00" * 2205)
    return buffer.getvalue()


def test_uses_explicit_phonemes_not_letter_names_and_caches(monkeypatch, tmp_path):
    monkeypatch.setattr(phonics_speech.shutil, "which", lambda _: "espeak-ng")
    calls = []
    def run(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(stdout=wav_bytes())
    monkeypatch.setattr(phonics_speech.subprocess, "run", run)
    speech = phonics_speech.PhonicsSpeech(tmp_path)
    assert speech.audio("flash", 1, "sound") == wav_bytes()
    assert speech.audio("flash", 1, "sound") == wav_bytes()
    assert calls[0][0][-1] == "[[f]]"
    assert calls[0][1]["timeout"] == 10
    assert len(calls) == 1
    speech.audio("flash", 2, "blend")
    assert calls[-1][0][-1] == "[[fl]]"
    speech.audio("flash", 5, "sound")
    assert calls[-1][0][-1] == "[[S]]"
    with pytest.raises(ValueError):
        speech.audio("flash", 4, "sound")


def test_no_engine_or_bad_synthesis_is_explicit(monkeypatch, tmp_path):
    monkeypatch.setattr(phonics_speech.shutil, "which", lambda _: None)
    with pytest.raises(RuntimeError, match="needs eSpeak"):
        phonics_speech.PhonicsSpeech(tmp_path).audio("flash", 1, "sound")
    monkeypatch.setattr(phonics_speech.shutil, "which", lambda _: "espeak-ng")
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("espeak-ng", 10)
    monkeypatch.setattr(phonics_speech.subprocess, "run", timeout)
    with pytest.raises(RuntimeError, match="sound failed"):
        phonics_speech.PhonicsSpeech(tmp_path).audio("flash", 1, "sound")
    monkeypatch.setattr(phonics_speech.subprocess, "run", lambda *a, **k: SimpleNamespace(stdout=b""))
    with pytest.raises(RuntimeError, match="empty or invalid"):
        phonics_speech.PhonicsSpeech(tmp_path).audio("flash", 1, "sound")


def test_only_curated_sounds_and_spelling_allowed(monkeypatch, tmp_path):
    monkeypatch.setattr(phonics_speech.shutil, "which", lambda _: "espeak-ng")
    calls = []
    def run(args, **kwargs):
        calls.append(args)
        return SimpleNamespace(stdout=wav_bytes())
    monkeypatch.setattr(phonics_speech.subprocess, "run", run)
    speech = phonics_speech.PhonicsSpeech(tmp_path)
    for item_id, position, kind in [("unknown", 1, "sound"), ("flash", 99, "sound"), ("flash", 0, "[[xxx]]")]:
        with pytest.raises(ValueError):
            speech.audio(item_id, position, kind)
    assert not calls
    speech.audio("flash", 0, "spell")
    assert calls[0][-1] == "Flash. Let's type. F, L, A, S, H."


@pytest.mark.parametrize("item_id,position,prompt", [
    ("batman", 1, "[[b@-]]"), ("dog", 1, "[[d@-]]"),
    ("dog", 3, "[[g@-]]"), ("joker", 1, "[[dZ@-]]"),
])
def test_voiced_stops_have_audible_release_prompt(monkeypatch, tmp_path, item_id, position, prompt):
    monkeypatch.setattr(phonics_speech.shutil, "which", lambda _: "espeak-ng")
    calls = []
    def run(args, **kwargs):
        calls.append(args)
        return SimpleNamespace(stdout=wav_bytes())
    monkeypatch.setattr(phonics_speech.subprocess, "run", run)
    phonics_speech.PhonicsSpeech(tmp_path).audio(item_id, position, "sound")
    assert calls[0][-1] == prompt


def test_rejects_well_formed_but_silent_audio(monkeypatch, tmp_path):
    monkeypatch.setattr(phonics_speech.shutil, "which", lambda _: "espeak-ng")
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as sound:
        sound.setnchannels(1)
        sound.setsampwidth(2)
        sound.setframerate(22050)
        sound.writeframes(b"\0\0" * 2205)
    monkeypatch.setattr(phonics_speech.subprocess, "run", lambda *a, **k: SimpleNamespace(stdout=buffer.getvalue()))
    with pytest.raises(RuntimeError, match="silent audio"):
        phonics_speech.PhonicsSpeech(tmp_path).audio("flash", 1, "sound")
