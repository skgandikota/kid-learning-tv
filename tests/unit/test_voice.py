import pytest
import io
import sys
import wave
from types import SimpleNamespace
from unittest.mock import Mock

from app.voice.commands import memory_items
from app.voice.stt.offline import OfflineRecognizer
from app.voice.tts import SpeechOutput
from tools.setup_voice import install_model, verify_and_enable


def test_spoken_memory_list_preserves_order_and_repeats_for_game_validation():
    assert memory_items("I went to the shop and bought an apple and bread and apple", ["bread", "apple"]) == ["apple", "bread", "apple"]
    assert memory_items("fire engine and car", ["fire", "fire engine", "car"]) == ["fire engine", "car"]
    with pytest.raises(ValueError):
        memory_items("apple and spaceship", ["apple", "bread"])


def test_missing_model_is_explicit_and_never_downloaded_at_runtime(tmp_path):
    recognizer = OfflineRecognizer(tmp_path / "missing")
    assert recognizer.available() is False
    with pytest.raises(ValueError, match="setup-voice"):
        recognizer.accept(bytes(100), "turn", ["avocado"])
    assert list(tmp_path.iterdir()) == []


def test_model_setup_is_repeatable_without_redownloading(tmp_path, monkeypatch):
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    (snapshot / "model.bin").write_bytes(b"model")
    download = Mock(return_value=str(snapshot))
    monkeypatch.setitem(sys.modules, "huggingface_hub", SimpleNamespace(snapshot_download=download))
    install_model(tmp_path, "test-model", "owner/repo", "fixed-revision", ["model.bin"])
    assert (tmp_path / "test-model" / "model.bin").read_bytes() == b"model"
    install_model(tmp_path, "test-model", "owner/repo", "fixed-revision", ["model.bin"])
    assert download.call_count == 1
    assert download.call_args.kwargs["revision"] == "fixed-revision"


def test_failed_download_is_not_published_as_an_installed_model(tmp_path, monkeypatch):
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    monkeypatch.setitem(sys.modules, "huggingface_hub", SimpleNamespace(snapshot_download=Mock(return_value=str(snapshot))))
    with pytest.raises(ValueError, match="missing"):
        install_model(tmp_path, "test-model", "owner/repo", "fixed-revision", ["model.bin"])
    assert not (tmp_path / "test-model").exists()
    assert not list(tmp_path.glob(".voice-download-*"))


def test_incomplete_existing_model_is_not_silently_reused(tmp_path):
    (tmp_path / "test-model").mkdir()
    with pytest.raises(ValueError, match="Incomplete"):
        install_model(tmp_path, "test-model", "owner/repo", "fixed-revision", ["model.bin"])


def test_verification_preserves_parent_voice_settings_and_only_enable_changes_them(tmp_path, monkeypatch):
    pytest.importorskip("numpy")
    from app.database import Database
    monkeypatch.setenv("KLT_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(OfflineRecognizer, "load", Mock())
    monkeypatch.setattr(OfflineRecognizer, "speech_present", Mock(return_value=False))
    monkeypatch.setattr(SpeechOutput, "wave", Mock(return_value=b"RIFFtest"))
    database = Database(tmp_path / "kid-learning-tv.sqlite3")
    preferences = {"voice_enabled": False, "voice_input_enabled": False, "volume": 40}
    database.set("preferences", preferences)
    verify_and_enable(False)
    assert database.get("preferences") == preferences
    verify_and_enable(True)
    assert database.get("preferences") == {**preferences, "voice_enabled": True, "voice_input_enabled": True}


def decoder(tmp_path):
    pytest.importorskip("numpy")
    recognizer = OfflineRecognizer(tmp_path)
    recognizer.load = Mock()
    recognizer.speech_present = Mock(return_value=False)
    word = SimpleNamespace(probability=.9)
    segment = SimpleNamespace(text=" elephant ", words=[word], no_speech_prob=.01,
                              avg_logprob=-.2, compression_ratio=1.1)
    recognizer.model = Mock()
    recognizer.model.transcribe.return_value = (iter([segment]), None)
    return recognizer


def test_whisper_ignores_silence_and_decodes_only_after_a_spoken_utterance(tmp_path):
    recognizer = decoder(tmp_path)
    chunk = bytes(16000)
    for _ in range(100):
        assert recognizer.accept(chunk, "turn", ["elephant"]) is None
    assert not recognizer.audio
    assert len(recognizer.preroll) == 16000
    recognizer.model.transcribe.assert_not_called()
    recognizer.speech_present.return_value = True
    recognizer.accept(chunk, "turn", ["elephant"])
    recognizer.speech_present.return_value = False
    assert recognizer.accept(chunk, "turn", ["elephant"]) is None
    assert recognizer.accept(chunk, "turn", ["elephant"]) is None
    result = recognizer.accept(chunk, "turn", ["elephant"])
    assert result == {"text": "elephant", "confidence": .9}
    assert not recognizer.audio
    assert recognizer.model.transcribe.call_args.kwargs["condition_on_previous_text"] is False


def test_whisper_turn_change_discards_old_audio_and_utterance_has_a_hard_limit(tmp_path):
    recognizer = decoder(tmp_path)
    recognizer.speech_present.return_value = True
    recognizer.accept(bytes(16000), "old", ["apple"])
    recognizer.speech_present.return_value = False
    recognizer.accept(bytes(16000), "new", ["elephant"])
    assert not recognizer.audio
    recognizer.speech_present.return_value = True
    results = []
    for _ in range(36):
        result = recognizer.accept(bytes(16000), "new", ["elephant"])
        if result is not None:
            results.append(result)
    assert recognizer.model.transcribe.call_count == 1
    assert len(results) == 1


def test_whisper_hard_limit_includes_preroll_and_truncates_a_crossing_chunk(tmp_path):
    recognizer = decoder(tmp_path)
    recognizer.accept(bytes(32000), "turn", ["elephant"])
    recognizer.speech_present.return_value = True
    for _ in range(18):
        recognizer.accept(bytes(32000), "turn", ["elephant"])
    samples = recognizer.model.transcribe.call_args.args[0]
    assert len(samples) == 18 * 16000
    assert not recognizer.audio


def test_whisper_filters_hallucinations_instead_of_using_them_as_answers(tmp_path):
    recognizer = decoder(tmp_path)
    recognizer.model.transcribe.return_value = (iter([
        SimpleNamespace(text="unrelated", words=[], no_speech_prob=.99, avg_logprob=-.1, compression_ratio=1),
    ]), None)
    recognizer.speech_present.return_value = True
    recognizer.accept(bytes(16000), "turn", ["elephant"])
    recognizer.speech_present.return_value = False
    for _ in range(3):
        result = recognizer.accept(bytes(16000), "turn", ["elephant"])
    assert result == {"text": "", "confidence": 0}


def test_piper_generates_browser_wav_with_parent_speed_and_volume(tmp_path, monkeypatch):
    speech = SpeechOutput(tmp_path)
    speech.neural_available = Mock(return_value=True)
    def synthesize(text, output, syn_config):
        assert text == "Hello!"
        assert syn_config.volume == .4
        assert syn_config.length_scale == 145 / 180
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(22050)
        output.writeframes(bytes(100))
    voice = SimpleNamespace(synthesize_wav=synthesize)
    loader = Mock(return_value=voice)
    monkeypatch.setitem(sys.modules, "piper", SimpleNamespace(
        PiperVoice=SimpleNamespace(load=loader),
        SynthesisConfig=lambda **kwargs: SimpleNamespace(**kwargs),
    ))
    for _ in range(2):
        audio = speech.wave("Hello!", "en-gb", 180, 40)
        with wave.open(io.BytesIO(audio)) as decoded:
            assert decoded.getframerate() == 22050
            assert decoded.getnframes() == 50
    assert loader.call_count == 1
    assert loader.call_args.kwargs["use_cuda"] is False
