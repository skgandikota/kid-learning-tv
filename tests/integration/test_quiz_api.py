from unittest.mock import Mock

import pytest

from app.auth.security import hash_pin
from tests.conftest import csrf_for


@pytest.fixture
def parent(client, app):
    app.extensions["klt_db"].set_pin_hash(hash_pin("123456"))
    login = client.post("/api/login", json={"pin": "123456"}, headers={"X-CSRF-Token": csrf_for(client)})
    client.environ_base["HTTP_X_CSRF_TOKEN"] = login.json["csrf_token"]
    return client


def test_child_can_open_choose_and_close_but_not_interrupt_food(client):
    headers = {"X-CSRF-Token": csrf_for(client)}
    assert client.post("/api/child/quiz", json={"action": "menu"}).status_code == 400
    assert client.post("/api/child/quiz", json={"action": "menu"}, headers=headers).status_code == 200
    assert client.get("/api/display").json["playback"]["mode"] == "quiz-menu"
    assert client.post("/api/child/quiz", json={"action": "start", "category": "cars"}, headers=headers).status_code == 200
    quiz = client.get("/api/display").json["playback"]["quiz"]
    assert quiz["phase"] == "loading"
    assert quiz["count"] == 5
    assert client.post("/api/child/quiz", json={"action": "close"}, headers=headers).status_code == 200
    assert client.get("/api/display").json["playback"]["mode"] == "blank"


def test_parent_settings_persist_and_child_uses_them(parent, app):
    assert parent.post("/api/parent/quiz", json={
        "action": "settings", "settings": {"seconds": 5, "count": 10, "ticking": False},
    }).status_code == 200
    assert app.extensions["klt_db"].quiz_settings()["seconds"] == 5
    assert parent.post("/api/child/quiz", json={"action": "start", "category": "cars"}).status_code == 200
    quiz = parent.get("/api/display").json["playback"]["quiz"]
    assert quiz["seconds"] == 5 and quiz["ticking"] is False
    assert parent.post("/api/parent/food-time", json={"enabled": True}).status_code == 200
    assert parent.post("/api/child/quiz", json={"action": "menu"}).status_code == 423
    assert parent.get("/api/display").json["playback"]["quiz"] is None


def test_loopback_ready_and_stale_speech(parent):
    parent.post("/api/parent/quiz", json={"action": "start", "category": "animals"})
    quiz = parent.get("/api/display").json["playback"]["quiz"]
    report = {"action": "ready", "token": quiz["token"]}
    assert parent.post("/api/tv/quiz", json=report, environ_overrides={"REMOTE_ADDR": "192.168.1.2"}).status_code == 403
    assert parent.post("/api/tv/quiz", json=report).status_code == 200
    assert parent.get("/api/display").json["playback"]["quiz"]["phase"] == "question"
    parent.post("/api/parent/quiz", json={"action": "reveal"})
    assert parent.post("/api/tv/quiz", json={"action": "speech-done", "token": quiz["token"]}).status_code == 200
    parent.post("/api/parent/quiz", json={"action": "next"})
    assert parent.post("/api/tv/quiz", json=report).status_code == 409


def test_only_parent_can_set_timer_and_names_are_catalog_only(client, app):
    headers = {"X-CSRF-Token": csrf_for(client)}
    assert client.get("/api/parent/quiz").status_code == 401
    assert client.post("/api/parent/quiz", json={"action": "menu"}, headers=headers).status_code == 401
    speech = app.extensions["klt_quiz_speech"]
    speech.audio = Mock(return_value=b"RIFFtest")
    assert client.get("/api/quiz/audio/cars/not-an-answer").status_code == 404
    speech.audio.assert_not_called()


def test_speech_outside_playback_lock_and_failure_explicit(parent, app):
    from app.quiz_catalog import get_items
    item = get_items("cars")[0]
    speech = app.extensions["klt_quiz_speech"]
    speech.audio = Mock(return_value=b"RIFFtest")
    response = parent.get(f"/api/quiz/audio/cars/{item['id']}")
    assert response.mimetype == "audio/wav"
    speech.audio.assert_called_once_with(item.get("speech", item["name"]))
    speech.audio.side_effect = RuntimeError("No speech")
    assert parent.get(f"/api/quiz/audio/cars/{item['id']}").status_code == 503


def test_child_cannot_interrupt_video_or_finished_photo(parent, app):
    playback = app.extensions["klt_playback"]
    playback.start([{"id": "demo", "title": "Demo", "duration": 10}])
    assert parent.post("/api/child/quiz", json={"action": "start", "category": "cars"}).status_code == 423
    playback.advance()
    assert parent.post("/api/child/quiz", json={"action": "menu"}).status_code == 423
    assert playback.snapshot()["mode"] == "finished"
