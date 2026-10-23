import io
from pathlib import Path
import shutil
import subprocess
import sys
from types import ModuleType, SimpleNamespace
import uuid
import wave

import pytest

from app import quiz_speech
from tools import setup_quiz_voice


@pytest.fixture
def directory():
    root = Path.cwd() / f".quiz-speech-test-{uuid.uuid4().hex}"
    root.mkdir()
    yield root
    shutil.rmtree(root)


def wav_bytes():
    output = io.BytesIO()
    with wave.open(output, "wb") as sound:
        sound.setnchannels(1)
        sound.setsampwidth(2)
        sound.setframerate(22050)
        sound.writeframes(b"\x01\x00" * 2205)
    return output.getvalue()


@pytest.fixture
def engines(monkeypatch, directory):
    model = directory / "model"
    model.mkdir()
    monkeypatch.setattr(quiz_speech, "MODEL_DIR", model)
    monkeypatch.setattr(quiz_speech.shutil, "which", lambda _: "espeak-ng")
    calls = []

    def run(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(stdout=wav_bytes())

    monkeypatch.setattr(quiz_speech.subprocess, "run", run)
    return model, calls


def piper(monkeypatch, model, failure=None):
    (model / quiz_speech.MODEL_NAME).write_bytes(b"model")
    (model / f"{quiz_speech.MODEL_NAME}.json").write_text("{}")
    calls = []

    class Voice:
        @classmethod
        def load(cls, path, **kwargs):
            calls.append(("load", path, kwargs))
            if failure == "load":
                raise OSError("model damaged")
            return cls()

        def synthesize_wav(self, text, sound, *, syn_config):
            calls.append(("synthesize", text, syn_config))
            if failure == "infer":
                raise RuntimeError("inference failed")
            sound.setnchannels(1)
            sound.setsampwidth(2)
            sound.setframerate(22050)
            sound.writeframes(b"\x01\x00" * 2205)

    module = ModuleType("piper")
    module.PiperVoice = Voice
    config = ModuleType("piper.config")
    config.SynthesisConfig = lambda **kw: kw
    monkeypatch.setitem(sys.modules, "piper", module)
    monkeypatch.setitem(sys.modules, "piper.config", config)
    monkeypatch.setattr(quiz_speech.importlib.util, "find_spec", lambda _: object())
    return calls


def test_piper_is_lazy_cpu_and_cached(monkeypatch, directory, engines):
    model, fallback = engines
    calls = piper(monkeypatch, model)
    speech = quiz_speech.QuizSpeech(directory)
    assert speech.status() == {
        "engine": "piper", "available": True, "natural_available": True, "error": None,
    }
    assert not calls
    assert quiz_speech._valid_wav(speech.audio("Apple"))
    assert speech.audio("Apple") == wav_bytes()
    assert calls[0][2] == {"use_cuda": False}
    assert calls[1] == ("synthesize", "Apple", {"volume": .7, "length_scale": 1.0})
    assert len(calls) == 2
    assert not fallback


@pytest.mark.parametrize("failure", ["load", "infer"])
def test_neural_failure_falls_back_and_keeps_reason(monkeypatch, directory, engines, failure):
    model, calls = engines
    piper(monkeypatch, model, failure)
    speech = quiz_speech.QuizSpeech(directory)
    assert quiz_speech._valid_wav(speech.audio("Banana"))
    state = speech.status()
    assert state["engine"] == "espeak-ng" and not state["natural_available"]
    assert "Natural voice failed" in state["error"]
    assert calls[0] == (
        ["espeak-ng", "--stdout", "-v", "en-gb", "-s", "135", "-a", "70", "Banana"],
        {"capture_output": True, "check": True, "timeout": 10},
    )
    speech.audio("Banana")
    assert speech.status()["error"] == state["error"]
    assert len(calls) == 1


def test_missing_engines_are_explicit(monkeypatch, directory, engines):
    monkeypatch.setattr(quiz_speech.shutil, "which", lambda _: None)
    speech = quiz_speech.QuizSpeech(directory)
    with pytest.raises(RuntimeError, match="no local speech engine"):
        speech.audio("Apple")
    assert not speech.status()["available"]
    assert speech.status()["engine"] == "none"


def test_optional_import_failure_falls_back(monkeypatch, directory, engines):
    model, calls = engines
    piper(monkeypatch, model)
    monkeypatch.setitem(sys.modules, "piper", None)
    speech = quiz_speech.QuizSpeech(directory)
    speech.audio("Apple")
    assert "ModuleNotFoundError" in speech.status()["error"]
    assert calls


def test_cached_neural_audio_does_not_hide_load_failure(monkeypatch, directory, engines):
    model, calls = engines
    piper(monkeypatch, model)
    quiz_speech.QuizSpeech(directory).audio("Apple")
    piper(monkeypatch, model, "load")
    speech = quiz_speech.QuizSpeech(directory)
    speech.audio("Apple")
    assert speech.status()["engine"] == "espeak-ng"
    assert "model damaged" in speech.status()["error"]
    assert len(calls) == 1


def test_espeak_timeout_is_not_cached(monkeypatch, directory, engines):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("espeak-ng", 10)

    monkeypatch.setattr(quiz_speech.subprocess, "run", timeout)
    speech = quiz_speech.QuizSpeech(directory)
    with pytest.raises(RuntimeError, match="TimeoutExpired"):
        speech.audio("Apple")
    assert not speech.status()["available"]
    assert not list(directory.glob("quiz-audio/*.wav"))


@pytest.mark.parametrize("text", ["", "   ", "x" * 121, "../Apple", "Apple\n", None])
def test_invalid_catalog_input_never_synthesizes(directory, engines, text):
    speech = quiz_speech.QuizSpeech(directory)
    with pytest.raises(ValueError):
        speech.audio(text)
    assert not engines[1]


def test_cache_filenames_are_hashed_and_corruption_is_replaced(directory, engines):
    speech = quiz_speech.QuizSpeech(directory)
    speech.audio("Child's apple")
    files = list((directory / "quiz-audio").iterdir())
    assert len(files) == 1 and len(files[0].stem) == 64
    files[0].write_bytes(b"RIFF" + b"\0" * 40)
    assert quiz_speech._valid_wav(speech.audio("Child's apple"))
    assert len(engines[1]) == 2


@pytest.mark.parametrize("data", [b"", b"RIFF\0\0\0\0WAVE", wav_bytes()[:45]])
def test_invalid_audio_is_not_cached(monkeypatch, directory, engines, data):
    monkeypatch.setattr(quiz_speech.subprocess, "run", lambda *a, **kw: SimpleNamespace(stdout=data))
    speech = quiz_speech.QuizSpeech(directory)
    with pytest.raises(RuntimeError, match="invalid or empty WAV"):
        speech.audio("Apple")
    assert not list(directory.glob("quiz-audio/*.wav"))


def test_setup_pins_download_and_is_atomic_idempotent(monkeypatch, directory):
    monkeypatch.setattr(setup_quiz_voice, "ROOT", directory)
    calls = []

    def download(**kwargs):
        calls.append(kwargs)
        assert not (directory / "models" / "piper-cori-medium").exists()
        name = Path(kwargs["filename"]).name
        path = Path(kwargs["local_dir"]) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x" * 2048 if name.endswith(".onnx") else
                         b"{}" if name.endswith(".json") else b"Public domain")
        return str(path)

    module = ModuleType("huggingface_hub")
    module.hf_hub_download = download
    monkeypatch.setitem(sys.modules, "huggingface_hub", module)
    installed = setup_quiz_voice.install()
    assert setup_quiz_voice._complete(installed)
    assert len(calls) == 3
    assert all(c["revision"] == setup_quiz_voice.REVISION for c in calls)
    assert setup_quiz_voice.install() == installed
    assert len(calls) == 3
    assert not list(installed.parent.glob(".piper*"))


def test_setup_failure_cleans_staging(monkeypatch, directory):
    monkeypatch.setattr(setup_quiz_voice, "ROOT", directory)
    module = ModuleType("huggingface_hub")

    def fail(**kwargs):
        raise OSError("offline")

    module.hf_hub_download = fail
    monkeypatch.setitem(sys.modules, "huggingface_hub", module)
    assert setup_quiz_voice.main(["--data-dir", str(directory)]) == 1
    assert not list((directory / "models").iterdir())


def test_verify_accepts_fallback_without_downloading(monkeypatch, directory, engines, capsys):
    monkeypatch.setattr(setup_quiz_voice, "install", lambda: pytest.fail("unexpected download"))
    assert setup_quiz_voice.main(["--verify", "--data-dir", str(directory)]) == 0
    assert "WARNING: Using basic offline fallback" in capsys.readouterr().err


def test_verify_fails_without_working_engine(monkeypatch, directory, engines, capsys):
    monkeypatch.setattr(quiz_speech.shutil, "which", lambda _: None)
    assert setup_quiz_voice.main(["--verify", "--data-dir", str(directory)]) == 1
    assert "No working local speech engine" in capsys.readouterr().err
