import pytest
import io
import zipfile

from app.voice.commands import memory_items
from app.voice.stt.offline import OfflineRecognizer
from tools.setup_voice import MODEL_NAME, install_model


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
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(f"{MODEL_NAME}/am/final.mdl", b"model")
        bundle.writestr(f"{MODEL_NAME}/conf/model.conf", b"config")
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: io.BytesIO(archive.getvalue()))
    install_model(tmp_path)
    assert (tmp_path / MODEL_NAME / "am" / "final.mdl").read_bytes() == b"model"
    def no_download(*args, **kwargs):
        raise AssertionError("A second model download must not be attempted.")
    monkeypatch.setattr("urllib.request.urlopen", no_download)
    install_model(tmp_path)


def test_model_setup_rejects_archive_path_traversal(tmp_path, monkeypatch):
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(f"{MODEL_NAME}/../../escape", b"unsafe")
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: io.BytesIO(archive.getvalue()))
    with pytest.raises(ValueError, match="Unsafe"):
        install_model(tmp_path / "models")
    assert not (tmp_path / "escape").exists()
